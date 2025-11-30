from osgeo import gdal

# Your R2 credentials
access_key = "58adf3b5b777e3c092c0cee45526d9d7"
secret_key = "da5a69fe0348576e274097a1d49b3aa78f8548159733234478da6e8dfd3f61da"
bucket_name = "population-cog-5"
account_id = "2d25f237b013343aaf1d21b860116b79"
key = "tile_([-10,0],[-10,0]).tif"

endpoint = f"{account_id}.r2.cloudflarestorage.com"

gdal.SetConfigOption("AWS_ACCESS_KEY_ID", access_key)
gdal.SetConfigOption("AWS_SECRET_ACCESS_KEY", secret_key)
gdal.SetConfigOption("AWS_REGION", "auto")
gdal.SetConfigOption("AWS_S3_ENDPOINT", endpoint)
gdal.SetConfigOption("AWS_VIRTUAL_HOSTING", "FALSE")  # use path-style for R2

# Try to open the COG
cog_path = f"/vsis3/{bucket_name}/{key}"
print("Opening:", cog_path)

ds = gdal.Open(cog_path)
if ds is None:
    raise RuntimeError("Could not open the COG from R2. Check credentials + endpoint.")

print("SUCCESS:", ds.RasterXSize, ds.RasterYSize)
