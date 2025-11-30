from osgeo import gdal


def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": gdal.VersionInfo()
    }
