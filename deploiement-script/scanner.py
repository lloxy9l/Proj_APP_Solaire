#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scan 10.7.181.* et 10.7.182.*, choix d'une machine,
puis exécution distante :
    cd Proj_APP_Solaire/docker && docker compose up -d
via SSH (mot de passe), avec bash -lc pour charger l'environnement (PATH).
"""
import ipaddress
import subprocess
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import getpass
import sys


# ====== Configuration ======
NETWORKS = ["10.7.181.0/24", "10.7.182.0/24", "10.7.180.0/24"]
MAX_PING_WORKERS = 200
MAX_DNS_WORKERS = 100


# ====== Fonctions utilitaires ======
def _ping_cmd(ip: str):
    """Retourne la commande ping correcte selon l’OS."""
    if sys.platform.startswith("linux"):
        return ["ping", "-c", "1", "-W", "1", ip]
    elif sys.platform == "darwin":
        return ["ping", "-c", "1", "-W", "1000", ip]
    else:
        return ["ping", "-c", "1", ip]


def ping(ip: str) -> bool:
    """Retourne True si l’hôte répond au ping."""
    try:
        cmd = _ping_cmd(ip)
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            return True
        if sys.platform == "darwin" and "-W" in cmd:
            cmd_fallback = ["ping", "-c", "1", ip]
            res = subprocess.run(cmd_fallback, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return res.returncode == 0
        return False
    except Exception:
        return False


def resolve_hostname(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return "Inconnu"


# ====== SSH / déploiement ======
def deploy_docker_compose(ip: str, username: str, password: str, timeout=10) -> bool:
    """
    Connexion SSH (Paramiko) avec mot de passe, puis exécution :
      cd Proj_APP_Solaire/docker && docker compose up -d
    Fallback docker-compose si échec.
    """
    try:
        import paramiko
    except ImportError:
        print("❌ Le module 'paramiko' est requis. Installe-le avec : pip install paramiko")
        return False

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"\n🔐 Connexion à {username}@{ip} ...")
    try:
        client.connect(ip, username=username, password=password, timeout=timeout)
    except paramiko.AuthenticationException:
        print("❌ Erreur d'authentification : mot de passe incorrect.")
        return False
    except Exception as e:
        print(f"❌ Impossible de se connecter à {ip} : {e}")
        return False

    def run(cmd: str):
        """Exécute une commande dans un shell login pour charger PATH."""
        wrapped = f'bash -lc "{cmd}"'
        stdin, stdout, stderr = client.exec_command(wrapped)
        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")
        rc = stdout.channel.recv_exit_status()
        return rc, out, err

    try:
        # Vérifie docker
        rc, docker_path, _ = run('command -v docker || which docker || echo ""')
        docker_path = docker_path.strip()
        if not docker_path:
            print("❌ 'docker' introuvable dans le PATH.")
            return False
        print(f"✅ Docker détecté : {docker_path}")

        # Commande principale
        cmd_v2 = 'cd Proj_APP_Solaire/docker && docker compose up -d'
        print(f"\n▶️  Exécution : {cmd_v2}")
        rc, out, err = run(cmd_v2)

        # Fallback docker-compose
        if rc != 0:
            cmd_v1 = 'git clone https://github.com/lloxy9l/Proj_APP_Solaire.git && cd Proj_APP_Solaire/docker && docker-compose up -d'
            rc, out2, err2 = run(cmd_v1)
            out += "\n" + out2
            err += "\n" + err2

        if out.strip():
            print("\n=== Sortie ===\n" + out)
        if err.strip():
            print("\n=== Erreurs ===\n" + err)

        if rc == 0:
            print(f"✅ Déploiement réussi sur {ip}")
            return True
        else:
            print(f"❌ Échec du déploiement (code {rc}).")
            return False
    finally:
        client.close()


# ====== Programme principal ======
def main():
    print("Scan des réseaux :", ", ".join(NETWORKS))

    # Liste complète des IP à scanner
    ips = [str(ip) for net in NETWORKS for ip in ipaddress.IPv4Network(net, strict=False).hosts()]
    if not ips:
        print("Aucune IP à scanner.")
        return

    # --- Étape 1 : Ping ---
    print("\n🔍 Ping en cours...")
    active = []
    with ThreadPoolExecutor(max_workers=MAX_PING_WORKERS) as ex:
        fut_to_ip = {ex.submit(ping, ip): ip for ip in ips}
        for fut in as_completed(fut_to_ip):
            ip = fut_to_ip[fut]
            try:
                if fut.result():
                    active.append(ip)
            except Exception:
                pass

    if not active:
        print("Aucun hôte actif détecté.")
        return

    # --- Étape 2 : Résolution des hostnames ---
    print(f"\n{len(active)} hôte(s) actif(s) — résolution des noms…")
    results = [[ip, "Inconnu"] for ip in active]
    with ThreadPoolExecutor(max_workers=MAX_DNS_WORKERS) as ex:
        fut_to_row = {ex.submit(resolve_hostname, r[0]): r for r in results}
        for fut in as_completed(fut_to_row):
            r = fut_to_row[fut]
            try:
                r[1] = fut.result()
            except Exception:
                r[1] = "Inconnu"

    results.sort(key=lambda r: tuple(int(p) for p in r[0].split(".")))

    # --- Étape 3 : Affichage des hôtes ---
    print("\n--- Hôtes actifs (10.7.181.* / 10.7.182.*) ---")
    for i, (ip, host) in enumerate(results, 1):
        print(f"{i:3d}. {ip:15}  {host}")

    # --- Étape 4 : Choix de la machine ---
    try:
        choice = int(input("\nNuméro de la machine pour déployer (0 pour annuler) : ").strip())
    except Exception:
        print("Entrée invalide.")
        return

    if choice <= 0 or choice > len(results):
        print("Annulé.")
        return

    target_ip, target_host = results[choice - 1]
    print(f"\n🎯 Cible : {target_ip} ({target_host})")

    # --- Étape 5 : Demander le nom d'utilisateur ---
    username = input("Nom d'utilisateur SSH : ").strip()
    if not username:
        print("Nom d'utilisateur vide, opération annulée.")
        return

    # --- Étape 6 : Mot de passe ---
    password = getpass.getpass(f"Mot de passe SSH pour {username}@{target_ip} : ")

    # --- Étape 7 : Déploiement ---
    deploy_docker_compose(target_ip, username, password)


if __name__ == "__main__":
    try:
        import paramiko  # vérifie que paramiko est installé
    except ImportError:
        print("Le module 'paramiko' est requis. Installe-le avec : pip install paramiko")
        sys.exit(1)

    main()
