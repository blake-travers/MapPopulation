import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np

cog_path = "./cog_tiles/tile_([-180,-170],[-80,-70]).tif"

with rasterio.open(cog_path) as src:
    print("CRS:", src.crs)
    print("Bounds:", src.bounds)
    print("Bands:", src.count)
    print("Width x Height:", src.width, "x", src.height)

    for b in range(1, src.count + 1):
        band = src.read(b).astype(float)

        print(f"\n=== Band {b} Info ===")
        print("Shape:", band.shape, "| dtype:", band.dtype)

        # --- Count NODATA / 0 / >0 ---
        nodata = np.isnan(band) | np.isinf(band)
        zero = (band == 0)
        positive = band > 0

        print("NODATA pixels:", np.count_nonzero(nodata))
        print("Zero-value pixels:", np.count_nonzero(zero))
        print("Positive (>0) pixels:", np.count_nonzero(positive))

        # --- Basic statistics ---
        arr_valid = band[~nodata]
        if arr_valid.size > 0:
            print("Min:", np.nanmin(arr_valid))
            print("Max:", np.nanmax(arr_valid))
            print("Mean:", np.nanmean(arr_valid))
        else:
            print("All pixels are NODATA")

        # --- Unique values (cap at 20 to avoid huge prints) ---
        unique_vals = np.unique(arr_valid)
        print(f"Unique values (showing up to 20): {unique_vals[:20]}")

        # --- Small raw sample of pixel values (5x5 window) ---
        print("\nSample 5x5 window:")
        h, w = band.shape
        h0 = min(5, h)
        w0 = min(5, w)
        print(band[:h0, :w0])

    # --- Visualization clip at max=20 ---
    arr = src.read(1).astype(float)
    arr = np.clip(arr, 0, 20)

    plt.figure(figsize=(8, 8))
    #show(arr, cmap="gray")
    plt.title("COG Band 1 (clipped max=20)")
    plt.show()
