import { state } from "./state.js";

import { formatArea, updateEmptyState, closeAllDeleteConfirms } from "./sidebar.js";

async function addSampleShapes() {
    const samples = [
        {
            name: "Sample1",
            coords:
            [
                [-37.876, 144.921],
                [-37.856, 144.927],
                [-37.885, 144.969],
                [-37.852, 145.019],
                [-37.790, 145.020],
                [-37.761, 144.958],
                [-37.767, 144.911],
                [-37.787, 144.875],
                [-37.816, 144.858],
                [-37.861, 144.853]
            ]
        },
        {
            name: "Sample2",
            coords:
            [
                [-38.003, 144.396],
                [-38.051, 144.313],
                [-38.148, 144.278],
                [-38.234, 144.286],
                [-38.258, 144.374],
                [-38.213, 144.414],
                [-38.146, 144.410],
                [-38.134, 144.374],
                [-38.091, 144.398]
            ]
        },
        {
            name: "Sample3",
            coords:
            [
                [-37.993, 145.052],
                [-38.026, 145.094],
                [-38.018, 145.124],
                [-37.991, 145.120],
                [-37.947, 145.154],
                [-37.915, 145.167],
                [-37.894, 145.143],
                [-37.882, 145.046],
                [-37.900, 145.005],
                [-37.917, 144.979],
                [-37.972, 145.002],
                [-38.003, 145.032]
            ]
        },
        {
            name: "Sample4",
            coords:
            [
                [-38.496, 145.401],
                [-38.554, 145.398],
                [-38.586, 145.366],
                [-38.532, 145.085],
                [-38.445, 145.142],
                [-38.433, 145.307]
            ]
        }
    ];

    for (const sample of samples) {
        const layer = L.polygon(sample.coords);

        layer._isSample = true;
        layer._sampleName = sample.name;

        await createShapeSequential(layer);
    }
}

function createShapeSequential(layer) {
    return new Promise(resolve => {
        layer.once("population:done", resolve);

        map.fire(L.Draw.Event.CREATED, {
            layer,
            layerType: "polygon"
        });
    });
}

const COLOR_PALETTE =
[
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab",

    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",

    "#6a3d9a", "#b15928", "#33a02c", "#fb9a99", "#e31a1c",
    "#1f78b4", "#a6cee3", "#b2df8a", "#cab2d6", "#ffff99",

    "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3",
    "#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd",

    "#ccebc5", "#ffed6f"
];

let nextColorIndex = 0;

function getNextColor()
{
    const c = COLOR_PALETTE[nextColorIndex % COLOR_PALETTE.length];
    nextColorIndex++;
    return c;
}

// Initialize map
const DEFAULT_MAP_VIEW = {center: [-38, 145.2631], zoom: 10};
const map = L.map('map', {minZoom: 3, maxZoom: 17}).setView(DEFAULT_MAP_VIEW.center, DEFAULT_MAP_VIEW.zoom);

// Layer options
const baseLayers = {
    vector_carto: L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
        {
            subdomains: 'abcd',
            maxZoom: 20,
            attribution: '&copy; OpenStreetMap &copy; CARTO'
        }
    ),

    vector_osm: L.tileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        {
            subdomains: 'abc',
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap'
        }
    ),

    satellite: L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        {
            maxZoom: 18,
            attribution: '&copy; Esri'
        }
    ),

    terrain: L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        {
            maxZoom: 18,
            attribution: '&copy; Esri'
        }
    ),

    dark: L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        {
            subdomains: 'abcd',
            maxZoom: 20,
            attribution: '&copy; OpenStreetMap &copy; CARTO'
        }
    )
};

let currentBaseLayer = baseLayers.vector_carto;
currentBaseLayer.addTo(map);

// Folium-like Draw controls
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

const drawControl = new L.Control.Draw
(
    {
        edit:
        {
            featureGroup: drawnItems,
            edit: true,
            remove: false
        },
        draw:
        {
            polygon: true,  
            rectangle: true,
            circle: false,
            polyline: false,
            marker: false,
            circlemarker: false
        }
    }
);
map.addControl(drawControl);

function unwrapLongitudes(coords)
{
    const out = [];
    let prevLon = coords[0][0];
    let offset = 0;

    for (let i = 0; i < coords.length; i++) {
        let lon = coords[i][0];

        let diff = lon - prevLon;

        if (diff > 180) offset -= 360;
        else if (diff < -180) offset += 360;

        const unwrappedLon = lon + offset;
        out.push([unwrappedLon, coords[i][1]]);

        prevLon = lon;
    }

    return out;
}

function recenterRing(ring)
{
    const lons = ring.map(p => p[0]);
    const avgLon = lons.reduce((a, b) => a + b, 0) / lons.length;

    const centerShift = Math.round(avgLon / 360) * 360;

    return ring.map(([lon, lat]) => [lon - centerShift, lat]);
}

function normalisePolygonGeometry(geometry) {
    if (geometry.type !== "Polygon") return geometry;

    const fixedRings = geometry.coordinates.map(ring => {
        const unwrapped = unwrapLongitudes(ring);
        return recenterRing(unwrapped);
    });

    return {
        ...geometry,
        coordinates: fixedRings
    };
}

// Map + AWS Lambda Functionality //
map.on(L.Draw.Event.CREATED, async function (event) {
    const layer = event.layer;
    const id = state.shapeCounter++;
    const color = getNextColor();

    layer.setStyle({
        color,
        weight: 4,
        fillOpacity: 0.2
    });


    drawnItems.addLayer(layer);

    const rawGeom = layer.toGeoJSON().geometry;
    const safeGeom = normalisePolygonGeometry(rawGeom);

    const area_m2 = turf.area({
        type: "Feature",
        geometry: safeGeom,
        properties: {}
    });

    const formattedArea = formatArea(area_m2);


    try {
        const response = await fetch(
            "https://njsg367vql.execute-api.ap-southeast-4.amazonaws.com/hello",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    polygon: safeGeom,
                    speed: state.settings.calcMode
                })
            }
        );

        const data = await response.json();
        console.log("Lambda response:", data);

        const population = data.result.result.population;
        const timems = data.result.duration.algorithm_time.total_ms;
        const valid = Number.isFinite(population);

        // --- Create sidebar dropdown ---
        const item = document.createElement("div");
        item.className = "shape-item open";

        item.innerHTML = `
            <div class="shape-header">
                <div class="shape-color" style="background:${color}"></div>
                <span class="shape-title">Shape ${id}</span>
                <span class="shape-arrow">▼</span>
            </div>

            <div class="shape-details">
                <button class="shape-delete" aria-label="Delete shape">🗑</button>

                <div class="delete-confirm">
                    <span>Confirm Deletion:</span>
                    <button class="confirm-yes">✓</button>
                </div>

            ${
                valid
                ? `
                    <p><b>Population:</b> ${Math.round(population).toLocaleString()}</p>

                    <p class="shape-area">
                        <b>Area:</b>
                        <span class="area-value">-</span>
                        <span class="area-unit"></span>
                    </p>

                    <p><b>Time:</b> ${timems} ms</p>
                `
                : `
                    <p style="color:#b00000; font-weight:500;">
                        Error: Shapes cannot have intersecting edges
                    </p>
                `
            }
            </div>
        `;
        item.style.setProperty("--shape-color", color);

        const deleteBtn = item.querySelector(".shape-delete");
        const confirmBox = item.querySelector(".delete-confirm");
        const confirmYes = item.querySelector(".confirm-yes");

        deleteBtn.addEventListener("click", (e) => {
            e.stopPropagation();

            closeAllDeleteConfirms();

            if (state.settings.confirmDelete) {
                confirmBox.classList.add("show");
            } else {
                // Immediate delete (no confirm)
                drawnItems.removeLayer(layer);
                item.remove();
                state.shapes.delete(id);
                updateEmptyState();
            }
        });

        confirmYes.addEventListener("click", (e) => {
            e.stopPropagation();

            drawnItems.removeLayer(layer);
            item.remove();
            state.shapes.delete(id);

            updateEmptyState();
        });

        document.getElementById("shapeList").appendChild(item);

        const areaValueEl = item.querySelector(".area-value");
        const areaUnitEl  = item.querySelector(".area-unit");

        if (areaValueEl && areaUnitEl) {
            const formatted = formatArea(area_m2);
            areaValueEl.textContent = formatted.value.toLocaleString(undefined, {
                maximumFractionDigits: 2
            });
            areaUnitEl.textContent = formatted.unit;
        }

        // Auto-scroll to bottom
        const panels = document.querySelector(".sidebar-panels");
        panels.scrollTo({
            top: panels.scrollHeight,
            behavior: "smooth"
        });

        state.shapes.set(id, {
            layer,
            item,
            area_m2
        });

        updateEmptyState();

        layer.fire("population:done");

        // --- Hover sync: shape → sidebar ---
        layer.on("mouseover", () => {
            layer.setStyle({fillOpacity: 0.4 });
            item.classList.add("highlight");
        });

        layer.on("mouseout", () => {
            layer.setStyle({fillOpacity: 0.2 });
            item.classList.remove("highlight");
        });

        // --- Hover sync: sidebar → shape ---
        item.addEventListener("mouseover", () => {
            layer.setStyle({ fillOpacity: 0.4 });
            item.classList.add("highlight");
        });

        item.addEventListener("mouseout", () => {
            layer.setStyle({ fillOpacity: 0.2 });
            item.classList.remove("highlight");
        });

        // --- Toggle dropdown ---
        item.addEventListener("click", () => {
            item.classList.toggle("open");
        });

        item.addEventListener("mouseleave", () => {
            confirmBox.classList.remove("show");
        });

        item.addEventListener("click", (e) => {
            closeAllDeleteConfirms();
        });

    } catch (err) {
        console.error("Population error:", err);
    }
});

// Recalculate upon shape edit

map.on(L.Draw.Event.EDITED, async (e) => {
    for (const layer of Object.values(e.layers._layers)) {

        let entry = null;
        for (const [, e] of state.shapes) {
            if (e.layer === layer) {
                entry = e;
                break;
            }
        }
        if (!entry) continue;

        const rawGeom = layer.toGeoJSON().geometry;
        const safeGeom = normalisePolygonGeometry(rawGeom);

        const area_m2 = turf.area({
            type: "Feature",
            geometry: safeGeom
        });
        entry.area_m2 = area_m2;

        const formatted = formatArea(area_m2);
        entry.item.querySelector(".area-value").textContent =
            formatted.value.toLocaleString(undefined, { maximumFractionDigits: 2 });
        entry.item.querySelector(".area-unit").textContent = formatted.unit;

        const response = await fetch(
            "https://njsg367vql.execute-api.ap-southeast-4.amazonaws.com/hello",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    polygon: safeGeom,
                    speed: state.settings.calcMode
                })
            }
        );

        const data = await response.json();
        const population = data?.result?.population;

        if (Number.isFinite(population)) {
            const popEl = entry.item.querySelector("p b")?.parentElement;
            if (popEl) {
                popEl.innerHTML =
                    `<b>Population:</b> ${Math.round(population).toLocaleString()}`;
            }
        }
    }
});

document.getElementById("addSampleShapesBtn")
    .addEventListener("click", () => {
        addSampleShapes();
    });

// ===== Map type switching =====
document.querySelectorAll('input[name="mapType"]').forEach(radio => {
    radio.addEventListener('change', () => {
        const selected = radio.value;

        if (!baseLayers[selected]) return;

        // Remove old base layer
        map.removeLayer(mapState.currentBaseLayer);

        // Add new base layer
        mapState.currentBaseLayer = baseLayers[selected];
        mapState.currentBaseLayer.addTo(map);
    });
});

export {
    map,
    DEFAULT_MAP_VIEW,
    baseLayers,
    drawnItems
};

export const mapState = {
    currentBaseLayer: baseLayers.vector_carto
};