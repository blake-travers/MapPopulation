import json
import rasterio

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "rasterio": rasterio.__version__,
            "gdal": rasterio.__gdal_version__
        })
    }