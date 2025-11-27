from typing import Dict, List
from shapely.geometry import shape, box, Polygon
import numpy as np
import time
import subprocess
import os


class PopulationAggregator:
    """
    Logic behind Population Aggregator
    
    """
    def __init__(self, bucket_name: str = None, tile_size: int = 30, initial_depth: int = 13):
        """
        GDAL-CLI based COG aggregator for AWS Lambda + S3.
        Authentication is handled automatically via IAM Role.
        """

        # ---- AWS CONFIG ----
        self.bucket_name = bucket_name or os.environ.get("COG_BUCKET_NAME", "population-cog20")

        self.region = os.environ.get("AWS_REGION", "ap-southeast-4")

        # ---- CLASS CONFIG ----
        self.initial_depth = initial_depth
        self.tile_size = tile_size

        print("Class Initialisation")
        print(f"  Bucket: {self.bucket_name}")
        print(f"  Region: {self.region}")
        print(f"  Default depth: {self.initial_depth}")

        # Precompute tile bounds + keys
        self._generate_global_tile_keys(tile_size=self.tile_size)


    def _generate_global_tile_keys(self, tile_size: int) -> List[str]:
        """
        Generate all tile keys of the form:
        tile_([lon_min,lon_max],[lat_min,lat_max]).tif

        tile_size must divide 360 (lon) and 180 (lat), e.g. 5, 10, 30.
        """

        if 180 % tile_size != 0:
            raise ValueError(f"Tile size {tile_size}° does not evenly divide the globe.")

        self.tile_keys = []
        self.tile_bounds = [] 

        print(f"Building Keys for tile_size of {tile_size}")
        print(f'Pixel Size: {(tile_size*3600)/(2**(self.initial_depth+1))}" or {tile_size/(2**(self.initial_depth+1))}°')

        for lon1 in range(-180, 180, tile_size):
            lon2 = lon1 + tile_size

            for lat1 in range(-90, 90, tile_size):
                lat2 = lat1 + tile_size
                
                key = f"tile_([{lon1},{lon2}],[{lat1},{lat2}]).tif"

                # store parsed bounds + key
                self.tile_bounds.append( ((lon1, lat1, lon2, lat2), key))

                self.tile_keys.append(key)

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

    def _build_url(self, key: str) -> str:
        return f"/vsis3/{self.bucket_name}/{key}"
    
    def _sum_bbox(self, key: str, bbox, depth: int) -> float:
        raise NotImplementedError

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

            data = self._sum_bbox(ds, depth, bbox)
            total = float(data[data > 0].sum())
            return total

        #3.If this node is partially inside the shape
        elif depth <= self.max_depth:
            #3.1 If we've reached maximum depth: read data once and weight by intersection proportion
            data = self._sum_bbox(ds, depth, bbox)
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