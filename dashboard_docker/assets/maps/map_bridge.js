/**
 * assets/maps/map_bridge.js
 * 
 * Pont de communication entre le dashboard Dash et les cartes Leaflet (iframes).
 * 
 * FONCTIONNALITÉS:
 * - Zoom automatique via postMessage
 * - Parsing des URL params (?lat=X&lon=Y&zoom=Z)
 * - Marqueur highlight avec popup
 * - Animation de zoom fluide
 * - Support de plusieurs formats de message
 * - Historique de navigation
 */

(function() {
    'use strict';

    // =========================================================================
    // CONFIGURATION
    // =========================================================================
    const CONFIG = {
        defaultZoom: 13,
        animationDuration: 0.5, // secondes
        markerColor: '#005DFF',
        highlightColor: '#FF6B35',
        pulseAnimation: true,
    };

    // =========================================================================
    // UTILITAIRES
    // =========================================================================
    function safeNum(x) {
        const n = Number(x);
        return Number.isFinite(n) ? n : null;
    }

    function getLeafletMap() {
        // Essaie window.map d'abord
        if (typeof window.map !== 'undefined' && window.map && window.map.setView) {
            return window.map;
        }
        // Fallback: chercher toute variable qui ressemble à une map Leaflet
        for (const k in window) {
            try {
                if (window[k] && 
                    typeof window[k].setView === 'function' && 
                    typeof window[k].getCenter === 'function' &&
                    typeof window[k].getZoom === 'function') {
                    return window[k];
                }
            } catch(e) {}
        }
        return null;
    }

    // =========================================================================
    // GESTION DES MARQUEURS
    // =========================================================================
    let currentMarker = null;
    let currentPulse = null;

    function clearCurrentMarker(map) {
        if (currentMarker) {
            try {
                map.removeLayer(currentMarker);
            } catch(e) {}
            currentMarker = null;
        }
        if (currentPulse) {
            try {
                map.removeLayer(currentPulse);
            } catch(e) {}
            currentPulse = null;
        }
    }

    function createHighlightMarker(map, lat, lon, label) {
        if (typeof L === 'undefined') return;

        clearCurrentMarker(map);

        // Créer un marqueur avec icône personnalisée
        const customIcon = L.divIcon({
            className: 'solarx-highlight-marker',
            html: `
                <div style="
                    width: 32px;
                    height: 32px;
                    background: ${CONFIG.highlightColor};
                    border: 3px solid white;
                    border-radius: 50%;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    animation: solarx-pulse 1.5s ease-out infinite;
                ">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
                        <path d="M12 2L13.09 8.26L19 9L13.18 13.27L14.78 20L12 16.27L9.22 20L10.82 13.27L5 9L10.91 8.26L12 2Z"/>
                    </svg>
                </div>
            `,
            iconSize: [32, 32],
            iconAnchor: [16, 16],
            popupAnchor: [0, -20]
        });

        currentMarker = L.marker([lat, lon], { icon: customIcon });
        currentMarker.addTo(map);

        if (label) {
            currentMarker.bindPopup(`
                <div style="
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                    font-weight: 600;
                    color: #333;
                    padding: 4px;
                ">
                    📍 ${label}
                </div>
            `).openPopup();
        }

        // Ajouter un effet de pulse autour
        if (CONFIG.pulseAnimation && typeof L.circleMarker === 'function') {
            currentPulse = L.circleMarker([lat, lon], {
                radius: 25,
                fillColor: CONFIG.highlightColor,
                fillOpacity: 0.3,
                color: CONFIG.highlightColor,
                weight: 2,
                opacity: 0.6,
            });
            currentPulse.addTo(map);

            // Animation du pulse
            let radius = 25;
            const pulseInterval = setInterval(() => {
                radius += 2;
                if (radius > 50) radius = 25;
                if (currentPulse) {
                    currentPulse.setRadius(radius);
                    currentPulse.setStyle({ fillOpacity: 0.3 - (radius - 25) * 0.01 });
                }
            }, 50);

            // Arrêter l'animation après 5 secondes
            setTimeout(() => {
                clearInterval(pulseInterval);
                if (currentPulse) {
                    try { map.removeLayer(currentPulse); } catch(e) {}
                    currentPulse = null;
                }
            }, 5000);
        }
    }

    // =========================================================================
    // ZOOM VERS COORDONNÉES
    // =========================================================================
    function zoomToLocation(lat, lon, zoom, label, options = {}) {
        const map = getLeafletMap();
        if (!map) {
            console.warn('[SolarX MapBridge] No Leaflet map found');
            return false;
        }

        lat = safeNum(lat);
        lon = safeNum(lon);
        zoom = safeNum(zoom) || CONFIG.defaultZoom;

        if (lat === null || lon === null) {
            console.warn('[SolarX MapBridge] Invalid coordinates:', { lat, lon });
            return false;
        }

        console.log('[SolarX MapBridge] Zooming to:', { lat, lon, zoom, label });

        try {
            // Zoom avec animation
            map.setView([lat, lon], zoom, {
                animate: true,
                duration: CONFIG.animationDuration,
            });

            // Ajouter marqueur highlight
            if (options.showMarker !== false) {
                setTimeout(() => {
                    createHighlightMarker(map, lat, lon, label);
                }, 300);
            }

            // Déclencher événement custom
            window.dispatchEvent(new CustomEvent('solarx-map-zoomed', {
                detail: { lat, lon, zoom, label }
            }));

            return true;
        } catch(e) {
            console.error('[SolarX MapBridge] Zoom error:', e);
            return false;
        }
    }

    // =========================================================================
    // GESTION DES MESSAGES
    // =========================================================================
    function handleMessage(event) {
        const data = event.data;
        if (!data || typeof data !== 'object') return;

        // Format 1: type = 'ZOOM_TO'
        if (data.type === 'ZOOM_TO') {
            zoomToLocation(data.lat, data.lon, data.zoom, data.label || data.name, {
                idpoint: data.idpoint,
                showMarker: data.showMarker !== false,
            });
            return;
        }

        // Format 2: type = 'SET_MIN_SCORE' (pour carte optimisation)
        if (data.type === 'SET_MIN_SCORE' && typeof window.setMinScore === 'function') {
            window.setMinScore(data.value, false);
            return;
        }

        // Format 3: type = 'FOCUS_POINT' (pour carte optimisation)
        if (data.type === 'FOCUS_POINT' && typeof window.focusOnPoint === 'function') {
            window.focusOnPoint(data);
            return;
        }

        // Format 4: action = 'zoom' (compatibilité)
        if (data.action === 'zoom' && data.lat && data.lon) {
            zoomToLocation(data.lat, data.lon, data.zoom, data.label || data.name);
            return;
        }
    }

    // =========================================================================
    // PARSING DES URL PARAMS
    // =========================================================================
    function parseUrlParams() {
        const params = new URLSearchParams(window.location.search);
        const lat = params.get('lat');
        const lon = params.get('lon');
        const zoom = params.get('zoom');
        const name = params.get('name');

        if (lat && lon) {
            // Attendre que la carte soit chargée
            const checkMap = setInterval(() => {
                const map = getLeafletMap();
                if (map) {
                    clearInterval(checkMap);
                    setTimeout(() => {
                        zoomToLocation(lat, lon, zoom, name);
                    }, 500);
                }
            }, 100);

            // Timeout de sécurité
            setTimeout(() => clearInterval(checkMap), 10000);
        }
    }

    // =========================================================================
    // STYLES CSS POUR ANIMATIONS
    // =========================================================================
    function injectStyles() {
        if (document.getElementById('solarx-map-bridge-styles')) return;

        const style = document.createElement('style');
        style.id = 'solarx-map-bridge-styles';
        style.textContent = `
            @keyframes solarx-pulse {
                0% {
                    transform: scale(1);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                }
                50% {
                    transform: scale(1.1);
                    box-shadow: 0 6px 20px rgba(255,107,53,0.5);
                }
                100% {
                    transform: scale(1);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                }
            }
            
            .solarx-highlight-marker {
                background: transparent;
                border: none;
            }
            
            .leaflet-popup-content {
                margin: 8px 12px;
            }
        `;
        document.head.appendChild(style);
    }

    // =========================================================================
    // API GLOBALE
    // =========================================================================
    window.SolarXMapBridge = {
        zoomTo: zoomToLocation,
        clearMarker: function() {
            const map = getLeafletMap();
            if (map) clearCurrentMarker(map);
        },
        getMap: getLeafletMap,
        config: CONFIG,
    };

    // =========================================================================
    // INITIALISATION
    // =========================================================================
    function init() {
        injectStyles();
        window.addEventListener('message', handleMessage);
        
        // Parser les URL params au chargement
        if (document.readyState === 'complete') {
            parseUrlParams();
        } else {
            window.addEventListener('load', parseUrlParams);
        }

        console.log('[SolarX MapBridge] Initialized');
    }

    // Lancer l'initialisation
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();