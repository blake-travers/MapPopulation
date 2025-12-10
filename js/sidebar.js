import { state, DEFAULT_SETTINGS } from "./state.js";

import {
    map,
    DEFAULT_MAP_VIEW,
    baseLayers,
    drawnItems,
    mapState
} from "./map.js";



// DOM references
const sidebar = document.getElementById('sidebar');
const mapDiv = document.getElementById('map');
const toggleBtn = document.getElementById('sidebarButton');
toggleBtn.textContent = '▶';
const SIDEBAR_WIDTH = '30%';

const deleteAllBtn = document.querySelector(".delete-all-btn");
const deleteAllConfirm = document.querySelector(".delete-all-confirm");
const deleteAllYes = deleteAllConfirm.querySelector(".confirm-yes");

const resetMapBtn = document.querySelector(".reset-map-btn");

const resetSettingsBtn = document.querySelector(".reset-settings-btn");

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

export function updateEmptyState() {
    if (state.shapes.size === 0) {
        emptyState.style.display = "block";
        shapeList.style.display = "none";
    } else {
        emptyState.style.display = "none";
        shapeList.style.display = "block";
    }
}

updateEmptyState();

export function formatArea(area_m2) {
    switch (state.settings.areaUnit) {
        case "ha": {
            const area = area_m2 / 10_000;
            return {value: area, unit: "ha"};
        } 

        case "mi2": {
            const area = area_m2 / 2_589_988.110336;
            return {value: area, unit: "mi²"};
        }

        case "km2": {
            const area = area_m2 / 1_000_000;
            return {value: area, unit: "km²"};
        }
            
    }
}

export function formatDensity(pop, area_m2) {
    switch (state.settings.areaUnit) {
        case "ha": {
            const area = area_m2 / 10_000;
            return { value: pop / area, unit: "people/ha" };
        }

        case "mi2": {
            const area = area_m2 / 2_589_988.110336;
            return { value: pop / area, unit: "people/mi²" };
        }

        case "km2":
        default: {
            const area = area_m2 / 1_000_000;
            return { value: pop / area, unit: "people/km²" };
        }
    }
}

function refreshShapeAreaDensity(item, area_m2, pop) {
    const { value: areaValue, unit: areaUnit } = formatArea(area_m2);;
    const { value: densityValue, unit: densityUnit } = formatDensity(pop, area_m2);;

    const areaEl = item.querySelector(".area-value");
    const areaUnitEl  = item.querySelector(".area-unit");
    const densityEl = item.querySelector(".density-value");
    const densityUnitEl = item.querySelector(".density-unit");
    
    if (!areaEl || !areaUnitEl || !densityEl || !densityUnitEl) return;

    areaEl.textContent = areaValue.toLocaleString(undefined, {
        maximumFractionDigits: 2
    });
    densityEl.textContent = densityValue.toLocaleString(undefined, {
        maximumFractionDigits: 2
    });

    areaUnitEl.textContent = areaUnit
    densityUnitEl.textContent = densityUnit;  
}


function refreshAllAreasDensities() {
    state.shapes.forEach(({ item, area_m2, result}) => {
        refreshShapeAreaDensity(item, area_m2, result.result.result.population);
    });
}

// ===== Confirm Delete Setting =====
document.getElementById("confirmDeleteToggle").addEventListener("change", (e) => {
    state.settings.confirmDelete = e.target.checked;
});

export function closeAllDeleteConfirms()
{
    document
        .querySelectorAll(".delete-confirm.show")
        .forEach(el => el.classList.remove("show"));

}

// Sidebar Functionality //\

// Start closed

sidebar.style.transition = 'none';
toggleBtn.style.transition = 'none';

sidebar.style.width = '0';
sidebar.setAttribute('aria-hidden', 'true');

toggleBtn.style.right = '0';
toggleBtn.textContent = '◀';

let sidebarOpen = false;

//Next frame, open sidebar without transitions
requestAnimationFrame(() => {
    sidebar.style.width = SIDEBAR_WIDTH;
    sidebar.setAttribute('aria-hidden', 'false');

    toggleBtn.style.right = SIDEBAR_WIDTH;
    toggleBtn.textContent = '▶';

    sidebarOpen = true;
    requestAnimationFrame(() => { //third frame, we re-enable transitions
        sidebar.style.transition = '';
        toggleBtn.style.transition = '';
    });
});

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

// Escape Key functionality //

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeAllDeleteConfirms();
    }
});

document.querySelectorAll('input[name="units"]').forEach(radio => {
    radio.addEventListener('change', () => {
        state.settings.areaUnit = radio.value;
        refreshAllAreasDensities();
    });
});

document.querySelectorAll('input[name="calcMode"]').forEach(radio => {
    radio.addEventListener("change", () => {
        state.settings.calcMode = radio.value;
        console.log("Calc mode changed:", state.settings.calcMode);
    });
});

resetMapBtn.addEventListener("click", () => {
    // Reset view
    map.setView(DEFAULT_MAP_VIEW.center, DEFAULT_MAP_VIEW.zoom);
});

resetSettingsBtn.addEventListener("click", () => {

    // ---- Reset STATE ----
    Object.assign(state.settings, DEFAULT_SETTINGS);

    // ---- Sync UI from state ----
    document.querySelector(
        `input[name="calcMode"][value="${state.settings.calcMode}"]`
    ).checked = true;

    document.querySelector(
        `input[name="units"][value="${state.settings.areaUnit}"]`
    ).checked = true;

    document.getElementById("confirmDeleteToggle").checked = state.settings.confirmDelete;

    document.getElementById("debugModeToggle").checked = state.settings.debugMode;

    if (mapState.currentBaseLayer !== baseLayers[state.settings.mapType]) {
        document.querySelector(
            `input[name="mapType"][value="${state.settings.mapType}"]`
        ).checked = true;

        // Remove old layer + add correct one
        map.removeLayer(mapState.currentBaseLayer);
        mapState.currentBaseLayer = baseLayers[state.settings.mapType];
        mapState.currentBaseLayer.addTo(map);
    }

    // ---- Apply effects ----
    refreshAllShapeCards();
});


if (deleteAllBtn) {
    deleteAllBtn.addEventListener("click", (e) => {
        e.stopPropagation();

        if (state.shapes.size === 0) return;

        closeAllDeleteConfirms();
        deleteAllConfirm.classList.add("show");
    });
}

if (deleteAllYes) {
    deleteAllYes.addEventListener("click", (e) => {
        e.stopPropagation();

        state.shapes.forEach(({ layer }) => {
            drawnItems.removeLayer(layer); //This is Not good practise - should change eventually
        });

        state.shapes.clear();
        document.getElementById("shapeList").innerHTML = "";
        state.shapeCounter = 1;

        updateEmptyState();
        deleteAllConfirm.classList.remove("show");
    });
}

export function renderShapeUI(item, data, area_m2) {

    const valid = Number.isFinite(data.result.result.population);
    const details = item.querySelector(".shape-details");
    const round5 = (x, d = 5) => Number(x.toFixed(d));
    const roundint = (x) => Math.round(x).toLocaleString();

    const pop = data.result.result.population;
    const D = data.result.duration;
    const G = data.result.geometry;
    const R = data.result.resolution;
    const Q = data.result.quadtree;
    const U = data.result.uncertainty;



    if (!valid) {
        details.innerHTML = `
            <button class="shape-delete" aria-label="Delete shape">🗑</button>

            <div class="delete-confirm">
                <span>Confirm Deletion:</span>
                <button class="confirm-yes">✓</button>
            </div>

            <p style="color:#b00000;">Invalid shape — cannot process polygon</p>
        `;
        return;
    }


    if (!state.settings.debugMode) {
        details.innerHTML = `
            <button class="shape-delete" aria-label="Delete shape">🗑</button>

            <div class="delete-confirm">
                <span>Confirm Deletion:</span>
                <button class="confirm-yes">✓</button>
            </div>

            <button class="shape-pan" aria-label="Pan to shape">🔍︎</button>

            <div class="simple-grid">
                <b>Population:</b> ${roundint(pop)}

                <b>Area:</b>
                <span>
                    <span class="area-value">-</span>
                    <span class="area-unit"></span>
                </span>

                <b>Density:</b>
                <span>
                    <span class="density-value">-</span>
                    <span class="density-unit"></span>
                </span>

            </div>

        `;

        item.classList.remove("debug-expanded");
    }

    else {
        details.innerHTML = `
            <button class="shape-delete" aria-label="Delete shape">🗑</button>

            <div class="delete-confirm">
                <span>Confirm Deletion:</span>
                <button class="confirm-yes">✓</button>
            </div>

            <button class="shape-pan" aria-label="Pan to shape">🔍︎</button>

            <div class="debug-grid">

                <b>Population:</b> ${roundint(pop)}

                <b>Area:</b>
                <span>
                    <span class="area-value">-</span>
                    <span class="area-unit"></span>
                </span>

                <b>Density:</b>
                <span>
                    <span class="density-value">-</span>
                    <span class="density-unit"></span>
                </span>

                <b>Shape Bounding box:</b>
                [${G.bounding_box.xmin}°, ${G.bounding_box.ymin}°] →  [${G.bounding_box.xmax}°, ${G.bounding_box.ymax}°]
                
                <b>Shape Angular Span:</b> ${G.angular_span_deg}°
                <b>Shape Perimeter:</b> ${G.perimeter_deg}°

                <b>Algorithmic Uncertainty:</b> ±${U.algorithmic_uncertainty_pct}% (95% Confidence)
                <b>Estimated Dataset Uncertainty:</b> ±${U.estimated_dataset_uncertainty_pct}%

                <b>Total Calculation Time:</b> ${D.algorithm_time.total_ms} ms

                <b>Calculation Preset:</b> ${R.speed}
                <b>Effective Resolution:</b>
                ${R.highest_resolution_degrees}° /
                ${R.highest_resolution_minutes}' /
                ${R.highest_resolution_seconds}"
                <b>Number of Visited Nodes:</b> ${Q.nodes_visited}


            </div>
        `;
        item.classList.add("debug-expanded")
    }

    refreshShapeAreaDensity(item, area_m2, pop);
}
// <b>Tile Size:</b> ${R.scheme_tile_size_deg}°
// <b>Complexity Factor: </b> ${G.complexity}
// <b>Maximum Chosen Depth:</b> ${R.custom_max_depth}
// <b>Full Nodes:</b> ${Q.full_nodes}
// <b>Empty Nodes:</b> ${Q.empty_nodes}
// <b>Partial Nodes:</b> ${Q.partial_nodes}
// <b>Recursed Nodes:</b> ${Q.recursed_nodes}
// <b>Server startup time:</b> ${D.lambda_time_ms} ms
// <b>Dataset Open time:</b> ${D.algorithm_time.open_ms} ms
// <b>Shape Process time:</b> ${D.algorithm_time.process_ms} ms



document.getElementById("debugModeToggle").addEventListener("change", (e) => {
    state.settings.debugMode = e.target.checked;
    refreshAllShapeCards();
});

export function refreshAllShapeCards() {
    state.shapes.forEach(({ item, result, area_m2, layer }, id) => {

        // Re-render UI
        renderShapeUI(item, result, area_m2);

        // Re-bind delete buttons (because innerHTML wipes them)
        attachShapeListeners(item, layer, id);
    });
}

if (deleteAllConfirm) {
    deleteAllConfirm.addEventListener("click", (e) => {
        e.stopPropagation();
    });

}


const settingsActions = document.querySelector(".settings-actions");

settingsActions.addEventListener("mouseleave", () => {
    deleteAllConfirm.classList.remove("show");
});

// Info Panel

const infoPanel = document.getElementById("infoPanelContent");

function setInfoPanelText(text) {
    infoPanel.innerHTML = `<p>${text}</p>`;
}

function resetInfoPanel() {
    infoPanel.innerHTML = `
        <p class="placeholder">
            Hover over any <span class="info-icon small">i</span> icon to see details here.
        </p>`;
}

export function attachShapeListeners(item, layer, id) {
    const deleteBtn   = item.querySelector(".shape-delete");
    const confirmBox  = item.querySelector(".delete-confirm");
    const confirmYes  = item.querySelector(".confirm-yes");
    const panBtn      = item.querySelector(".shape-pan");

    // DELETE
    if (deleteBtn) {
        deleteBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            closeAllDeleteConfirms();

            if (state.settings.confirmDelete) {
                confirmBox.classList.add("show");
            } else {
                drawnItems.removeLayer(layer);
                item.remove();
                state.shapes.delete(id);
                updateEmptyState();
            }
        });
    }

    // CONFIRM DELETE
    if (confirmYes) {
        confirmYes.addEventListener("click", (e) => {
            e.stopPropagation();
            drawnItems.removeLayer(layer);
            item.remove();
            state.shapes.delete(id);
            updateEmptyState();
        });
    }

    // PAN TO SHAPE
    if (panBtn) {
        panBtn.addEventListener("click", (e) => {
            e.stopPropagation();

            const bounds = layer.getBounds();
            if (bounds.isValid()) {
                map.fitBounds(bounds, {
                    paddingTopLeft: [200, 200],
                    paddingBottomRight: [sidebar.offsetWidth + 200, 200],
                    maxZoom: 14
                });
            }
        });
    }
}


// Attach behaviour to all existing and future info icons
let pinnedIcon = null;
let pinnedMessage = null;

export function initializeInfoPanelListeners() {
    document.querySelectorAll('.info-icon').forEach(icon => {

        const message = icon.dataset.info;

        // Hover temporarily overrides pinned state
        icon.addEventListener("mouseenter", () => {
            setInfoPanelText(message); 
        });

        // On leaving: restore pinned message or placeholder
        icon.addEventListener("mouseleave", () => {
            if (pinnedMessage) setInfoPanelText(pinnedMessage);
            else resetInfoPanel();
        });

        // Click-to-pin
        icon.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();

            // Unpin if clicking same icon
            if (pinnedIcon === icon) {
                icon.classList.remove("pinned");
                pinnedIcon = null;
                pinnedMessage = null;
                resetInfoPanel();
                return;
            }

            // Remove previous pinned state
            if (pinnedIcon) {
                pinnedIcon.classList.remove("pinned");
            }

            // Pin new icon
            pinnedIcon = icon;
            pinnedMessage = message;
            icon.classList.add("pinned");
            setInfoPanelText(message);
        });
    });
}

initializeInfoPanelListeners();