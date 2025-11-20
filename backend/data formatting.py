from osgeo import gdal

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

#Convert Tif and Overviews to a COG

import rasterio
import numpy as np
import os

input_tif = "./GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0/GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0.tif"
output_dir = "cog_tiles"
os.makedirs(output_dir, exist_ok=True)

# Loop longitude (-180 to 175)
tile_size = 3
for lon in range(-180, 180, tile_size):
    for lat in range(-90, 90, tile_size):
        
        minX = lon
        maxX = lon + tile_size
        minY = lat
        maxY = lat + tile_size

        print(f"Processing Tile [{minX},{maxX}],[{minY},{maxY}]")
        
        tile_name = f"tile_([{minX},{maxX}],[{minY},{maxY}]).tif"
        temp_tile = os.path.join(output_dir, "temp.tif")
        final_cog = os.path.join(output_dir, tile_name)

        # Extract 5×5 degree window
        gdal.Translate(
            temp_tile,
            input_tif,
            projWin=[minX, maxY, maxX, minY],
            format="GTiff"
        )

        with rasterio.open(temp_tile, "r+") as ds:
            arr = ds.read(1)

            arr = np.round(arr, 3)    # 3 decimal places
            arr[arr < 1e-6] = 0.0     # Threshold
            arr = arr.astype("float32")  # reduce dtype size

            ds.write(arr, 1)

        # Convert to COG
        gdal.Translate(
            final_cog,
            temp_tile,
            format="COG",
            creationOptions=[
                "COMPRESS=DEFLATE",
                "PREDICTOR=2",
                "BLOCKSIZE=512",
                "RESAMPLING=AVERAGE",
                "OVERVIEWS=IGNORE_EXISTING",
                "BIGTIFF=YES",
            ]
        )

print("COG creation complete.")


