from osgeo import gdal
import rasterio
import numpy as np
import os
import time

import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np

from osgeo import gdal
import numpy as np


def format_data():
    #Convert Tif and Overviews to a COG
    input_tif = "./GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0/GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0.tif"
    output_dir = "cog_tiles"
    os.makedirs(output_dir, exist_ok=True)

    scales = [1000, 1000, 1000,
            100, 100, 100, 100, 100,
            10, 10, 10, 10, 10,
            1, 1]

    tile_size = 30
    num_pixels = 2**14
    print(f'Pixel Size: {(tile_size*3600)/num_pixels}", {tile_size/num_pixels}d')
    correction_factor = ((tile_size/num_pixels) / (3.0/3600.0))**2

    def downsample_sum(arr):
        h, w = arr.shape
        arr = arr[:h//2*2, :w//2*2]   # ensure even
        return arr.reshape(h//2, 2, w//2, 2).sum(axis=(1,3))

    def scale_array_uint32(arr, scale):
        scaled = np.rint(arr * scale)

        if np.any(scaled < 0):
            raise ValueError(f"Band {i+1}: scaled values < 0 — check scaling logic")

        if np.any(scaled > 4294967295):
            raise ValueError( f"Band {i+1}: scaled values exceed uint32 limit — "f"max={scaled.max()} scale={scale}")
        scaled = scaled.astype("uint32")
        return scaled

    # Loop longitude (-180 to 180)
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

                    # Set data type for base band
            with rasterio.open(temp_resampled, "r+") as ds:
                arr = ds.read(1)
                arr = arr * correction_factor

                ov = arr.copy()
                arr_uint32 = scale_array_uint32(arr, scale=scales[0])
                ds.write(arr_uint32, 1)

            #3. Build Overviews
            overviews = []

            #Set scales for overviews

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

            band = ds.GetRasterBand(1)
            band.SetMetadataItem("PYRAMID_SCALES", ",".join(map(str, scales)))

            num_levels = 1 + len(overviews)
            assert len(scales) == num_levels, (
                f"scales has length {len(scales)} but {num_levels} "
                f"levels (base + {len(overviews)} overviews) are required"
            )

            # Write our own SUM overviews and round
            for i, ov in enumerate(overviews):
                scale = scales[i+1]

                ov_uint32 = scale_array_uint32(ov, scale=scale)

                ovr_band = band.GetOverview(i)
                ovr_band.WriteArray(ov_uint32)

            ds = None   # flush to disk
            # Convert to COG
            gdal.Translate(
                final_cog,
                temp_resampled,
                format="COG",
                creationOptions=[
                    "COMPRESS=ZSTD",
                    "PREDICTOR=3",
                    "BLOCKSIZE=512",
                    "BIGTIFF=YES"
                ]
            )

            print(f"Elapsed: {(time.time() - start_time):.1f}s")

    print("COG creation complete.")

def check_single_file():
    print("Starting Check")
    cog_path = "./cog_tiles/tile_([0,30],[30,60]).tif"

    ds = gdal.Open(cog_path)
    print("COG File loaded")
    band = ds.GetRasterBand(1)

    # --- read scales from metadata ---
    scale_str = band.GetMetadataItem("PYRAMID_SCALES")
    if scale_str is None:
        raise RuntimeError("Missing PYRAMID_SCALES metadata")

    scales = list(map(float, scale_str.split(",")))

    # --- base raster (level 0) ---
    print("Reading band 1, converting to float64 for printout...")
    base_raw = band.ReadAsArray()
    base = base_raw.astype(np.float64) / scales[0]

    print("=== Base Raster ===")
    print("Shape:", base.shape)
    print("Min:", np.min(base))
    print("Max:", np.max(base))
    print("Mean:", np.mean(base))
    print("Sum:", np.sum(base))

    # --- overviews ---
    num_ovr = band.GetOverviewCount()

    # sanity check
    assert len(scales) >= 1 + num_ovr, (
        f"Need {1 + num_ovr} scales, found {len(scales)}"
    )

    for i in range(num_ovr):
        ovr_band = band.GetOverview(i)
        ovr_raw = ovr_band.ReadAsArray()

        scale = scales[i + 1]
        ovr = ovr_raw.astype(np.float64) / scale

        print(f"\n=== Overview {i} ===")
        print("Shape:", ovr.shape)
        print("Min:", np.min(ovr))
        print("Max:", np.max(ovr))
        print("Mean:", np.mean(ovr))
        print(f"Overview {i} total population:", np.sum(ovr))

def check_all_data():
    # -------------------------
    # Configuration
    # -------------------------
    output_dir = "cog_tiles"
    tile_size = 30

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

check_single_file()