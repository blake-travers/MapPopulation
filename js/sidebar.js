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
    state.shapes.forEach(({ item, area_m2 }) => {
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

// ===== Confirm Delete Setting =====
document.querySelectorAll('input[name="confirmDelete"]').forEach(radio => {
    radio.addEventListener("change", () => {
        state.settings.confirmDelete = radio.value === "true";
    });
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

//next frame, open sidebar without transitions
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
        refreshAllAreas();
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

    document.querySelector(
        `input[name="mapType"][value="${state.settings.mapType}"]`
    ).checked = true;

    document.querySelector(
        `input[name="confirmDelete"][value="${state.settings.confirmDelete}"]`
    ).checked = true;

    // ---- Apply map effects ----
    map.removeLayer(mapState.currentBaseLayer);
    mapState.currentBaseLayer = baseLayers[state.settings.mapType];
    mapState.currentBaseLayer.addTo(map);

    // ---- Apply area effects ----
    refreshAllAreas();
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


if (deleteAllConfirm) {
    deleteAllConfirm.addEventListener("click", (e) => {
        e.stopPropagation();
    });

}


const settingsActions = document.querySelector(".settings-actions");

settingsActions.addEventListener("mouseleave", () => {
    deleteAllConfirm.classList.remove("show");
});
