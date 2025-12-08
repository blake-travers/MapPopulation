const shapes = new Map();
let shapeCounter = 1;
let currentAreaUnit = "km2";

const DEFAULT_SETTINGS = {calcMode: "fast", mapType: "vector_carto", units: "km2", shapePanning: false, confirmDelete: false};

let confirmDeleteEnabled = DEFAULT_SETTINGS.confirmDelete;

