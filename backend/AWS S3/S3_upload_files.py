import boto3
import os
from osgeo import gdal

def upload_files_to_s3(bucket="population-cog20", directory="cog_tiles"):

    s3 = boto3.client("s3")

    for root, _, files in os.walk(directory):
        for f in files:
            if not f.endswith(".tif"):
                continue

            local_path = os.path.join(root, f)
            key = os.path.relpath(local_path, directory).replace("\\", "/")

            print(f"Uploading {key}")
            s3.upload_file(local_path, bucket, key)


upload_files_to_s3()

"""

test_key = "tile_([-30,0],[0,30]).tif"
path = f"/vsis3/{BUCKET}/{test_key}"

gdal.SetConfigOption(
    "AWS_S3_ENDPOINT",
    "s3.ap-southeast-4.amazonaws.com"
)
gdal.SetConfigOption("GDAL_DISABLE_READDIR_ON_OPEN", "YES")

print("Opening:", path)
ds = gdal.Open(path)
if ds is None:
    raise RuntimeError("GDAL open failed")

print("SUCCESS:", ds.RasterXSize, ds.RasterYSize)
"""