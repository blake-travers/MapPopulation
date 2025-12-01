import json
from osgeo import gdal

def lambda_handler(event, context):

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "message": "GDAL OK",
            "gdal_version": gdal.VersionInfo()
        })
    }


"""
Build & Deploy zip-based docker file:

1. Rebuild Docker Image (cd sam-app)

    docker build -t gdal-zip-builder -f build/Dockerfile .          (Returns 30-200+ lines)

2. Extract package.zip

    docker create --name gdal_tmp gdal-zip-builder                  (Returns 1 line)
    docker cp gdal_tmp:/tmp/package.zip dist/package.zip            (Returns 1 line)
    docker rm gdal_tmp                                              (Returns 1 line)

3. Checks & tests

    ls -lh dist/package.zip
    sam local invoke

4. Deploy to Lambda

    sam deploy

"""