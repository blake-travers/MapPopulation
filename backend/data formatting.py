from osgeo import gdal
import rasterio
import numpy as np
import os
import time

def downsample_sum(arr):
    """Downsample by factor 2 using SUM not AVERAGE."""
    return arr.reshape(arr.shape[0]//2, 2,
                       arr.shape[1]//2, 2).sum(axis=(1,3))


def build_sum_overviews(path):
    """Open a TIFF and overwrite all overview levels using SUM pyramids."""
    ds = gdal.Open(path, gdal.GA_Update)
    band = ds.GetRasterBand(1)

    # Read base buffer
    arr = band.ReadAsArray().astype(np.float64)
    band.WriteArray(arr)

    # Build SUM pyramid
    for i in range(band.GetOverviewCount()):
        arr = downsample_sum(arr)

        ovr = band.GetOverview(i)
        ovr.WriteArray(arr)

    band.FlushCache()
    ds = None

def round_all_levels(path, decimals=6):
    """
    After EVERYTHING is built, round ONCE at the end.
    This prevents all rounding error accumulation.
    """
    ds = gdal.Open(path, gdal.GA_Update)
    band = ds.GetRasterBand(1)

    # Round base
    arr = band.ReadAsArray()
    arr = np.round(arr, decimals)
    band.WriteArray(arr)

    # Round all overviews
    for i in range(band.GetOverviewCount()):
        ovr = band.GetOverview(i)
        arr = ovr.ReadAsArray()
        arr = np.round(arr, decimals)
        ovr.WriteArray(arr)

    band.FlushCache()
    ds = None
#Convert Tif and Overviews to a COG
input_tif = "./GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0/GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0.tif"
output_dir = "cog_tiles"
os.makedirs(output_dir, exist_ok=True)


# Loop longitude (-180 to 170)
tile_size = 30
num_pixels = 2**15
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

        # Extract 5×5 degree window
        gdal.Translate(
            temp_raw,
            input_tif,
            projWin=[minX, maxY, maxX, minY],
            format="GTiff"
        )

        # Resample tile to target resolution
        gdal.Translate(
            temp_resampled, #End resolution
            temp_raw, #Start resolution
            width=num_pixels,
            height=num_pixels,
            resampleAlg="bilinear",
            format="GTiff"
        )

        # Change to float32 to improve storage efficiency
        with rasterio.open(temp_resampled, "r+") as ds:
            arr = ds.read(1)
            arr = arr.astype("float32")  # reduce dtype size
            ds.write(arr, 1)

        ds = gdal.Open(temp_resampled, gdal.GA_Update)
        overview_levels = []
        f = 2
        while f < num_pixels:
            overview_levels.append(f)
            f *= 2
        ds.BuildOverviews("NONE", overview_levels)
        ds = None

        # Write SUM overviews
        build_sum_overviews(temp_resampled)

        round_all_levels(temp_resampled)

        # Convert to COG
        gdal.Translate(
            final_cog,
            temp_resampled,
            format="COG",
            creationOptions=[
                "COMPRESS=DEFLATE",
                "PREDICTOR=2",
                "BLOCKSIZE=512",
                "BIGTIFF=YES",
                "OVERVIEWS=IGNORE_EXISTING"
            ]
        )

        print(f"Elapsed: {(time.time() - start_time):.1f}s")

print("COG creation complete.")


