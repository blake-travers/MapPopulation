from osgeo import gdal
from typing import Dict, List
from shapely.geometry import shape
import numpy as np

class COGAggregatorGDAL:
    def __init__(self,
        access_key: str = "58adf3b5b777e3c092c0cee45526d9d7",
        secret_key: str = "da5a69fe0348576e274097a1d49b3aa78f8548159733234478da6e8dfd3f61da",
        account_id: str = "2d25f237b013343aaf1d21b860116b79",
        bucket_name: str = "population-cog-5", region: str = "auto"
    ):
        """
        Configure GDAL to authenticate with Cloudflare R2
        using /vsis3/ with path-style access.
        """

        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.account_id = account_id
        self.region = region
        self.initial_depth = 14

        # Cloudflare R2 endpoint (NO https:// — GDAL adds automatically)
        self.endpoint = f"{self.account_id}.r2.cloudflarestorage.com"

        # ---- GDAL CONFIGURATION ----
        gdal.SetConfigOption("AWS_ACCESS_KEY_ID", self.access_key)
        gdal.SetConfigOption("AWS_SECRET_ACCESS_KEY", self.secret_key)

        # Required for R2 Cloudfare
        gdal.SetConfigOption("AWS_REGION", self.region)
        gdal.SetConfigOption("AWS_S3_ENDPOINT", self.endpoint)
        gdal.SetConfigOption("AWS_VIRTUAL_HOSTING", "FALSE")  # path-style required
        gdal.SetConfigOption("GDAL_DISABLE_READDIR_ON_OPEN", "YES")  # speeds up COG access

        # Optional speed improvements:
        #gdal.SetConfigOption("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif,.tiff,.ovr")
        #gdal.SetConfigOption("CPL_DEBUG", "OFF")

        print("[GDAL] Configured for Cloudflare R2 via /vsis3/")

        self.tile_keys = self._generate_global_tile_keys(tile_size=30)

    def _generate_global_tile_keys(self, tile_size: int) -> List[str]:
        """
        Generate all tile keys of the form:
        tile_([lon_min,lon_max],[lat_min,lat_max]).tif

        tile_size must divide 360 (lon) and 180 (lat), e.g. 5, 10, 30.
        """

        if 180 % tile_size != 0:
            raise ValueError(f"Tile size {tile_size}° does not evenly divide the globe.")

        keys = []

        print(f"Building Keys for tile_size of {tile_size}")
        print(f'Pixel Size: {(tile_size*3600)/(2**self.initial_depth)}" or {tile_size/(2**self.initial_depth)}°')

        for lon1 in range(-180, 180, tile_size):
            lon2 = lon1 + tile_size

            for lat1 in range(-90, 90, tile_size):
                lat2 = lat1 + tile_size

                key = f"tile_([{lon1},{lon2}],[{lat1},{lat2}]).tif"
                keys.append(key)

        return keys

    def _build_url(self, key: str) -> str:
        """
        Build a GDAL /vsis3/ URL to a COG tile.
        """
        print(f"Building URL /vsis3/{self.bucket_name}/{key}")
        return f"/vsis3/{self.bucket_name}/{key}"


    def aggregate_polygon(self, polygon_geojson: Dict, max_depth: int = 0) -> float:
        """
        Placeholder aggregator entry point — we will replace all Rasterio code
        with a full GDAL implementation next.
        """
        self.max_depth = max_depth
        self.polygon = shape(polygon_geojson)
        

        total = 0.0
        for key in self.tile_keys:
            url = self._build_url(key)
            ds = self._open_tile(url)

            print("Opened COG:", url, ds.RasterXSize, ds.RasterYSize)


        return total
    
    def _world_to_pixel(self, gt, x, y):
        """
        Convert geographic coordinates (x, y) into pixel offsets.
        gt = ds.GetGeoTransform()
        """
        px = int((x - gt[0]) / gt[1])
        py = int((y - gt[3]) / gt[5])  # note: gt[5] is negative
        return px, py
    
    def _bbox_to_window(self, gt, bbox):
        """
        Convert a rectangular bounding box into pixel coodinates

        """
        xmin, ymin, xmax, ymax = bbox

        xoff, yoff = self._world_to_pixel(gt, xmin, ymax)
        xend, yend = self._world_to_pixel(gt, xmax, ymin)

        xsize = max(0, xend - xoff)
        ysize = max(0, yend - yoff)

        return xoff, yoff, xsize, ysize
    
    def _read_data_gdal(self, ds, depth, bbox):
        """
        Read a region of a GDAL COG at a specific quadtree depth.

        depth = 0 → full resolution
        depth >= 1 → overview index depth-1
        """
        band = ds.GetRasterBand(1)

        # Select band (full res or overview)
        if depth == 0:
            target_band = band
            target_gt = ds.GetGeoTransform()
        else:
            idx = depth - 1
            ovr = band.GetOverview(idx)
            if ovr is None:
                raise RuntimeError(f"Overview {idx} missing for depth {depth}")
            target_band = ovr
            target_gt = ovr.GetDataset().GetGeoTransform()

        # Convert bbox -> pixel window
        xoff, yoff, xsize, ysize = self._bbox_to_window(target_gt, bbox)

        if xsize <= 0 or ysize <= 0:
            return np.zeros((1, 1), dtype=np.float32)

        arr = target_band.ReadAsArray(xoff, yoff, xsize, ysize)

        if arr is None:
            return np.zeros((1, 1), dtype=np.float32)

        return np.array(arr, dtype=np.float32)
    
def test_GDAL_Cloudfare():

    print("=== Testing GDAL Cloudflare R2 COG Access ===")
hasattr
    agg = COGAggregatorGDAL()

    # Pick the first generated tile for testing
    test_key = agg.tile_keys[0]
    print(f"\n[Test] Using tile key: {test_key}")

    url = agg._build_url(test_key)

    print(f"[Test] Opening URL: {url}")
    ds = gdal.Open(url)

    if ds is None:
        raise RuntimeError("GDAL could not open the test tile. Check credentials or endpoint configuration.")

    print("[Test] OPEN SUCCESS")
    print("  Raster Size:", ds.RasterXSize, "x", ds.RasterYSize)
    print("  Projection :", ds.GetProjection())
    print("  GeoTransform:", ds.GetGeoTransform())

    # Compute a tiny center bounding box (1-degree box)
    gt = ds.GetGeoTransform()
    center_x = gt[0] + ds.RasterXSize * gt[1] / 2
    center_y = gt[3] + ds.RasterYSize * gt[5] / 2  # gt[5] is negative

    test_bbox = (
        center_x - 0.01,
        center_y - 0.01,
        center_x + 0.01,
        center_y + 0.01
    )

    print("\n[Test] Reading full resolution data at bbox:", test_bbox)
    data = agg._read_data_gdal(ds, depth=0, bbox=test_bbox)
    print("  Full-res read shape:", data.shape)
    print("  Full-res sample values:", data[:5, :5])

    print("\n[Test] Trying overview read at depth=1")
    try:
        data_ovr = agg._read_data_gdal(ds, depth=1, bbox=test_bbox)
        print("  Overview read shape:", data_ovr.shape)
        print("  Overview sample values:", data_ovr[:5, :5])
    except Exception as e:
        print("  Overview read failed:", e)

    print("\n[Test] Trying overview read at depth=4")
    try:
        data_ovr = agg._read_data_gdal(ds, depth=4, bbox=test_bbox)
        print("  Overview read shape:", data_ovr.shape)
        print("  Overview sample values:", data_ovr[:5, :5])
    except Exception as e:
        print("  Overview read failed:", e)

        print("\n[Test] Trying overview read at depth=12")
    try:
        data_ovr = agg._read_data_gdal(ds, depth=12, bbox=test_bbox)
        print("  Overview read shape:", data_ovr.shape)
        print("  Overview sample values:", data_ovr[:5, :5])
    except Exception as e:
        print("  Overview read failed:", e)


    print("\n=== Debug test complete ===")

if __name__ == "__main__":
    test_GDAL_Cloudfare()
