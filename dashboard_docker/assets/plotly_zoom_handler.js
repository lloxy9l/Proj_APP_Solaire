/*
  SolarX Plotly Zoom Handler (persistent + highlight)

  Goal:
    - When URL params indicate a target location (lat/lon/zoom), the map should zoom
      AND stay zoomed even if Dash re-renders the figure.
    - Optional: add a persistent highlight marker on the map.

  Supported Plotly map types:
    - geo-based maps: layout.geo.center / projection.scale
    - mapbox maps:   layout.mapbox.center / layout.mapbox.zoom (and mapbox2, mapbox3...)

  URL format:
    ?lat=46.2044&lon=6.1432&zoom=12&name=Geneve
    Optional highlight marker:
    &hl=marker&hl_lat=46.2044&hl_lon=6.1432&hl_text=Geneve

  Storage:
    sessionStorage.solarx_target_view

  Notes:
    - We don't rely on a fixed Graph id. We detect visible Plotly graphs.
    - We attach a MutationObserver to re-apply the view after re-render.
*/

(function () {
  const STORAGE_KEY = "solarx_target_view";
  const APPLY_LOCK_KEY = "solarx_target_view_lock";
  const HIGHLIGHT_TRACE_NAME = "__solarx_highlight__";

  // How aggressively to retry finding a Plotly graph after navigation/rerender
  const FIND_RETRY_MAX = 40; // ~40 * 250ms = 10s
  const FIND_RETRY_DELAY_MS = 250;

  function log(...args) {
    // eslint-disable-next-line no-console
    console.log("PlotlyZoom:", ...args);
  }

  function warn(...args) {
    // eslint-disable-next-line no-console
    console.warn("PlotlyZoom:", ...args);
  }

  function safeParseFloat(v) {
    const n = parseFloat(v);
    return Number.isFinite(n) ? n : null;
  }

  function parseUrlParams() {
    const params = new URLSearchParams(window.location.search || "");
    const lat = safeParseFloat(params.get("lat"));
    const lon = safeParseFloat(params.get("lon"));
    const zoom = safeParseFloat(params.get("zoom"));
    const name = params.get("name") || "";

    // Optional highlight
    const hl = (params.get("hl") || "").toLowerCase(); // "marker"
    const hlLat = safeParseFloat(params.get("hl_lat"));
    const hlLon = safeParseFloat(params.get("hl_lon"));
    const hlText = params.get("hl_text") || "";

    if (lat === null || lon === null) return null;

    return {
      lat,
      lon,
      zoom: zoom === null ? 12 : zoom,
      name,
      hl,       // "" or "marker"
      hlLat,    // nullable
      hlLon,    // nullable
      hlText,
      source: "url",
      ts: Date.now(),
    };
  }

  function getStoredTargetView() {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  function setStoredTargetView(view) {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(view));
    } catch {
      /* ignore */
    }
  }

  function isElementVisible(el) {
    if (!el) return false;
    // offsetParent is null for display:none or detached
    if (el.offsetParent === null && el.getClientRects().length === 0) return false;
    const rect = el.getBoundingClientRect();
    return rect.width > 10 && rect.height > 10;
  }

  function listPlotlyGraphDivs() {
    // Plotly renders a div with class "js-plotly-plot" inside dcc.Graph container
    return Array.from(document.querySelectorAll(".js-plotly-plot"))
      .map((el) => el)
      .filter(isElementVisible);
  }

  function pickBestGraph(graphDivs) {
    // Prefer a mapbox graph, otherwise geo map, otherwise first visible plotly.
    for (const gd of graphDivs) {
      const layout = gd && gd.layout;
      if (layout && hasAnyMapbox(layout)) return gd;
    }
    for (const gd of graphDivs) {
      const layout = gd && gd.layout;
      if (layout && layout.geo) return gd;
    }
    return graphDivs.length ? graphDivs[0] : null;
  }

  function hasAnyMapbox(layout) {
    if (!layout) return false;
    return Object.keys(layout).some((k) => k === "mapbox" || k.startsWith("mapbox"));
  }

  function buildRelayoutPayload(gd, view) {
    const layout = gd.layout || {};
    const payload = {};

    // Mapbox: update all mapbox subplots (mapbox, mapbox2, ...)
    const mapboxKeys = Object.keys(layout).filter((k) => k === "mapbox" || k.startsWith("mapbox"));
    if (mapboxKeys.length) {
      for (const k of mapboxKeys) {
        payload[`${k}.center`] = { lat: view.lat, lon: view.lon };
        payload[`${k}.zoom`] = view.zoom;
      }
      return payload;
    }

    // Geo: center + projection scale (roughly correlates with zoom)
    if (layout.geo) {
      payload["geo.center"] = { lat: view.lat, lon: view.lon };
      // Projection scale: keep within a sane range.
      const scale = Math.max(1, Math.min(100, view.zoom * 1.25));
      payload["geo.projection.scale"] = scale;
      return payload;
    }

    return null;
  }

  function buildHighlightTrace(view) {
    if (!view) return null;
    if (view.hl !== "marker") return null;
    if (view.hlLat === null || view.hlLon === null) return null;

    // Works for mapbox figures (scattermapbox). If your map is geo-based, we skip highlight.
    return {
      type: "scattermapbox",
      lat: [view.hlLat],
      lon: [view.hlLon],
      mode: view.hlText ? "markers+text" : "markers",
      text: view.hlText ? [view.hlText] : undefined,
      textposition: "top center",
      marker: { size: 18, color: "red" },
      name: HIGHLIGHT_TRACE_NAME,
      hoverinfo: view.hlText ? "text" : "skip",
      showlegend: false,
    };
  }

  function applyHighlightMarker(gd, view) {
    if (!gd || !window.Plotly) return;
    const layout = gd.layout || {};
    if (!hasAnyMapbox(layout)) return; // highlight marker supports mapbox figures only

    const trace = buildHighlightTrace(view);
    if (!trace) return;

    const data = gd.data || [];
    const idx = data.findIndex((t) => t && t.name === HIGHLIGHT_TRACE_NAME);

    // If already exists -> replace it, else add it
    if (idx !== -1) {
      try {
        // Full replacement of trace
        window.Plotly.deleteTraces(gd, [idx]).then(() => {
          window.Plotly.addTraces(gd, [trace]);
        });
      } catch {
        // fallback
        try {
          window.Plotly.addTraces(gd, [trace]);
        } catch {
          /* ignore */
        }
      }
    } else {
      try {
        window.Plotly.addTraces(gd, [trace]);
      } catch {
        /* ignore */
      }
    }
  }

  function applyViewToGraph(gd, view, reason) {
    if (!gd || !window.Plotly) return false;
    const payload = buildRelayoutPayload(gd, view);
    if (!payload) return false;

    // Avoid infinite relayout loops: a small lock window
    const now = Date.now();
    const lockUntil = safeParseFloat(sessionStorage.getItem(APPLY_LOCK_KEY) || "") || 0;
    if (lockUntil > now) return true;
    sessionStorage.setItem(APPLY_LOCK_KEY, String(now + 400));

    try {
      log(`Applying target view (${reason})`, view);

      // Apply zoom/center, then highlight (after relayout completes)
      const relayoutPromise = window.Plotly.relayout(gd, payload);
      if (relayoutPromise && typeof relayoutPromise.then === "function") {
        relayoutPromise.then(() => {
          applyHighlightMarker(gd, view);
        });
      } else {
        // fallback for older behavior
        setTimeout(() => applyHighlightMarker(gd, view), 60);
      }
      return true;
    } catch (e) {
      warn("Relayout failed", e);
      return false;
    }
  }

  function attachPersistenceHandlers(gd) {
    if (!gd || gd.__solarxZoomHandlersAttached) return;
    gd.__solarxZoomHandlersAttached = true;

    // If the user manually pans/zooms, store that as the last view too.
    gd.on("plotly_relayout", () => {
      try {
        const layout = gd.layout || {};
        const stored = getStoredTargetView();

        if (hasAnyMapbox(layout)) {
          const mainKey = Object.keys(layout).find((k) => k === "mapbox" || k.startsWith("mapbox"));
          const mb = mainKey ? layout[mainKey] : null;
          if (mb && mb.center && typeof mb.zoom === "number") {
            const view = {
              lat: mb.center.lat,
              lon: mb.center.lon,
              zoom: mb.zoom,
              name: stored?.name || "",
              // Keep highlight from stored (so it persists)
              hl: stored?.hl || "",
              hlLat: stored?.hlLat ?? null,
              hlLon: stored?.hlLon ?? null,
              hlText: stored?.hlText || "",
              source: "user",
              ts: Date.now(),
            };
            setStoredTargetView(view);
          }
        } else if (layout.geo && layout.geo.center) {
          const view = {
            lat: layout.geo.center.lat,
            lon: layout.geo.center.lon,
            zoom: safeParseFloat(layout.geo.projection?.scale) || (stored?.zoom ?? 12),
            name: stored?.name || "",
            // Geo maps: keep highlight values stored (even if not used)
            hl: stored?.hl || "",
            hlLat: stored?.hlLat ?? null,
            hlLon: stored?.hlLon ?? null,
            hlText: stored?.hlText || "",
            source: "user",
            ts: Date.now(),
          };
          setStoredTargetView(view);
        }
      } catch {
        /* ignore */
      }
    });

    // Re-apply after Plotly redraws (Dash figure update)
    gd.on("plotly_afterplot", () => {
      const view = getStoredTargetView();
      if (view) applyViewToGraph(gd, view, "afterplot");
    });
  }

  function applyTargetViewOnce() {
    const urlView = parseUrlParams();
    if (urlView) {
      setStoredTargetView(urlView);
      log("URL params detected", urlView);
    }

    const target = urlView || getStoredTargetView();
    if (!target) return;

    const graphs = listPlotlyGraphDivs();
    const gd = pickBestGraph(graphs);
    if (!gd) return;

    attachPersistenceHandlers(gd);
    applyViewToGraph(gd, target, urlView ? "url" : "storage");
  }

  function retryFindAndApply() {
    let attempts = 0;
    const timer = setInterval(() => {
      attempts += 1;
      applyTargetViewOnce();
      const hasGraph = !!pickBestGraph(listPlotlyGraphDivs());
      if (hasGraph || attempts >= FIND_RETRY_MAX) {
        if (!hasGraph) warn("Max attempts reached, Plotly graph not found");
        clearInterval(timer);
      }
    }, FIND_RETRY_DELAY_MS);
  }

  function installObservers() {
    // URL changes (pushState/replaceState) aren't always detected by popstate
    const _pushState = history.pushState;
    history.pushState = function () {
      const ret = _pushState.apply(this, arguments);
      window.dispatchEvent(new Event("solarx:urlchange"));
      return ret;
    };
    const _replaceState = history.replaceState;
    history.replaceState = function () {
      const ret = _replaceState.apply(this, arguments);
      window.dispatchEvent(new Event("solarx:urlchange"));
      return ret;
    };

    window.addEventListener("popstate", () => retryFindAndApply());
    window.addEventListener("solarx:urlchange", () => retryFindAndApply());

    // Observe DOM changes that might add/remove graphs
    const obs = new MutationObserver(() => {
      // Debounce by scheduling a microtask-ish delay
      if (window.__solarxZoomMutationScheduled) return;
      window.__solarxZoomMutationScheduled = true;
      setTimeout(() => {
        window.__solarxZoomMutationScheduled = false;
        applyTargetViewOnce();
      }, 120);
    });
    obs.observe(document.documentElement, { childList: true, subtree: true });
  }

  function init() {
    try {
      log("Handler loaded");
      installObservers();
      retryFindAndApply();
    } catch (e) {
      warn("Init failed", e);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
