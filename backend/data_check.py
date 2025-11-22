import os
from osgeo import gdal
import rasterio

# -------------------------
# Configuration
# -------------------------
output_dir = "cog_tiles"
tile_size = 5

lon_start = -180   # your generation loop starts here
lon_end = 180
lat_start = -90
lat_end = 90

# -------------------------
# Verification Logic
# -------------------------
missing_files = []
corrupted_files = []
ok_files = []

print("Checking generated COG tiles...\n")

for lon in range(lon_start, lon_end, tile_size):
    for lat in range(lat_start, lat_end, tile_size):

        minX = lon
        maxX = lon + tile_size
        minY = lat
        maxY = lat + tile_size

        tile_name = f"tile_([{minX},{maxX}],[{minY},{maxY}]).tif"
        tile_path = os.path.join(output_dir, tile_name)

        # Check 1 — File exists
        if not os.path.exists(tile_path):
            missing_files.append(tile_path)
            print(f"❌ MISSING: {tile_name}")
            continue

        # Check 2 — File is readable and valid
        ds = gdal.Open(tile_path)
        if ds is None:
            corrupted_files.append(tile_path)
            print(f"⚠️ CORRUPTED (Unreadable): {tile_name}")
            continue

        # Optional: sanity check raster size > 0
        if ds.RasterXSize == 0 or ds.RasterYSize == 0:
            corrupted_files.append(tile_path)
            print(f"⚠️ CORRUPTED (Empty raster): {tile_name}")
            continue

        ok_files.append(tile_path)

print("\n-------------------")
print("Verification Summary")
print("-------------------")

print(f"Total Expected Tiles: {len(ok_files) + len(missing_files) + len(corrupted_files)}")
print(f"✔ OK Files: {len(ok_files)}")
print(f"❌ Missing Files: {len(missing_files)}")
print(f"⚠️ Corrupted Files: {len(corrupted_files)}")

if missing_files:
    print("\nMissing tile list:")
    for f in missing_files:
        print(" -", f)

if corrupted_files:
    print("\nCorrupted tile list:")
    for f in corrupted_files:
        print(" -", f)


# Open the TIFF
ds = gdal.Open("./GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0/GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0.tif")
band = ds.GetRasterBand(1)

#Determine TIFF and Overview Sizes

print("TIFF:")
print("  Size:", ds.RasterXSize, "x", ds.RasterYSize)
print("  Bands:", ds.RasterCount)

# Overviews in the TIFF
ovr_count = band.GetOverviewCount()
print("  Overview Count:", ovr_count)

for i in range(ovr_count):
    ovr = band.GetOverview(i)
    print(f"    Overview {i}: {ovr.XSize} × {ovr.YSize}")

print("Checking specific GOD tile")

path = "./cog_tiles/tile_([115,120],[30,35]).tif"

with rasterio.open(path) as ds:
    print("Driver:", ds.driver)
    print("Size:", ds.width, ds.height)
    print("CRS:", ds.crs)
    print("Transform:", ds.transform)

    print("\n--- Overviews ---")
    for i, ovr in enumerate(ds.overviews(1)):
        print(f"Overview level {i}: factor = {ovr}")

with rasterio.open(path) as ds:
    for i, f in enumerate(ds.overviews(1)):
        ovr_width = ds.width // f
        ovr_height = ds.height // f
        print(f"Level {i}: {ovr_width} × {ovr_height}")
