from COG_polygon_aggregator import COGPolygonAggregator

aggregator = COGPolygonAggregator()

example_polygons = [
    ("Small square (Melbourne CBD)", {"type": "Polygon","coordinates":[[[144.955, -37.820],[144.965, -37.820],[144.965, -37.810],[144.955, -37.810],[144.955, -37.820]]]}),
    ("Europe rectangle", {"type": "Polygon","coordinates": [[[10, 50],[20, 50],[20, 55],[10, 55],[10, 50]]]}),
    ("Australia east coast region", {"type": "Polygon","coordinates": [[[149, -36],[151, -36],[153, -34],[153, -32],[151, -30],[149, -33],[149, -36]]]}),
    ("Concave polygon test", {"type": "Polygon","coordinates": [[[0, 0],[4, 0],[4, 4],[2, 2],[0, 4],[0, 0]]]}),
    ("Huge region (EU + Middle East)", {"type": "Polygon","coordinates": [[[-10, 30],[40, 30],[40, 60],[-10, 60],[-10, 30]]]}),
    ("Tiny subpixel polygon", {"type": "Polygon","coordinates": [[[12.0001, 48.0001],[12.0002, 48.0001],[12.0002, 48.0002],[12.0001, 48.0002],[12.0001, 48.0001]]]})
]

tile_keys = []

#Auto generate required keys
for min_lon in range(-180, 180, 10):
    for min_lat in range(-90, 90, 10):
        key = f"tile_([{min_lon},{min_lon+10}],[{min_lat},{min_lat+10}]).tif"
        tile_keys.append(key)


print("\n--- Running Cloudflare COG polygon tests ---\n")

for name, polygon in example_polygons:
    print(f"Testing: {name}")

    try:
        pop = aggregator.aggregate_polygon(polygon_geojson=polygon, tile_keys=tile_keys, max_depth=0)
        print(f"  Population = {pop:,.2f}\n")

    except Exception as e:
        print(f"  ERROR: {e}\n")

print("--- All tests completed ---")