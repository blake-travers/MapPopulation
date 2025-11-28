import json
import subprocess
import sys
from osgeo import gdal
from population_aggregator import COGAggregatorGDAL
import time


def gdal_version():
    result = subprocess.check_output(
        ["gdalinfo", "--version"],
        stderr=subprocess.STDOUT,
        text=True
    )
    return result.strip()


def lambda_handler(event, context):
    # Optional mode flag
    if event.get("mode") == "test":
        return {
            "statusCode": 200,
            "body": json.dumps({
                "mode": "polygon_test",
                "results": run_polygon_tests()
            })
        }

    return {
        "statusCode": 200,
        "body": json.dumps({"mode": "lambda_alive"})
    }

def run_polygon_tests():
    agg = COGAggregatorGDAL(bucket_name="population-cog20")

    example_polygons = [
        ("Small square (Melbourne CBD)", {"type": "Polygon","coordinates":[[[144.955, -37.820],[144.965, -37.820],[144.965, -37.810],[144.955, -37.810],[144.955, -37.820]]]}),
        ("Europe rectangle", {"type": "Polygon","coordinates": [[[10, 50],[20, 50],[20, 55],[10, 55],[10, 50]]]}),
        ("Australia east coast region", {"type": "Polygon","coordinates": [[[149, -36],[151, -36],[153, -34],[153, -32],[151, -30],[149, -33],[149, -36]]]}),
        ("Concave polygon test", {"type": "Polygon","coordinates": [[[0, 0],[4, 0],[4, 4],[2, 2],[0, 4],[0, 0]]]}),
        ("Huge region (EU + Middle East)", {"type": "Polygon","coordinates": [[[-10, 30],[40, 30],[40, 60],[-10, 60],[-10, 30]]]}),
        ("Tiny subpixel polygon", {"type": "Polygon","coordinates": [[[12.0001, 48.0001],[12.0002, 48.0001],[12.0002, 48.0002],[12.0001, 48.0002],[12.0001, 48.0001]]]})
    ]

    print("\n--- Running COG polygon tests ---\n")

    for name, polygon in example_polygons:
        print(f"Testing: {name}")
        
        start = time.time()
        try:
            pop = agg.aggregate_polygon(polygon_geojson=polygon, max_depth=0)

            dt = time.time() - start

            print(f"  Population = {pop:,.2f}")
            print(f"  Time taken = {dt:.4f} seconds\n")

        except Exception as e:
            print(f"  ERROR: {e}\n")

    print("--- All tests completed ---")


if __name__ == "__main__":
    #LOCAL DEBUG MODE
    print("Running in LOCAL debug mode")
    print("GDAL:", gdal_version())
    run_polygon_tests()
