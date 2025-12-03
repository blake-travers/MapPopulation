import json
from osgeo import gdal
from app.population_aggregator import test_polygons

def lambda_handler(event, context):

    print(f"GDAL Version: {gdal.VersionInfo()}")
    
    print("Running polygon population tests...")
    results = test_polygons()
    print("Finished running polygon tests.\n")

    for i, result in enumerate(results, start=1):
        print(f"--- Test Polygon {i} ---")
        for key, value in result.items():
            print(f"{key}: {value}")
        print()

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": "Polygon tests completed successfully",
            "gdal_version": gdal.VersionInfo(),
            "num_tests": len(results),
            "results": results
        })
    }