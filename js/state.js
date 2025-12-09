const shapes = new Map();
let shapeCounter = 1;
let currentAreaUnit = "km2";

export const DEFAULT_SETTINGS = {
    calcMode: "fast",
    mapType: "vector_carto",
    areaUnit: "km2",
    confirmDelete: false,
    debugMode: false
};

export const state = {
    shapes: new Map(),
    shapeCounter: 1,
    settings: { ...DEFAULT_SETTINGS }
};

