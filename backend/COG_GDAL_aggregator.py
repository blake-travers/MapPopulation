from osgeo import gdal
from typing import Dict, List
from shapely.geometry import shape  
from shapely.geometry import box
from shapely.geometry import Polygon  
import numpy as np
import time

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
        self.initial_depth = 13

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
        self.tile_bounds = [] 

        print(f"Building Keys for tile_size of {tile_size}")
        print(f'Pixel Size: {(tile_size*3600)/(2**(self.initial_depth+1))}" or {tile_size/(2**(self.initial_depth+1))}°')

        for lon1 in range(-180, 180, tile_size):
            lon2 = lon1 + tile_size

            for lat1 in range(-90, 90, tile_size):
                lat2 = lat1 + tile_size
                
                key = f"tile_([{lon1},{lon2}],[{lat1},{lat2}]).tif"

                # store parsed bounds + key
                self.tile_bounds.append( ((lon1, lat1, lon2, lat2), key) )

                keys.append(key)

        return keys

    def _build_url(self, key: str) -> str:
        """
        Build a GDAL /vsis3/ URL to a COG tile.
        """
        print(f"Building URL /vsis3/{self.bucket_name}/{key}")
        return f"/vsis3/{self.bucket_name}/{key}"
    
    def _open_tile(self, url: str):
        """Open a COG tile via GDAL and return the dataset."""
        ds = gdal.Open(url)
        if ds is None:
            raise RuntimeError(f"GDAL could not open COG: {url}")
        return ds

    def aggregate_polygon(self, polygon_geojson: Dict, max_depth: int = 0) -> float:
        """
        Placeholder aggregator entry point — we will replace all Rasterio code
        with a full GDAL implementation next.
        """
        self.max_depth = max_depth
        self.polygon = shape(polygon_geojson)
        total = 0.0
        pxmin, pymin, pxmax, pymax = self.polygon.bounds
 
        #Determine if Tile intersects with rectangular representation of polygon
        candidate_tiles = []
        for (lon1, lat1, lon2, lat2), key in self.tile_bounds:
            
            if not (pxmax < lon1 or lon2 < pxmin or pymax < lat1 or lat2 < pymin):
                candidate_tiles.append(((lon1, lat1, lon2, lat2), key))

        #Determine if Tile intersects at all with rectangular representation of polygon
        candidate_tiles2 = []
        for (lon1, lat1, lon2, lat2), key in candidate_tiles:
            tile_poly = box(lon1, lat1, lon2, lat2)

            if tile_poly.intersects(self.polygon):
                candidate_tiles2.append(((lon1, lat1, lon2, lat2), key))

        #For all other tiles, start running recursive algorithm
        for (lon1, lat1, lon2, lat2), key in candidate_tiles2:
            t0 = time.time()

            url = self._build_url(key)
            ds = self._open_tile(url)

            t_open = time.time() - t0
            t1 = time.time()

            tile_bbox = (lon1, lat1, lon2, lat2)
            tile_pop = self._process_single_tile(ds, tile_bbox)

            t_proc = time.time() - t1

            total += tile_pop

            print(f"Opened COG: url: {url}, size: ({ds.RasterXSize}x{ds.RasterYSize}). Tile Population added: {tile_pop}")
            print(f"    Open time: {t_open:.4f} sec")
            print(f"    Process time: {t_proc:.4f} sec")

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

        depth = 0  -> full resolution
        depth >= 1 -> overview index depth - 1
        """

        band_full = ds.GetRasterBand(1)
        full_gt = ds.GetGeoTransform()

        if depth == 0:
            # Compute pixel window at FULL resolution
            xoff, yoff, xsize, ysize = self._bbox_to_window(full_gt, bbox)

            if xsize <= 0 or ysize <= 0:
                return np.zeros((1, 1), dtype=np.float32)

            arr = band_full.ReadAsArray(xoff, yoff, xsize, ysize)

            if arr is None:
                return np.zeros((1, 1), dtype=np.float32)

            return np.array(arr, dtype=np.float32)
        
        else:

            #Complexity of this part is due to COG not storing overview Pixel Windows correctly - need to regenerate manually

            ovr_index = depth - 1
            ovr_band = band_full.GetOverview(ovr_index)

            if ovr_band is None:
                raise RuntimeError(f"Overview {ovr_index} missing for depth {depth}")

            # Compute the downsampling factor between full-res and this overview
            factor_x = ds.RasterXSize // ovr_band.XSize
            factor_y = ds.RasterYSize // ovr_band.YSize
            factor = max(factor_x, factor_y)

            # Compute the overview geotransform manually
            ovr_gt = list(full_gt)
            ovr_gt[1] = full_gt[1] * factor       # pixel width grows by scale
            ovr_gt[5] = full_gt[5] * factor       # pixel height grows (negative)

            ovr_gt = tuple(ovr_gt)

            # Compute the window IN OVERVIEW SPACE
            xoff, yoff, xsize, ysize = self._bbox_to_window(ovr_gt, bbox)

            if xsize <= 0 or ysize <= 0:
                return np.zeros((1, 1), dtype=np.float32)

            # Read from the overview band (FAST)
            arr = ovr_band.ReadAsArray(xoff, yoff, xsize, ysize)

            if arr is None:
                return np.zeros((1, 1), dtype=np.float32)

            return np.array(arr, dtype=np.float32)
        
    def _process_single_tile(self, ds, tile_bbox) -> float:
        """
        Process a single tile using quadtrees. Starts by dividing tile into four parts representing the coarsest overview

        tile_bbox: (xmin, ymin, xmax, ymax) of the whole tile in geo coords.
        """

        xmin, ymin, xmax, ymax = tile_bbox

        # Split into 4 quadrants (SW, SE, NW, NE)
        mid_x = (xmin + xmax) / 2.0
        mid_y = (ymin + ymax) / 2.0

        quadrants = [
            (xmin, ymin, mid_x, mid_y),  # SW
            (mid_x, ymin, xmax, mid_y),  # SE
            (xmin, mid_y, mid_x, ymax),  # NW
            (mid_x, mid_y, xmax, ymax),  # NE
        ]

        tile_population = 0.0
        for child_bbox in quadrants:
            tile_population += self._process_quadtree_node(ds=ds, bbox=child_bbox, depth=self.initial_depth)

        return tile_population
    
    def _process_quadtree_node(self, ds, bbox, depth: int) -> float:
        """
        Recursively process a raster region using quadtrees.

        bbox: (xmin, ymin, xmax, ymax) in geographic coordinates.
        depth:
            - controls which overview / resolution is used
            - is decreased as we go deeper
        """
        total = 0.0

        #Convert bounding box into a Shapley polygon
        xmin, ymin, xmax, ymax = bbox
        tile_bounds = Polygon([
            (xmin, ymin),
            (xmin, ymax),
            (xmax, ymax),
            (xmax, ymin),
        ])

        #1. If this node does not intersect the shape
        if not tile_bounds.intersects(self.polygon):
            return 0.0

        #2. If this node is entirely inside the shape
        elif self.polygon.contains(tile_bounds):

            data = self._read_data_gdal(ds, depth, bbox)
            total = float(data[data > 0].sum())
            return total

        #3.If this node is partially inside the shape
        elif depth <= self.max_depth:
            #3.1 If we've reached maximum depth: read data once and weight by intersection proportion
            data = self._read_data_gdal(ds, depth, bbox)
            total = float(data[data > 0].sum())

            intersection_area = tile_bounds.intersection(self.polygon).area
            proportion = intersection_area / tile_bounds.area if tile_bounds.area > 0 else 0.0

            total *= proportion
            return total
        else:
            #3.2 If we've not yet reached maximum depth, recusrively go one resolution deeper
            mid_x = (xmin + xmax) / 2.0
            mid_y = (ymin + ymax) / 2.0

            quadrants = [
                (xmin, ymin, mid_x, mid_y),  # SW
                (mid_x, ymin, xmax, mid_y),  # SE
                (xmin, mid_y, mid_x, ymax),  # NW
                (mid_x, mid_y, xmax, ymax),  # NE
            ]

            for child_bbox in quadrants:
                total += self._process_quadtree_node(ds=ds,bbox=child_bbox,depth=depth - 1)

            return total



def print_stats(name: str, arr: np.ndarray):
    if arr.size == 0:
        print(f"  {name} → EMPTY ARRAY")
        return

    # ignore zeros (consistent with your population masking logic)
    valid = arr[arr > 0]

    if valid.size == 0:
        print(f"  {name} → all zeros")
        return

    print(f"  {name}:")
    print(f"    min:  {valid.min():.4f}")
    print(f"    max:  {valid.max():.4f}")
    print(f"    mean: {valid.mean():.4f}")
    print(f"    shape: {arr.shape}")

def test_GDAL_Cloudfare():

    print("=== Testing GDAL Cloudflare R2 COG Access ===")

    agg = COGAggregatorGDAL()

    # Pick the first generated tile for testing
    test_key = agg.tile_keys[26]
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

    try:
        data_ovr = agg._read_data_gdal(ds, depth=0, bbox=test_bbox)
        print_stats("Overview depth=0", data_ovr)
    except Exception as e:
        print("  Overview read failed:", e)

    print("\n[Test] Trying overview read at depth=1")
    try:
        data_ovr = agg._read_data_gdal(ds, depth=1, bbox=test_bbox)
        print_stats("Overview depth=1", data_ovr)
    except Exception as e:
        print("  Overview read failed:", e)


    print("\n[Test] Trying overview read at depth=4")
    try:
        data_ovr = agg._read_data_gdal(ds, depth=4, bbox=test_bbox)
        print_stats("Overview depth=4", data_ovr)
    except Exception as e:
        print("  Overview read failed:", e)


    print("\n[Test] Trying overview read at depth=12")
    try:
        data_ovr = agg._read_data_gdal(ds, depth=12, bbox=test_bbox)
        print_stats("Overview depth=12", data_ovr)
    except Exception as e:
        print("  Overview read failed:", e)


    print("\n=== Debug test complete ===")

def test_polygons():
    agg = COGAggregatorGDAL()

    example_polygons = [
        ("Small square (Melbourne CBD)", {"type": "Polygon","coordinates":[[[144.955, -37.820],[144.965, -37.820],[144.965, -37.810],[144.955, -37.810],[144.955, -37.820]]]}),
        ("Europe rectangle", {"type": "Polygon","coordinates": [[[10, 50],[20, 50],[20, 55],[10, 55],[10, 50]]]}),
        ("Australia east coast region", {"type": "Polygon","coordinates": [[[149, -36],[151, -36],[153, -34],[153, -32],[151, -30],[149, -33],[149, -36]]]}),
        ("Concave polygon test", {"type": "Polygon","coordinates": [[[0, 0],[4, 0],[4, 4],[2, 2],[0, 4],[0, 0]]]}),
        ("Huge region (EU + Middle East)", {"type": "Polygon","coordinates": [[[-10, 30],[40, 30],[40, 60],[-10, 60],[-10, 30]]]}),
        ("Tiny subpixel polygon", {"type": "Polygon","coordinates": [[[12.0001, 48.0001],[12.0002, 48.0001],[12.0002, 48.0002],[12.0001, 48.0002],[12.0001, 48.0001]]]})
    ]

    print("\n--- Running COG polygon tests ---\n")

    for name, polygon in example_polygons:
        print(f"Testing: {name}")
        
        start = time.time()
        try:
            pop = agg.aggregate_polygon(polygon_geojson=polygon, max_depth=0)

            dt = time.time() - start

            print(f"  Population = {pop:,.2f}")
            print(f"  Time taken = {dt:.4f} seconds\n")

        except Exception as e:
            print(f"  ERROR: {e}\n")

    print("--- All tests completed ---")

if __name__ == "__main__":
    #test_GDAL_Cloudfare()
    test_polygons()
    #debug_one_scenario()
