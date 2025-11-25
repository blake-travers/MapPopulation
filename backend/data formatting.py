from osgeo import gdal
import rasterio
import numpy as np
import os
import time

#Convert Tif and Overviews to a COG
input_tif = "./GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0/GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0.tif"
output_dir = "cog_tiles"
os.makedirs(output_dir, exist_ok=True)



tile_size = 30
num_pixels = 2**14
print(f'Pixel Size: {(tile_size*3600)/num_pixels}", {tile_size/num_pixels}d')
correction_factor = ((tile_size/num_pixels) / (3.0/3600.0))**2

def downsample_sum(arr):
    h, w = arr.shape
    arr = arr[:h//2*2, :w//2*2]   # ensure even
    return arr.reshape(h//2, 2, w//2, 2).sum(axis=(1,3))

def round_array(arr, decimals=6):
    arr[arr < 1e-6] = 0
    return arr.astype(np.float32)#np.round(arr.astype(np.float32), decimals=decimals)

# Loop longitude (-180 to 170)
for lon in range(-180, 180, tile_size):

    # Loop latitude (-90 to 90)
    for lat in range(-90, 90, tile_size):
        
        minX, maxX = lon, lon + tile_size
        minY, maxY = lat, lat + tile_size

        print(f"Processing Tile [{minX},{maxX}],[{minY},{maxY}]")
        start_time = time.time()
        
        tile_name = f"tile_([{minX},{maxX}],[{minY},{maxY}]).tif"

        temp_raw = os.path.join(output_dir, "temp_raw.tif")
        temp_resampled = os.path.join(output_dir, "temp_resampled.tif")

        final_cog = os.path.join(output_dir, tile_name)

        #1. Extract 5×5 degree window
        gdal.Translate(
            temp_raw,
            input_tif,
            projWin=[minX, maxY, maxX, minY],
            format="GTiff"
        )

        #2. Resample tile to target resolution. Ensure population values are summed and not averaged
        gdal.Warp(
            temp_resampled,
            temp_raw,
            width=num_pixels,
            height=num_pixels,
            resampleAlg="average",
            format="GTiff"
        )

        # Round values to improve storage efficiency, correct values by resampling correction factor. Make a copy for overveiws before rounding
        with rasterio.open(temp_resampled, "r+") as ds:
            arr = ds.read(1)
            arr = arr * correction_factor
            arr = arr.astype("float32")  # reduce dtype size
            ov = arr.copy()
            arr = round_array(arr, decimals=5)
            ds.write(arr, 1)

        #3. Build Overviews
        
        overviews = []
        while ov.shape[0] > 1 and ov.shape[1] > 1:
            ov = downsample_sum(ov)
            overviews.append(ov)
        ds = gdal.Open(temp_resampled, gdal.GA_Update)

        #Build required overview levels
        levels = []
        level = 1
        for ov in overviews:
            level *= 2
            levels.append(level)
        ds.BuildOverviews("NONE", levels)

        # Write our own SUM overviews and round
        band = ds.GetRasterBand(1)
        for i, ov in enumerate(overviews):
            ov_rounded = round_array(ov, decimals=5)
            ovr_band = band.GetOverview(i)
            ovr_band.WriteArray(ov_rounded)

        ds = None   # flush to disk
        # Convert to COG
        gdal.Translate(
            final_cog,
            temp_resampled,
            format="COG",
            creationOptions=[
                "COMPRESS=DEFLATE",
                "PREDICTOR=2",
                "BLOCKSIZE=512",
                "BIGTIFF=YES"
            ]
        )

        print(f"Elapsed: {(time.time() - start_time):.1f}s")

print("COG creation complete.")


import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np

cog_path = "./cog_tiles/tile_([0,30],[30,60]).tif"

from osgeo import gdal
import numpy as np

ds = gdal.Open(cog_path)
band = ds.GetRasterBand(1)

base = band.ReadAsArray()
print("=== Base Raster ===")
print("Shape:", base.shape)
print("Min:", np.min(base))
print("Max:", np.max(base))
print("Mean:", np.mean(base))
print("Sum:", np.sum(base))

# Overviews
num_ovr = band.GetOverviewCount()
for i in range(num_ovr):
    ovr = band.GetOverview(i).ReadAsArray()
    print(f"\n=== Overview {i} ===")
    print("Shape:", ovr.shape)
    print("Min:", np.min(ovr))
    print("Max:", np.max(ovr))
    print("Mean:", np.mean(ovr))
    #factor = (2**11 // ovr.shape[0]) * 2.197
    #total_pop = np.mean(ovr) * (ovr.shape[0]*factor) * (ovr.shape[1]*factor)
    total_pop = np.sum(ovr)
    print(f"Overview {i} total population: {total_pop}")
