from osgeo import gdal
import rasterio
import numpy as np
import os
import time

#Convert Tif and Overviews to a COG
input_tif = "./GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0/GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0.tif"
output_dir = "cog_tiles"
os.makedirs(output_dir, exist_ok=True)

band_scales = [100, 100, 100, 100, 100, 10, 10, 10, 10, 10, 1, 1, 1, 1, 1, 1]
#Note: need to manually divide each band by what this is here


tile_size = 30
num_pixels = 2**14
print(f'Pixel Size: {(tile_size*3600)/num_pixels}", {tile_size/num_pixels}d')
correction_factor = ((tile_size/num_pixels) / (3.0/3600.0))**2

def downsample_sum(arr):
    h, w = arr.shape
    arr = arr[:h//2*2, :w//2*2]   # ensure even
    return arr.reshape(h//2, 2, w//2, 2).sum(axis=(1,3))

# Loop longitude (-180 to 180)
for lon in range(0, 30, tile_size):
    # Loop latitude (-90 to 90)
    for lat in range(30, 60, tile_size):
        
        minX, maxX = lon, lon + tile_size
        minY, maxY = lat, lat + tile_size

        print(f"Processing Tile [{minX},{maxX}],[{minY},{maxY}]")
        start_time = time.time()
        
        tile_name = f"tile_([{minX},{maxX}],[{minY},{maxY}]).tif"

        temp_raw = os.path.join(output_dir, "temp_raw.tif")
        temp_resampled = os.path.join(output_dir, "temp_resampled.tif")

        final_cog = os.path.join(output_dir, tile_name)

        warnings = 0

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
            ds.write(arr, 1)

        # ============================================================
        # 3. Build multi-band pyramid (uint32 with configurable scaling)
        # ============================================================

        # Load full-resolution array
        with rasterio.open(temp_resampled) as src:
            full = src.read(1).astype("float32")  # band 1 (float32)
            full *= correction_factor

        # Build SUM pyramid
        pyramid = [full]
        arr = full.copy()
        while arr.shape[0] > 1 and arr.shape[1] > 1:
            arr = downsample_sum(arr)
            pyramid.append(arr)

        num_bands = len(pyramid)
        assert num_bands <= len(band_scales), f"Need {num_bands} scale entries in band_scales. Current is {len(band_scales)}"

        # Create multi-band output GTiff
        temp_multiband = os.path.join(output_dir, "temp_multiband.tif")
        driver = gdal.GetDriverByName("GTiff")
        ds_mb = driver.Create(
            temp_multiband,
            pyramid[0].shape[1],
            pyramid[0].shape[0],
            num_bands,
            gdal.GDT_UInt32,
            options=[
                "TILED=YES",
                "BLOCKSIZE=512",
                "BIGTIFF=YES",
                "COMPRESS=ZSTD"
            ]
        )

        # Get geotransform from resampled GDAL dataset
        ds_in = gdal.Open(temp_resampled)
        gt0 = ds_in.GetGeoTransform()

        # Write each band
        for i, level in enumerate(pyramid):
            scale = band_scales[i]

            # Scale + clamp to uint32 safe range
            scaled = np.rint(level * scale)
            if np.any(scaled < 0):
                raise ValueError(f"Band {i+1}: scaled values < 0 — check scaling logic")

            if np.any(scaled > 1073741823):
                warnings += 1

            if np.any(scaled > 4294967295):
                raise ValueError(
                    f"Band {i+1}: scaled values exceed uint32 limit — "
                    f"max={scaled.max()} scale={scale}"
                )
            scaled = scaled.astype("uint32")

            band = ds_mb.GetRasterBand(i + 1)
            band.WriteArray(scaled)
            band.SetMetadataItem("SCALE", str(scale)) #Set Scale value

            # Compute per-band geotransform
            f = 2 ** i
            new_gt = (
                gt0[0],
                gt0[1] * f,
                gt0[2],
                gt0[3],
                gt0[4],
                gt0[5] * f
            )
            ds_mb.SetGeoTransform(new_gt)

        ds_mb.FlushCache()
        ds_mb = None
        ds_in = None

        # ============================================================
        # 4. Convert multi-band file to final COG
        # ============================================================
        gdal.Translate(
            final_cog,
            temp_multiband,
            format="COG",
            creationOptions=[
                "COMPRESS=ZSTD",
                "BLOCKSIZE=512",
                "BIGTIFF=YES"
            ]
        )

        os.remove(temp_multiband)
        os.remove(temp_resampled)
        os.remove(temp_raw)
        if warnings > 0:
            print(f"Warning: Numbers close to max: {warnings}")




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

band_count = ds.RasterCount

for i in range(1, band_count + 1):
    b = ds.GetRasterBand(i)
    arr_raw = b.ReadAsArray()

    scale = band_scales[i - 1]
    arr = arr_raw.astype(np.float64) / scale  # unscale to real population

    print(f"\n=== Band {i} ===")
    print("Shape:", arr.shape)
    print("Min:", np.min(arr))
    print("Max:", np.max(arr))
    print("Mean:", np.mean(arr))
    print("Sum:", np.sum(arr))