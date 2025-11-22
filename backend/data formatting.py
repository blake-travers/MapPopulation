from osgeo import gdal
import rasterio
import numpy as np
import os
import time

#Convert Tif and Overviews to a COG
input_tif = "./GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0/GHS_POP_E2025_GLOBE_R2023A_4326_3ss_V1_0.tif"
output_dir = "cog_tiles"
os.makedirs(output_dir, exist_ok=True)

start_time = time.time()

# Loop longitude (-180 to 175)
tile_size = 5
for lon in range(-180, 180, tile_size):

    # Loop latitude (-90 to 90)
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

        # Round values to improve storage efficiency
        with rasterio.open(temp_tile, "r+") as ds:
            arr = ds.read(1)

            arr = np.round(arr, 2)
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

        print(f"Elapsed: {(time.time() - start_time):.1f}s")

print("COG creation complete.")


