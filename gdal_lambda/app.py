import json
import subprocess
import sys
from osgeo import gdal


def gdal_version():
    result = subprocess.check_output(
        ["gdalinfo", "--version"],
        stderr=subprocess.STDOUT,
        text=True
    )
    return result.strip()


def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "gdal": gdal_version(),
            "mode": "lambda"
        })
    }


if __name__ == "__main__":
    #LOCAL DEBUG MODE
    print("Running in LOCAL debug mode")
    print("GDAL:", gdal_version())
