(function () {
  function getParams() {
    const p = new URLSearchParams(window.location.search);
    const lat = parseFloat(p.get("lat"));
    const lon = parseFloat(p.get("lon"));
    const zoom = parseInt(p.get("zoom") || "13", 10);
    const name = p.get("name") || "";
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
    return { lat, lon, zoom, name };
  }

  function postZoomToIframes(payload) {
    // cible tous les iframes de cartes (tu peux affiner par classe)
    const frames = document.querySelectorAll("iframe");
    frames.forEach((f) => {
      try {
        f.contentWindow.postMessage({ type: "ZOOM_TO", payload }, "*");
      } catch (e) {}
    });
  }

  function tryApply() {
    const payload = getParams();
    if (!payload) return;

    // petit délai pour laisser la page rendre l'iframe
    setTimeout(() => postZoomToIframes(payload), 600);
    setTimeout(() => postZoomToIframes(payload), 1200);
  }

  window.addEventListener("load", tryApply);
})();
