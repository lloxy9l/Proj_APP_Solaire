#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUIv5 – Scanner & Déploiement multi-IP avec recherche, surlignage et musique au démarrage
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import queue
import contextlib
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress
import scanner  # ton script réseau
import pygame  # pour la musique

MAX_DEPLOY_RETRIES = 3


class StdoutRedirect(io.StringIO):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def write(self, s):
        def _insert():
            self.text_widget.insert(tk.END, s)
            self.text_widget.see(tk.END)
        self.text_widget.after(0, _insert)

    def flush(self):
        pass


class FastScannerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Scanner & Déploiement (multi-IP)")
        self.geometry("1040x660")
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._scan_thread = None
        self.checked = set()
        self.all_hosts = []  # liste de tous les hôtes pour la recherche
        self.available_containers = ["db", "python_app", "nodejs"]
        self.container_labels = {
            "db": "Base de données MySQL",
            "python_app": "Application Python",
            "nodejs": "Service Node.js",
        }
        self.container_compose_files = {
            "db": "docker-compose.db.yml",
            "python_app": "docker-compose.python.yml",
            "nodejs": "docker-compose.node.yml",
        }
        self.current_container_plan = {}

        self._build_ui()

    def _get_container_label(self, name):
        return self.container_labels.get(name, name.replace("_", " "))

    # ---------- Musique ----------
    def _play_music(self):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load("deploiement-script/startup.mp3")
            pygame.mixer.music.play(-1)  # boucle infinie
        except Exception as e:
            print(f"Erreur musique : {e}")

    def _stop_music(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    # ---------- UI ----------
    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        self.scan_btn = ttk.Button(top, text="Démarrer le scan (rapide)", command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT, padx=4)

        self.stop_scan_btn = ttk.Button(top, text="Arrêter le scan", command=self.stop_scan, state=tk.DISABLED)
        self.stop_scan_btn.pack(side=tk.LEFT, padx=4)

        ttk.Label(top, text="Réseaux :").pack(side=tk.LEFT, padx=(12, 4))
        self.networks_var = tk.StringVar(value=", ".join(scanner.NETWORKS))
        self.networks_entry = ttk.Entry(top, textvariable=self.networks_var, width=40)
        self.networks_entry.pack(side=tk.LEFT, padx=4)

        middle = ttk.Frame(self)
        middle.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        hosts_frame = ttk.Labelframe(middle, text="Hôtes actifs (triés)")
        hosts_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        # Barre de recherche
        ttk.Label(hosts_frame, text="Rechercher IP :").pack(anchor="w", padx=4, pady=(4,0))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(hosts_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, padx=4, pady=(0,4))
        self.search_var.trace_add("write", self._filter_tree)

        bulk_frame = ttk.Frame(hosts_frame)
        bulk_frame.pack(fill=tk.X, padx=4, pady=(0, 4))
        ttk.Button(bulk_frame, text="Tout sélectionner", command=self._select_all_hosts).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(bulk_frame, text="Tout décocher", command=self._clear_all_hosts).pack(side=tk.LEFT)

        # Treeview avec checkbox simulée
        self.tree = ttk.Treeview(hosts_frame, columns=("check", "ip", "host"), show="headings", selectmode="none")
        self.tree.heading("check", text="✔")
        self.tree.column("check", width=40, anchor="center")
        self.tree.heading("ip", text="Adresse IP")
        self.tree.heading("host", text="Nom d'hôte")
        self.tree.column("ip", width=150, anchor="center")
        self.tree.column("host", width=420, anchor="w")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(hosts_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Styles pour surlignage des lignes cochées
        style = ttk.Style()
        style.map("Treeview", background=[("selected", "#3399FF")])
        self.tree.tag_configure("checked", background="#CCE5FF")  # bleu clair

        right = ttk.Labelframe(middle, text="Déploiement")
        right.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(right, text="Machines sélectionnées :").grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(6, 2))
        self.selected_ip = tk.StringVar()
        ttk.Label(right, textvariable=self.selected_ip, width=35, wraplength=250, justify="left").grid(row=1, column=0, columnspan=2, padx=6, pady=(0, 8))

        ttk.Separator(right, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=(4, 6))
        ttk.Label(
            right,
            text="Le choix des containers sera proposé pour chaque machine pendant le déploiement.",
            wraplength=250,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=6, pady=(0, 8))

        ttk.Button(right, text="Déployer sur les machines sélectionnées", command=self.deploy).grid(
            row=4, column=0, columnspan=2, pady=10, padx=6, sticky="ew"
        )

        logs_frame = ttk.Labelframe(self, text="Logs")
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.log = tk.Text(logs_frame, wrap="none")
        self.log.pack(fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(logs_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Button-1>", self._toggle_check)
        self.stdout_redirect = StdoutRedirect(self.log)

    # ---------- Scan ----------
    def start_scan(self):
        if self._scan_thread and self._scan_thread.is_alive():
            messagebox.showinfo("Scan", "Déjà en cours.")
            return

        nets = [n.strip() for n in self.networks_var.get().split(",") if n.strip()]
        scanner.NETWORKS = nets

        try:
            ips = [str(ip) for net in nets for ip in ipaddress.IPv4Network(net, strict=False).hosts()]
        except Exception as e:
            messagebox.showerror("Erreur", f"Réseaux invalides : {e}")
            return

        self.tree.delete(*self.tree.get_children())
        self.checked.clear()
        self.all_hosts.clear()
        self._stop_event.clear()
        self.scan_btn.config(state=tk.DISABLED)
        self.stop_scan_btn.config(state=tk.NORMAL)
        self.log.insert(tk.END, f"Scan rapide sur {len(ips)} adresses...\n")
        self.log.see(tk.END)

        self._play_music()  # démarre la musique au scan

        self._scan_thread = threading.Thread(target=self._scan_worker, args=(ips,), daemon=True)
        self._scan_thread.start()
        self.after(100, self._poll_queue)

    def stop_scan(self):
        self._stop_event.set()
        self.log.insert(tk.END, "Arrêt demandé...\n")
        self._stop_music()  # stop la musique si scan stoppé

    def _scan_worker(self, ips):
        active = []
        maxw = getattr(scanner, "MAX_PING_WORKERS", 200)
        with ThreadPoolExecutor(max_workers=maxw) as ex:
            futures = {ex.submit(scanner.ping, ip): ip for ip in ips}
            for fut in as_completed(futures):
                if self._stop_event.is_set():
                    break
                ip = futures[fut]
                try:
                    if fut.result(timeout=1):
                        host = scanner.resolve_hostname(ip)
                        active.append((ip, host))
                        self._queue.put(("host", (ip, host)))
                except Exception:
                    pass
        self._queue.put(("done", active))

    def _poll_queue(self):
        try:
            while True:
                kind, val = self._queue.get_nowait()
                if kind == "host":
                    ip, host = val
                    self.all_hosts.append((ip, host))
                    self.tree.insert("", tk.END, values=("", ip, host))
                    self._sort_tree()
                elif kind == "done":
                    self.log.insert(tk.END, f"Scan terminé — {len(val)} hôte(s) trouvés.\n")
                    self.scan_btn.config(state=tk.NORMAL)
                    self.stop_scan_btn.config(state=tk.DISABLED)
                    self._stop_music()  # stop la musique à la fin
        except queue.Empty:
            pass
        if self._scan_thread and self._scan_thread.is_alive():
            self.after(100, self._poll_queue)

    def _sort_tree(self):
        items = [(self.tree.item(i)["values"], i) for i in self.tree.get_children()]
        items.sort(key=lambda x: tuple(map(int, x[0][1].split("."))))
        for idx, (_, iid) in enumerate(items):
            self.tree.move(iid, "", idx)

    # ---------- Checkbox ----------
    def _toggle_check(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            col = self.tree.identify_column(event.x)
            if col == "#1":  # colonne "check"
                item = self.tree.identify_row(event.y)
                if not item:
                    return
                if item in self.checked:
                    self.checked.remove(item)
                    self.tree.set(item, "check", "")
                    self.tree.item(item, tags=())
                else:
                    self.checked.add(item)
                    self.tree.set(item, "check", "✓")
                    self.tree.item(item, tags=("checked",))
        self._update_selected_ips()

    def _select_all_hosts(self):
        for item in self.tree.get_children():
            self.checked.add(item)
            self.tree.set(item, "check", "✓")
            self.tree.item(item, tags=("checked",))
        self._update_selected_ips()

    def _clear_all_hosts(self):
        for item in list(self.checked):
            if self.tree.exists(item):
                self.tree.set(item, "check", "")
                self.tree.item(item, tags=())
            self.checked.discard(item)
        self._update_selected_ips()

    def _update_selected_ips(self):
        ips = []
        for item in list(self.checked):
            if self.tree.exists(item):
                values = self.tree.item(item)["values"]
                if values:
                    ips.append(values[1])
            else:
                self.checked.discard(item)
        self.selected_ip.set(", ".join(ips))

    # ---------- Filtrage IP ----------
    def _filter_tree(self, *args):
        filter_text = self.search_var.get()
        preserved_ips = set()
        for item in list(self.checked):
            if self.tree.exists(item):
                values = self.tree.item(item)["values"]
                if values:
                    preserved_ips.add(values[1])
        self.checked.clear()
        self.tree.delete(*self.tree.get_children())
        for ip, host in self.all_hosts:
            if filter_text in ip:
                item = self.tree.insert("", tk.END, values=("", ip, host))
                if ip in preserved_ips:
                    self.checked.add(item)
                    self.tree.set(item, "check", "✓")
                    self.tree.item(item, tags=("checked",))
        self._sort_tree()
        self._update_selected_ips()

    # ---------- Sélection des conteneurs ----------
    def _prompt_container_selection(self, ip, default_selection):
        dialog = tk.Toplevel(self)
        dialog.title(f"Containers pour {ip}")
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_set()

        vars_for_ip = {}

        wrapper = ttk.Frame(dialog, padding=10)
        wrapper.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            wrapper,
            text="Décoche les containers que tu ne souhaites pas déployer.",
            wraplength=260,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        rows = ttk.Frame(wrapper)
        rows.pack(fill=tk.X, padx=4, pady=4)
        rows.columnconfigure(0, weight=1)

        for idx, name in enumerate(self.available_containers):
            var = tk.BooleanVar(value=name in default_selection)
            ttk.Checkbutton(rows, text=self._get_container_label(name), variable=var).grid(row=idx, column=0, sticky="w", pady=2)
            vars_for_ip[name] = var

        btn_frame = ttk.Frame(dialog, padding=(10, 0, 10, 10))
        btn_frame.pack(fill=tk.X)

        selection = {"value": None}

        def confirm():
            selected = [name for name, var in vars_for_ip.items() if var.get()]
            if not selected:
                messagebox.showwarning(
                    "Sélection requise",
                    "Sélectionne au moins un container.",
                    parent=dialog,
                )
                return
            selection["value"] = selected
            dialog.destroy()

        def cancel():
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", cancel)

        ttk.Button(btn_frame, text="Annuler", command=cancel).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Button(btn_frame, text="Valider", command=confirm).pack(side=tk.RIGHT)

        dialog.wait_window()
        return selection["value"]

    # ---------- Déploiement ----------
    def deploy(self):
        valid_items = [item for item in self.checked if self.tree.exists(item)]
        if not valid_items:
            self.checked.clear()
            self._update_selected_ips()
            messagebox.showwarning("Erreur", "Coche au moins une machine.")
            return
        self.checked = set(valid_items)
        selected_ips = []
        for item in valid_items:
            values = self.tree.item(item)["values"]
            if values:
                selected_ips.append(values[1])

        if not selected_ips:
            messagebox.showwarning("Erreur", "Impossible de récupérer les IP sélectionnées.")
            return

        per_machine_containers = {}
        default_selection = list(self.available_containers)
        for ip in selected_ips:
            choice = messagebox.askyesnocancel(
                "Déploiement des containers",
                f"Installer tous les containers sur {ip} ?\n\n"
                "Oui : déployer l'intégralité des services.\n"
                "Non : choisir les containers à déployer.\n"
                "Annuler : stopper le déploiement.",
                parent=self,
            )
            if choice is None:
                return
            if choice:
                per_machine_containers[ip] = list(self.available_containers)
            else:
                selection = self._prompt_container_selection(ip, default_selection)
                if selection is None:
                    return
                per_machine_containers[ip] = selection

        ip_credentials = {}
        for ip in selected_ips:
            user = simpledialog.askstring("Identifiant SSH", f"Utilisateur pour {ip} :")
            if not user:
                messagebox.showwarning("Annulé", f"Aucun utilisateur pour {ip}, déploiement annulé.")
                return
            pw = simpledialog.askstring("Mot de passe SSH", f"Mot de passe pour {ip} :", show="*")
            if not pw:
                messagebox.showwarning("Annulé", f"Aucun mot de passe pour {ip}, déploiement annulé.")
                return
            ip_credentials[ip] = (user, pw)

        # Interface seulement : on affiche le choix des conteneurs et compose utilisés dans les logs.
        deployment_plan = {}
        self.log.insert(tk.END, "\nDéploiement demandé avec le plan suivant :\n")
        for ip in selected_ips:
            containers = per_machine_containers.get(ip, self.available_containers)
            compose_files = [
                self.container_compose_files[name]
                for name in containers
                if name in self.container_compose_files
            ]
            if not compose_files:
                compose_files = ["docker-compose.yml"]
            deployment_plan[ip] = {"containers": containers, "compose_files": compose_files}
            labels = ", ".join(self._get_container_label(name) for name in containers)
            compose_hint = ", ".join(compose_files)
            self.log.insert(tk.END, f" - {ip} : {labels} (compose: {compose_hint})\n")
        self.log.see(tk.END)
        self.current_container_plan = deployment_plan

        threading.Thread(target=self._deploy_multi_individual, args=(ip_credentials,), daemon=True).start()

    def _deploy_multi_individual(self, ip_credentials):
        with contextlib.redirect_stdout(self.stdout_redirect), contextlib.redirect_stderr(self.stdout_redirect):
            print(f"\n=== Déploiement parallèle sur {len(ip_credentials)} machine(s) ===\n")
            with ThreadPoolExecutor(max_workers=min(len(ip_credentials), 10)) as ex:
                futures = {
                    ex.submit(self._deploy_one, ip, creds[0], creds[1]): ip
                    for ip, creds in ip_credentials.items()
                }
                for fut in as_completed(futures):
                    ip = futures[fut]
                    try:
                        fut.result()
                    except Exception as e:
                        print(f"[{ip}] ❌ Erreur : {e}\n")
            print("\n=== Déploiement terminé sur toutes les machines ===\n")

    def _deploy_one(self, ip, user, pw):
        for attempt in range(1, MAX_DEPLOY_RETRIES + 1):
            plan = self.current_container_plan.get(ip, {})
            selected_containers = plan.get("containers", list(self.available_containers))
            compose_files = plan.get("compose_files", ["docker-compose.yml"])
            files_display = ", ".join(compose_files)
            services_display = ", ".join(self._get_container_label(name) for name in selected_containers)
            print(
                f"[{ip}] Tentative {attempt}/{MAX_DEPLOY_RETRIES} : docker compose up -d "
                f"(services : {services_display or 'tous'}, fichiers : {files_display})"
            )
            try:
                success = scanner.deploy_docker_compose(ip, user, pw, compose_files)
                if success:
                    print(f"[{ip}] ✅ Déploiement réussi !\n")
                    return
            except Exception as e:
                print(f"[{ip}] Erreur tentative {attempt} : {e}\n")
            time.sleep(3)
        print(f"[{ip}] ❌ Échec après {MAX_DEPLOY_RETRIES} tentatives.\n")


if __name__ == "__main__":
    app = FastScannerGUI()
    app.mainloop()
