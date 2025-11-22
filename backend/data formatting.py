from osgeo import gdal
import rasterio
import numpy as np
import os
import time

#Convert Tif and Overviews to a COG
input_tif = "./GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0/GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0.tif"
output_dir = "cog_tiles"
os.makedirs(output_dir, exist_ok=True)


# Loop longitude (-180 to 170)
tile_size = 10
num_pixels = 2**13
pixel_size = (tile_size*3600) / num_pixels
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

        # Round values to improve storage efficiency
        with rasterio.open(temp_raw, "r+") as ds:
            arr = ds.read(1)

            arr = np.round(arr, 2)
            arr = arr.astype("float32")  # reduce dtype size

            ds.write(arr, 1)

        # Step 3: Resample tile to target resolution
        gdal.Translate(
            temp_resampled,
            temp_raw,
            width=num_pixels,
            height=num_pixels,
            resampleAlg="bilinear",
            format="GTiff"
        )

        # Convert to COG
        gdal.Translate(
            final_cog,
            temp_resampled,
            format="COG",
            creationOptions=[
                "COMPRESS=DEFLATE",
                "PREDICTOR=2",
                "BLOCKSIZE=512",
                "RESAMPLING=AVERAGE",
                "OVERVIEWS=AUTO",
                "BIGTIFF=YES",
            ]
        )

        print(f"Elapsed: {(time.time() - start_time):.1f}s")

print("COG creation complete.")


