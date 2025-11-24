import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np

cog_path = "./cog_tiles/tile_([-180,-150],[-30,-0]).tif"

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
    print("Sum:", np.sum(ovr))
    factor = 2**15 // ovr.shape[0]
    total_pop = np.mean(ovr) * (ovr.shape[0]*factor) * (ovr.shape[1]*factor)
    #print(f"Overview {i} total population: {total_pop}")

