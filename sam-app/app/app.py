import json
import time
from osgeo import gdal
from app.population_aggregator import COGAggregatorGDAL

def lambda_handler(event, context):
    start_time = time.time()
    print(f"GDAL version: {gdal.VersionInfo()}")

    method = (
        event.get("requestContext", {})
            .get("http", {})
            .get("method", "")
    )

    if method != "POST":
        return {
            "statusCode": 405,
            "headers": {
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": "Only POST supported"})
        }

    #Grab Request polygon
    try:
        body = json.loads(event.get("body", "{}"))
        polygon = body["polygon"]
        speed = body.get("speed", "fast")
    except Exception as e:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Invalid request body",
                "details": str(e)
            })
        }

    #Aggregate Population
    try:
        agg = COGAggregatorGDAL(bucket_name="population-cog20")

        population, breadth, _ = agg.aggregate_polygon(
            polygon_geojson=polygon,
            speed=speed
        )

        dt = (time.time() - start_time) * 1000

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Population aggregation failed",
                "details": str(e)
            })
        }

    #Return results
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "population": population,
            "breadth": breadth,
            "speed": speed,
            "time": int(dt)
        })
    }