import { state } from "./state.js";
import { map } from "./map.js";

// Search Functionality //

function zoomForFeature(props) {
    switch (props.osm_value) {
        case "country": return 4;
        case "state":
        case "province":
        case "region": return 6;
        case "county": return 7;
        case "city": return 10;
        case "town": return 11;
        case "village":
        case "municipality": return 12;
        default: return 10;
    }
}

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

                        const zoom = 10;

                        map.setView([lat, lon], zoomForFeature(props), { animate: false });

                        const mapSize = map.getSize();
                        const targetX = mapSize.x * 0.35;
                        const centerX = mapSize.x * 0.5;

                        const offsetX = centerX - targetX;

                        // Step 3: pan by pixel offset
                        map.panBy([offsetX, 0], { animate: false });

                        L.marker([lat, lon]).addTo(map).bindPopup(label).openPopup();

                        searchResultsDiv.style.display = "none";
                    }
                );

                searchResultsDiv.appendChild(item);
            }
        );
        searchResultsDiv.style.display = "block";
    }
    catch (err) {
        console.warn("Search fetch aborted:", err);
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