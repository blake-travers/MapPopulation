from osgeo import gdal
from typing import Dict, List
from shapely.geometry import shape, box, Polygon
from shapely.ops import transform
import numpy as np
import time
import os
import math
#from pyproj import Geod

class COGAggregatorGDAL:
    def __init__(self):
        """
        GDAL-CLI based COG aggregator for AWS Lambda + S3.
        Authentication is handled automatically via IAM Role.
        """

        self.region = "s3.ap-southeast-4.amazonaws.com"
        gdal.UseExceptions()
        gdal.SetConfigOption("GDAL_DISABLE_READDIR_ON_OPEN", "YES")
        gdal.SetConfigOption("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif,.tiff,.ovr")
        gdal.SetConfigOption("AWS_REGION", "ap-southeast-4")
        gdal.SetConfigOption("AWS_S3_ENDPOINT",self.region)


        self.schemes ={
            "small": {
                "bucket": "population-cog20",   # rename later
                "tile_size": 30,
                "tile_bounds": self._generate_grid(30)
            },
            "large": {
                "bucket": "population-cog180",
                "tile_size": 180,
                "tile_bounds": self._generate_grid(180)
            }
        }

    def aggregate_polygon(self, polygon_geojson: Dict, speed: str = "fast") -> float:
        """
        Finds the population inside a specific polygon
        """

        # ---- Create polygon, Calculate Scheme & Depth for said Scheme ----
        self.polygon = shape(polygon_geojson)
        #area_km2 = self._polygon_area_km2()
        pxmin, pymin, pxmax, pymax = self.polygon.bounds
        scheme, self.custom_max_depth = self._calculate_depth_scheme(speed, pxmin, pymin, pxmax, pymax)

        self.bucket_name = scheme["bucket"]
        self.tile_bounds = scheme["tile_bounds"]
        self.tile_size = scheme["tile_size"]
        self.scales = None
        self.max_depth = None

        #print(f"|  Bucket: {self.bucket_name}, Polygon Area: {area_km2:.2f} km²")

        start_time = time.time()
    
        total = 0.0
        self.breadth = 0
        self.num_reads = 0
 
        # ----  Determine if Tile intersects with rectangular representation of polygon at all ----
        candidate_tiles = []
        for (lon1, lat1, lon2, lat2), key in self.tile_bounds:
            
            if not (pxmax < lon1 or lon2 < pxmin or pymax < lat1 or lat2 < pymin):
                candidate_tiles.append(((lon1, lat1, lon2, lat2), key))

        # ---- Determine if Tile intersects at all with rectangular representation of polygon ----
        candidate_tiles2 = []
        for (lon1, lat1, lon2, lat2), key in candidate_tiles:
            tile_poly = box(lon1, lat1, lon2, lat2)

            if tile_poly.intersects(self.polygon):
                candidate_tiles2.append(((lon1, lat1, lon2, lat2), key))

        # ---- For all other tiles, start running recursive algorithm ----
        start_time = time.time()
        for (lon1, lat1, lon2, lat2), key in candidate_tiles2:
            t0 = time.time()

            url = self._build_url(key)
            ds = self._open_tile(url)

            if not self.scales:
                self.scales = self._get_scales(ds)
            if not self.max_depth: #First time
                self.max_depth = ds.GetRasterBand(1).GetOverviewCount()
                self.custom_max_depth = min(self.custom_max_depth, self.max_depth)

            t_open = time.time() - t0
            t1 = time.time()

            tile_bbox = (lon1, lat1, lon2, lat2)
            tile_pop = self._process_quadtree_node(ds=ds, bbox=tile_bbox, depth=0)

            t_proc = time.time() - t1

            total += tile_pop

            print(f"|  Opened COG: url: {url}, size: ({ds.RasterXSize}x{ds.RasterYSize}). Tile Population added: {tile_pop}")
            print(f"|    Open time: {int(t_open * 1000)} ms")
            print(f"|    Process time: {int(t_proc * 1000)} ms")

        print(f"|  Population = {total:,.2f}")
        print(f"|  Breadth = {self.breadth}")
        print(f"|  Number of Reads: {self.num_reads}")
        print(f"|  Time taken = {int((time.time()-start_time) * 1000)} ms\n")

        return total, self.breadth#, area_km2
    

    def _generate_grid(self, tile_size: int):
        """
        Generate all tile keys of the form:
        tile_([lon_min,lon_max],[lat_min,lat_max]).tif

        tile_size must divide 360 (lon) and 180 (lat), e.g. 5, 10, 30.
        """

        if 180 % tile_size != 0:
            raise ValueError(f"Tile size {tile_size}° does not evenly divide the globe.")

        tile_bounds = []

        for lon1 in range(-180, 180, tile_size):
            lon2 = lon1 + tile_size
            for lat1 in range(-90, 90, tile_size):
                lat2 = lat1 + tile_size
                key = f"tile_([{lon1},{lon2}],[{lat1},{lat2}]).tif"
                tile_bounds.append(((lon1, lat1, lon2, lat2), key))

        return tile_bounds

    def _build_url(self, key: str) -> str:
        """
        Build a GDAL /vsis3/ URL to a COG tile.
        """
        #print(f"Building URL /vsis3/{self.bucket_name}/{key}")
        return f"/vsis3/{self.bucket_name}/{key}"
    
    def _open_tile(self, url: str):
        """Open a COG tile via GDAL and return the dataset."""
        ds = gdal.Open(url)
        if ds is None:
            err = gdal.GetLastErrorMsg()
            raise RuntimeError(f"GDAL could not open COG: {url}\n{err}")
        return ds

    def _calculate_depth_scheme(self, speed: str, pxmin, pymin, pxmax, pymax):
        """
        Selects tile scheme AND quadtree depth in a single pass.

        Returns:
            scheme (dict), depth (int)
        """

        angular_span = max(pxmax - pxmin, pymax - pymin)
        perimeter = self.polygon.length

        # ---- Shape complexity ----
        BASE_SPAN = 90.0
        SHAPE_CONSTANT = 0.5

        extra_perimeter = max(0.0, perimeter - 4 * angular_span)

        complexity_span = angular_span + SHAPE_CONSTANT * extra_perimeter
        complexity = math.log(complexity_span / BASE_SPAN, 4)

        # ---- Simple Scheme selection Heuristic ----
        if angular_span > 40 or complexity_span > 180:
            scheme = self.schemes["large"]
        else:
            scheme = self.schemes["small"]

        # ---- Depth Speed selection ----
        if speed == "fast":
            base_depth = 5
        else:
            base_depth = 9

        if scheme["tile_size"] == 180: # Account for scheme type
            base_depth += 2 #This is not 1:1 though... COG30 depth 0 = 30, COG180 depth 2 = 45.

        depth = int(round(base_depth - complexity))
        depth = max(3, depth)

        print(
            f"|  Span={angular_span:.2f}°, "
            f"Perimeter={perimeter:.2f}, "
            f"Complexity={complexity:.2f}, "
            f"Scheme={scheme['tile_size']}°, "
            f"Depth={depth}"
        )

        return scheme, depth
    
    def _world_to_pixel(self, gt, x, y):
        """
        Convert geographic coordinates (x, y) into pixel offsets.
        gt = ds.GetGeoTransform()
        """
        px = math.floor((x - gt[0]) / gt[1])
        py = math.floor((y - gt[3]) / gt[5])
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
    
    def _get_scales(self, ds):
        """
        Read and cache PYRAMID_SCALES metadata from the first band.
        Returns a list of floats or None if not present.
        """

        band = ds.GetRasterBand(1)
        scale_str = band.GetMetadataItem("PYRAMID_SCALES")
        if scale_str is None:
            return None
        return list(map(float, scale_str.split(",")))

    
    def _read_data_gdal(self, ds, depth, bbox):
        """
        Read a region of a GDAL COG at a specific quadtree depth.

        depth of 14 -> full resolution
        depth of 13 -> overview index 0
        ...
        depth of 0  -> overview index 13
        
        """
        self.num_reads += 1
        band_full = ds.GetRasterBand(1)
        full_gt = ds.GetGeoTransform()

        if self.max_depth != band_full.GetOverviewCount():
            print(self.max_depth)
            raise RuntimeError(f"Maximum Depth is not equal to total number of Overviews")

        if depth == self.max_depth:
            # Compute pixel window at FULL resolution
            xoff, yoff, xsize, ysize = self._bbox_to_window(full_gt, bbox)

            if xsize <= 0 or ysize <= 0:
                return np.zeros((1, 1), dtype=np.float32)

            arr = band_full.ReadAsArray(xoff, yoff, xsize, ysize)

            if arr is None:
                return np.zeros((1, 1), dtype=np.float32)
            
            arr /= self.scales[0]

            return np.array(arr, dtype=np.float32)
        
        else:

            #Complexity of this part is due to COG not storing overview Pixel Windows correctly - need to regenerate manually

            ovr_index = (self.max_depth - 1) - depth
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

            arr = ovr_band.ReadAsArray(xoff, yoff, xsize, ysize)

            if arr is None:
                return np.zeros((1, 1), dtype=np.float32)
            
            #Divide by scales to get final populationa array
            arr /= self.scales[ovr_index+1]

            return np.array(arr, dtype=np.float32)
        
    
    def _process_quadtree_node(self, ds, bbox, depth: int) -> float:
        """
        Recursively process a raster region using quadtrees.

        bbox: (xmin, ymin, xmax, ymax) in geographic coordinates.
        depth:
            - controls which overview / resolution is used
            - is increased as we go deeper.
        """
        total = 0.0
        self.breadth += 1
        xmin, ymin, xmax, ymax = bbox

        #Convert bounding box into a Shapley polygon
        tile_bounds = Polygon([
            (xmin, ymin),
            (xmin, ymax),
            (xmax, ymax),
            (xmax, ymin),
        ])

        #1. If this node does not intersect the shape
        if not self.polygon.intersects(tile_bounds):
            return 0.0

        #2. If this node is entirely inside the shape
        elif self.polygon.contains(tile_bounds):

            data = self._read_data_gdal(ds, depth, bbox)
            total = float(np.sum(data, where=(data > 0)))
            return total

        #3.If this node is partially inside the shape
        elif depth >= self.custom_max_depth:
            #3.1 If we've reached maximum custom depth: read data once and weight by intersection proportion
            data = self._read_data_gdal(ds, depth, bbox)
            total = float(np.sum(data, where=(data > 0)))

            intersection_area = tile_bounds.intersection(self.polygon).area
            proportion = intersection_area / tile_bounds.area if tile_bounds.area > 0 else 0.0

            return total * proportion
            
        else:
            """ Cut for now.. need raster populated vs non populated for easier reads
            if self.custom_max_depth - depth >= 3:
                #3.2 We want to first check to ensure that the tile is not completely empty (ocean etc), which would defeat the purpose of recursion.
                #However, we only want to do this if our remaining depth is large - thus preventing at this moment a minimum of 4^3 = 64 unnesecary calls
                data = self._read_data_gdal(ds, depth, bbox)
                if np.sum(data) == 0:
                    return 0.0
            """

            #4 And if all these checks fails - it means we are partially inside a tile and thus we need to recursively go one level deeper

            mid_x = (xmin + xmax) / 2.0
            mid_y = (ymin + ymax) / 2.0

            quadrants = [
                (xmin, ymin, mid_x, mid_y),  # SW
                (mid_x, ymin, xmax, mid_y),  # SE
                (xmin, mid_y, mid_x, ymax),  # NW
                (mid_x, mid_y, xmax, ymax),  # NE
            ]

            for child_bbox in quadrants:
                total += self._process_quadtree_node(ds=ds,bbox=child_bbox,depth=depth + 1)

            return total
            
    """
    def _polygon_area_km2(self) -> float:


        EARTH_AREA_KM2 = 510_072_000.0
        GEOD = Geod(ellps="WGS84")

        lon, lat = self.polygon.exterior.coords.xy

        # Signed geodesic area (m²)
        area_m2, _ = GEOD.polygon_area_perimeter(lon, lat)
        area_km2 = abs(area_m2) / 1_000_000.0


        if area_km2 > 0.5 * EARTH_AREA_KM2:
            area_km2 = EARTH_AREA_KM2 - area_km2

        return area_km2
    """


def test_polygons():
    agg = COGAggregatorGDAL()

    example_polygons = [
        ("Small square (Melbourne CBD)", {"type": "Polygon","coordinates":[[[144.955, -37.820],[144.965, -37.820],[144.965, -37.810],[144.955, -37.810],[144.955, -37.820]]]}, "fast"),
        ("Small square (Melbourne CBD)", {"type": "Polygon","coordinates":[[[144.955, -37.820],[144.965, -37.820],[144.965, -37.810],[144.955, -37.810],[144.955, -37.820]]]}, "fast"),
        ("Europe rectangle", {"type": "Polygon","coordinates": [[[10, 50],[20, 50],[20, 55],[10, 55],[10, 50]]]}, "fast"),
        ("Australia east coast region", {"type": "Polygon","coordinates": [[[149, -36],[151, -36],[153, -34],[153, -32],[151, -30],[149, -33],[149, -36]]]}, "fast"),
        ("Australia east coast region", {"type": "Polygon","coordinates": [[[149, -36],[151, -36],[153, -34],[153, -32],[151, -30],[149, -33],[149, -36]]]}, "exact"),
        ("Huge region (EU + Middle East)", {"type": "Polygon","coordinates": [[[-10, 30],[40, 30],[40, 60],[-10, 60],[-10, 30]]]}, "fast"),
        ("Huge region (EU + Middle East)", {"type": "Polygon","coordinates": [[[-10, 30],[40, 30],[40, 60],[-10, 60],[-10, 30]]]}, "exact"),
        ("Gigantic region", {"type": "Polygon","coordinates": [[[-170, -81],[171, -80],[169, 82],[-175, 77]]]}, "fast")
    ]

    print("\n--- Running COG polygon tests ---\n")

    results = []

    for name, polygon, depth in example_polygons:
        print(f"Testing: {name} at depth {depth}")
        
        start = time.time()
        try:
            pop, breadth = agg.aggregate_polygon(polygon_geojson=polygon, speed = depth)

            dt = time.time() - start


            results.append({
                "name": name,
                "population": pop,
                #"area_km2": area,
                "time": dt,
                "depth": depth
            })

        except Exception as e:
            print(f"  ERROR: {e}\n")

            results.append({
                "name": name,
                "population": None,
                #"area_km2": None,
                "depth": depth,
                "status": "error",
                "error": str(e)
            })

    #print("--- All tests completed ---")
    return results

if __name__ == "__main__":
    #test_GDAL_Cloudfare()
    results = test_polygons()
    print(results)

#177362732032.dkr.ecr.ap-southeast-4.amazonaws.com/gdal-lambda