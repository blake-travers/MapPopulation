import json
from osgeo import gdal

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Lambda handler reached",
            "gdal_version": gdal.VersionInfo()
        })
    }
