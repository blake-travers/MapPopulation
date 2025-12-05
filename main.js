// DOM references
const sidebar = document.getElementById('sidebar');
const mapDiv = document.getElementById('map');
const toggleBtn = document.getElementById('sidebarButton');
let sidebarOpen = true;
toggleBtn.textContent = '▶';
const SIDEBAR_WIDTH = '30%';

const shapes = new Map();
let shapeCounter = 1;

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
    document.querySelectorAll(".delete-confirm.show")
        .forEach(el => el.classList.remove("show"));

}

// Initialize map
const map = L.map('map').setView([-37.8136, 144.9631], 11);

// Initialise layer/s
var CartoDB_VoyagerNoLabels = L.tileLayer
(
    'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png',
    {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }
);

var Esri_WorldGrayCanvas = L.tileLayer
(
    'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    {
        attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
        maxZoom: 16
    }
);


var CartoDB_PositronOnlyLabels = L.tileLayer
(
    'https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png',
    {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }
);

CartoDB_VoyagerNoLabels.addTo(map)
CartoDB_PositronOnlyLabels.addTo(map);


// Folium-like Draw controls
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

const drawControl = new L.Control.Draw
(
    {
        edit: false,
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

    try {
        const response = await fetch(
            "https://njsg367vql.execute-api.ap-southeast-4.amazonaws.com/hello",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    polygon: layer.toGeoJSON().geometry,
                    speed: document.querySelector(
                        'input[name="speedMode"]:checked'
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
                    <p><b>Mode:</b> ${data.speed}</p>
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

            confirmBox.classList.add("show");
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

        document.getElementById("shapeList").appendChild(item);

        // --- Store shape ---
        shapes.set(id, { layer, item });

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