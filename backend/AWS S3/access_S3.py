from osgeo import gdal

# ==============================
# AWS S3 CREDENTIALS (LOCAL TEST)
# ==============================
AWS_ACCESS_KEY_ID     = "YOUR_AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY = "YOUR_AWS_SECRET_ACCESS_KEY"
AWS_REGION            = "ap-southeast-2"

BUCKET_NAME = "population-cog20"
KEY = "tile_([0,30],[30,60]).tif"

# ==============================
# GDAL CONFIG FOR AWS S3
# ==============================
gdal.SetConfigOption("AWS_ACCESS_KEY_ID", AWS_ACCESS_KEY_ID)
gdal.SetConfigOption("AWS_SECRET_ACCESS_KEY", AWS_SECRET_ACCESS_KEY)
gdal.SetConfigOption("AWS_REGION", AWS_REGION)

# Highly recommended for COG performance
gdal.SetConfigOption("GDAL_DISABLE_READDIR_ON_OPEN", "YES")

# Optional debugging (off by default)
# gdal.SetConfigOption("CPL_DEBUG", "ON")

# ==============================
# OPEN COG FROM S3
# ==============================
cog_path = f"/vsis3/{BUCKET_NAME}/{KEY}"
print("Opening:", cog_path)

ds = gdal.Open(cog_path)
if ds is None:
    raise RuntimeError("❌ Could not open the COG from S3.")

print("✅ SUCCESS")
print("  Raster Size:", ds.RasterXSize, "x", ds.RasterYSize)
print("  Bands:", ds.RasterCount)
print("  GeoTransform:", ds.GetGeoTransform())
print("  Projection:", ds.GetProjection())

# Read a tiny sample window to force range requests
band = ds.GetRasterBand(1)
arr = band.ReadAsArray(0, 0, 128, 128)

print("✅ Sample read OK")
print("  Min:", arr.min())
print("  Max:", arr.max())

ds = None
