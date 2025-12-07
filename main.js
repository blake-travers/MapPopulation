// DOM references
const sidebar = document.getElementById('sidebar');
const mapDiv = document.getElementById('map');
const toggleBtn = document.getElementById('sidebarButton');
let sidebarOpen = true;
toggleBtn.textContent = '▶';
const SIDEBAR_WIDTH = '30%';

const deleteAllBtn = document.querySelector(".delete-all-btn");
const deleteAllConfirm = document.querySelector(".delete-all-confirm");
const deleteAllYes = deleteAllConfirm.querySelector(".confirm-yes");

const resetMapBtn = document.querySelector(".reset-map-btn");

const resetSettingsBtn = document.querySelector(".reset-settings-btn");

const shapes = new Map();
let shapeCounter = 1;
let currentAreaUnit = "km2";

// ===== Sidebar Tabs =====
const tabButtons = document.querySelectorAll(".sidebar-tabs .tab");
const tabPanels  = document.querySelectorAll(".tab-panel");

function setSidebarMode(mode) {
    sidebar.classList.remove("mode-shapes", "mode-settings");
    sidebar.classList.add(`mode-${mode}`);

    toggleBtn.classList.remove("mode-shapes", "mode-settings");
    toggleBtn.classList.add(`mode-${mode}`);
}

// initial panel colour = shapes
setSidebarMode("shapes");

tabButtons.forEach(tabBtn => {
    tabBtn.addEventListener("click", () => {
        const target = tabBtn.dataset.tab;

        tabButtons.forEach(t => t.classList.remove("active"));
        tabPanels.forEach(p => p.classList.remove("active"));

        tabBtn.classList.add("active");
        document.getElementById(`tab-${target}`).classList.add("active");

        setSidebarMode(target);
    });
});

const emptyState = document.getElementById("emptyState");
const shapeList = document.getElementById("shapeList");

function updateEmptyState() {
    if (shapes.size === 0) {
        emptyState.style.display = "block";
        shapeList.style.display = "none";
    } else {
        emptyState.style.display = "none";
        shapeList.style.display = "block";
    }
}

updateEmptyState();


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


function formatArea(area_m2) {
    switch (currentAreaUnit) {
        case "ha":
            return {
                value: area_m2 / 10_000,
                unit: "ha"
            };

        case "mi2":
            return {
                value: area_m2 / 2_589_988.110336,
                unit: "mi²"
            };

        case "km2":
        default:
            return {
                value: area_m2 / 1_000_000,
                unit: "km²"
            };
    }
}


function refreshAllAreas() {
    shapes.forEach(({ item, area_m2 }) => {
        const formatted = formatArea(area_m2);

        const valueEl = item.querySelector(".area-value");
        const unitEl  = item.querySelector(".area-unit");

        if (!valueEl || !unitEl) return;

        valueEl.textContent = formatted.value.toLocaleString(undefined, {
            maximumFractionDigits: 2
        });
        unitEl.textContent = formatted.unit;
    });
}

const DEFAULT_SETTINGS = {calcMode: "fast", mapType: "vector_carto", units: "km2", shapePanning: false, confirmDelete: false};

let confirmDeleteEnabled = DEFAULT_SETTINGS.confirmDelete;

// ===== Confirm Delete Setting =====
document.querySelectorAll('input[name="confirmDelete"]').forEach(radio => {
    radio.addEventListener("change", () => {
        confirmDeleteEnabled = radio.value === "true";
    });
});

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

function closeAllDeleteConfirms()
{
    document
        .querySelectorAll(".delete-confirm.show")
        .forEach(el => el.classList.remove("show"));

}


// Initialize map
const DEFAULT_MAP_VIEW = {center: [-38, 145.2631], zoom: 10};
const map = L.map('map', {minZoom: 3, maxZoom: 16}).setView(DEFAULT_MAP_VIEW.center, DEFAULT_MAP_VIEW.zoom);

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
    const id = shapeCounter++;
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
                    speed: document.querySelector(
                        'input[name="calcMode"]:checked'
                    ).value
                })
            }
        );

        const data = await response.json();

        const valid = Number.isFinite(data.population);

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
                    <p><b>Population:</b> ${Math.round(data.population).toLocaleString()}</p>

                    <p class="shape-area">
                        <b>Area:</b>
                        <span class="area-value">
                            ${formattedArea.value.toLocaleString(undefined, {
                                maximumFractionDigits: 2
                            })}
                        </span>
                        <span class="area-unit">${formattedArea.unit}</span>
                    </p>

                    <p><b>Time:</b> ${data.time} ms</p>
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

            if (confirmDeleteEnabled) {
                confirmBox.classList.add("show");
            } else {
                // Immediate delete (no confirm)
                drawnItems.removeLayer(layer);
                item.remove();
                shapes.delete(id);
                updateEmptyState();
            }
        });

        confirmYes.addEventListener("click", (e) => {
            e.stopPropagation();

            // remove polygon
            drawnItems.removeLayer(layer);

            // remove sidebar card
            item.remove();

            // clean state
            shapes.delete(id);
        });

        confirmYes.addEventListener("click", (e) => {
            e.stopPropagation();

            drawnItems.removeLayer(layer);
            item.remove();
            shapes.delete(id);

            updateEmptyState();
        });

        document.getElementById("shapeList").appendChild(item);

        // Auto-scroll to bottom
        const panels = document.querySelector(".sidebar-panels");
        panels.scrollTo({
            top: panels.scrollHeight,
            behavior: "smooth"
        });

        shapes.set(id, {
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
        for (const [, e] of shapes) {
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
                    speed: document.querySelector(
                        'input[name="calcMode"]:checked'
                    ).value
                })
            }
        );

        const data = await response.json();
        if (Number.isFinite(data.population)) {
            const popEl = entry.item.querySelector("p b")?.parentElement;
            if (popEl) {
                popEl.innerHTML =
                    `<b>Population:</b> ${Math.round(data.population).toLocaleString()}`;
            }
        }
    }
});






// Sidebar Functionality //

sidebar.style.transition = 'none';
toggleBtn.style.transition = 'none';

sidebar.style.width = SIDEBAR_WIDTH;
toggleBtn.style.right = SIDEBAR_WIDTH;

toggleBtn.addEventListener('click', () =>
{
    sidebar.style.transition = '';
    toggleBtn.style.transition = '';

    sidebarOpen = !sidebarOpen;

    if (sidebarOpen) // If Sidebar is to be opened
    {
        sidebar.style.width = SIDEBAR_WIDTH;
        sidebar.setAttribute('aria-hidden', 'false');
    }
    else // If Sidebar is to be closed:
    {
        sidebar.style.width = '0';
        sidebar.setAttribute('aria-hidden', 'true');

    }

    toggleBtn.style.right = sidebarOpen ? SIDEBAR_WIDTH : '0';
    toggleBtn.textContent = sidebarOpen ? '▶' : '◀';

});

// Search Functionality //

async function searchLocation(query)
{
    const url = `https://photon.komoot.io/api/?q=${encodeURIComponent(query)}`;

    try
    {
        const response = await fetch(url);
        const data = await response.json();
        const results = data.features;

        const searchResultsDiv = document.getElementById("searchResults");
        searchResultsDiv.innerHTML = "";

        if (!results || !results.length)
        {
            searchResultsDiv.style.display = "none";
            return;
        }

        // VALID TYPES: Cities + States + Countries
        const VALID_TYPES = new Set
        ([
            "city",
            "town",
            "village",
            "hamlet",
            "municipality",
            "locality",

            "state",
            "province",
            "region",
            "county",

            "country"
        ]);

        const filtered = results.filter(f =>
            VALID_TYPES.has(f.properties.osm_value)
        );

        filtered.slice(0, 7).forEach
        (feature =>
            {
                const props = feature.properties;
                const coords = feature.geometry.coordinates; // [lon, lat]

                // Choose best name
                const mainName =
                    props.name ||
                    props.city ||
                    props.state ||
                    props.country ||
                    "(unknown)";

                // Build clean label
                const label = [
                    mainName,
                    props.state,
                    props.country
                ].filter(Boolean).join(", ");

                const item = document.createElement("div");
                item.className = "search-result-item";
                item.textContent = label;

                item.addEventListener
                ("click", () =>
                    {
                        const lon = coords[0];
                        const lat = coords[1];

                        map.setView([lat, lon], 10);

                        L.marker([lat, lon])
                            .addTo(map)
                            .bindPopup(label)
                            .openPopup();

                        searchResultsDiv.style.display = "none";
                    }
                );

                searchResultsDiv.appendChild(item);
            }
        );
        searchResultsDiv.style.display = "block";
    }
    catch (err)
    {
        alert("Search error: " + err);
    }
}

document.getElementById("searchBox").addEventListener
(
    "keydown", (e) =>
    {
        if (e.key === "Enter")
        {
            const query = document.getElementById("searchBox").value.trim();
            if (query) searchLocation(query);
        }
    }
);


let debounceTimer = null;

function debounceSearch(query)
{
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout
    (() =>
        {
            if (query.length >= 1)
            {
                searchLocation(query);
            }
            else
            {
                document.getElementById("searchResults").style.display = "none";
            }
        }, 250
    );
}

document.getElementById("searchBox").addEventListener
("input", () =>
    {
        const query = document.getElementById("searchBox").value.trim();
        debounceSearch(query);
    }
);

document.addEventListener("click", (e) => {
    const box = document.getElementById("searchBox");
    const drop = document.getElementById("searchResults");

    if (!box.contains(e.target) && !drop.contains(e.target)) {
        drop.style.display = "none";
    }
});

// Escape Key functionality //

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeAllDeleteConfirms();
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
        map.removeLayer(currentBaseLayer);

        // Add new base layer
        currentBaseLayer = baseLayers[selected];
        currentBaseLayer.addTo(map);
    });
});

document.querySelectorAll('input[name="units"]').forEach(radio => {
    radio.addEventListener('change', () => {
        currentAreaUnit = radio.value;
        refreshAllAreas();
    });
});

resetMapBtn.addEventListener("click", () => {
    // Reset view
    map.setView(DEFAULT_MAP_VIEW.center, DEFAULT_MAP_VIEW.zoom);

    // Reset basemap
    map.removeLayer(currentBaseLayer);
    currentBaseLayer = baseLayers.vector_carto;
    currentBaseLayer.addTo(map);

    // Sync radio UI
    document.querySelector('input[name="mapType"][value="vector_carto"]').checked = true;
});

resetSettingsBtn.addEventListener("click", () => {
    // --- Calculation mode ---
    document.querySelector(
        `input[name="calcMode"][value="${DEFAULT_SETTINGS.calcMode}"]`
    ).checked = true;

    // --- Units ---
    currentAreaUnit = DEFAULT_SETTINGS.units;
    document.querySelector(
        `input[name="units"][value="${DEFAULT_SETTINGS.units}"]`
    ).checked = true;
    refreshAllAreas();

    // --- Map type ---
    map.removeLayer(currentBaseLayer);
    currentBaseLayer = baseLayers[DEFAULT_SETTINGS.mapType];
    currentBaseLayer.addTo(map);
    document.querySelector(
        `input[name="mapType"][value="${DEFAULT_SETTINGS.mapType}"]`
    ).checked = true;
    document.querySelector(
        `input[name="unlockShapes"][value="${DEFAULT_SETTINGS.shapePanning}"]`
        ).checked = true;
    document.querySelector(
        `input[name="confirmDelete"][value="${DEFAULT_SETTINGS.confirmDelete}"]`
    ).checked = true;

    confirmDeleteEnabled = DEFAULT_SETTINGS.confirmDelete;
});

deleteAllBtn.addEventListener("click", (e) => {
    e.stopPropagation();

    if (shapes.size === 0) return;

    closeAllDeleteConfirms();
    deleteAllConfirm.classList.add("show");
});

deleteAllYes.addEventListener("click", (e) => {
    e.stopPropagation();

    shapes.forEach(({ layer }) => {
        drawnItems.removeLayer(layer);
    });

    shapes.clear();
    document.getElementById("shapeList").innerHTML = "";
    shapeCounter = 1;

    updateEmptyState();
    deleteAllConfirm.classList.remove("show");
});


deleteAllConfirm.addEventListener("click", (e) => {
    e.stopPropagation();
});

const settingsActions = document.querySelector(".settings-actions");

settingsActions.addEventListener("mouseleave", () => {
    deleteAllConfirm.classList.remove("show");
});




// TODO Frontend: Magnifying glass for every shape - auto pan
