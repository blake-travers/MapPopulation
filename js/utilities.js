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