import json
import rasterio
from rasterio.session import AWSSession
from rasterio.vrt import WarpedVRT
from rasterio.mask import mask
from shapely.geometry import shape, Polygon
import boto3
from typing import List, Dict, Tuple, Optional


class COGPolygonAggregator:
    """
    Aggregates population (or any raster values) inside a polygon
    from Cloudflare R2-hosted Cloud Optimized GeoTIFFs (COGs).

    Supports progressive resolution refinement:
    - Start at lowest-resolution overview (e.g., 10x10 degree)
    - Descend recursively until desired resolution
    """

    def __init__(self,
                 token_value: str = "5iklW0_uCgqnyqxE1ileSPvhmY6hpoBMoAobdWim",
                 access_key: str = "432716138e0e713176e09d50bb147059",
                 secret_key: str = "e0941d80a20d875e84edc59d53bbf7b62758565879e7ec46f7e8eab4f242b7df",
                 account_id: str = "2d25f237b013343aaf1d21b860116b79",
                 bucket_name: str = "population-cog-5",
                 region: str = "auto",):

        self.token_value = token_value
        self.access_key = access_key
        self.secret_key = secret_key
        self.account_id = account_id
        self.bucket_name = bucket_name
        self.region = region
        self.initial_depth = 12

        self.endpoint = f"https://{self.account_id}.r2.cloudflarestorage.com"

        self.session = AWSSession(boto3.Session(aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key, region_name=self.region,), endpoint_url=self.endpoint)


    def _build_url(self, key: str) -> str:
        """
        Helper: Build URL for a given COG tile
        """
        return f"{self.endpoint}/{self.bucket_name}/{key}"

    def aggregate_polygon(self, polygon_geojson: Dict, tile_keys: List[str], max_depth: int = 0) -> float:
        """
        Takes in a polygon and finds the population within each tile through _process_single_tiles function

        polygon_geojson: Leaflet polygon geometry (GeoJSON)
        tile_keys: list of R2 paths to COG tiles
        max_resolution_level: optional, limit to certain overview levels (0=full res)
        """
        self.max_depth = max_depth

        self.polygon = shape(polygon_geojson)

        total = 0.0
        for tile in tile_keys:
            tile_url = self._build_url(tile)
            tile_total = self._process_single_tile(tile_url)
            total += tile_total

        return total

    
    def _process_single_tile(self, tile_url: str) -> float:
        """
        Process a single tile using quadtrees.

        depth: How fine each is.
        0: Highest resolution (~4.3")
        12: Lowest resolution (5 degrees) (2x2 overview)
        """

        with rasterio.Env(self.session):
            with rasterio.open(tile_url) as src:
                # root = entire tile bbox
                bbox = src.bounds

                #Split into four sections at coarse overview for start - as there is no 1x1 overview. Same as recursion in line 169
                mid_x = (bbox.left + bbox.right) / 2
                mid_y = (bbox.bottom + bbox.top) / 2

                #Find bounds of four relevant quadrants
                quadrants = [
                    # (xmin, ymin, xmax, ymax)
                    rasterio.coords.BoundingBox(bbox.left, bbox.bottom, mid_x, mid_y), #SW
                    rasterio.coords.BoundingBox(mid_x, bbox.bottom, bbox.right, mid_y), #SE
                    rasterio.coords.BoundingBox(bbox.left, mid_y, mid_x, bbox.top), #NW
                    rasterio.coords.BoundingBox(mid_x, mid_y, bbox.right, bbox.top),#NE
                ]

                for child_bbox in quadrants:
                    total += self._process_quadtree_node(src=src, bbox=child_bbox, depth=self.initial_depth)

                return total
            
    def _process_quadtree_node(self, src, bbox, depth):
        """
        Recursively processes a raster region using quadtrees.

        Pseudocode steps:

        1. If the tile-point is mutually exclusive from the shape, terminate
        2. If the tile-point is entirely inside the shape, add and terminate
        3. If the tile-point is somewhat inside the shape:
            3.1 If the tile-point is at maximum depth (i.e. we cannot recurse any further), find the proportion of intersection, add and terminate
            3.2 If the tile-point is not at maximum depth, split into four children and recurse

        src: GDAL COG object link

        bbox: Bounding box representing the tile-point
            window: pixel coordinates of bbox
            tile_bounds: geometric object of the bbox

        """

        tile_bounds = Polygon([
            (bbox.left,  bbox.bottom),
            (bbox.left,  bbox.top),
            (bbox.right, bbox.top),
            (bbox.right, bbox.bottom)
        ])
            
        total = 0.0

        def _read_data(src, depth):
            """
            Helper function to choose overview and read data based upon the current depth

            Assumes that overviews always equals 12, and that all data is valid (TODO)
    
            Depth 12-1: COG Overviews from 2x2 to 4096x4096
            Depth 0: Full resolution at 8192x8192
            
            """
            
            if depth == 0:
                window = rasterio.windows.from_bounds(*bbox, transform=src.transform)
                return src.read(1, window=window, masked=True)
            elif depth <= 12:
                with WarpedVRT(src, overview_level=(depth-1)) as vrt:
                    window = rasterio.windows.from_bounds(*bbox, transform=vrt.transform)
                    return vrt.read(1, window=window, masked=True)
            

        #1. If this tile-point does not intersect the shape
        if not tile_bounds.intersects(self.polygon):

            total = 0.0

        #2. If this tile-point is entirely bounds by the shape
        elif self.polygon.contains(tile_bounds):

            data = _read_data(src, depth)
            
            total = float(data[data > 0].sum())
        
        #3. If this tile-point is partially bounds by the shape
        else:
            #3.1 If this is the highest resolution or the highest we have decided to do, take the proportion of the polygon intersected by the shape
            if depth <= self.max_depth:

                data = _read_data(src, depth)
                total = float(data[data > 0].sum())

                # Compute proportion of area interior
                intersection_area = tile_bounds.intersection(self.polygon).area
                proportion = intersection_area / tile_bounds.area

                total = total * proportion

            #If this is not the maximum depth, recusrively go one resolution deeper
            else:
                
                mid_x = (bbox.left + bbox.right) / 2
                mid_y = (bbox.bottom + bbox.top) / 2

                #Find bounds of four relevant quadrants
                quadrants = [
                    # (xmin, ymin, xmax, ymax)
                    rasterio.coords.BoundingBox(bbox.left, bbox.bottom, mid_x, mid_y), #SW
                    rasterio.coords.BoundingBox(mid_x, bbox.bottom, bbox.right, mid_y), #SE
                    rasterio.coords.BoundingBox(bbox.left, mid_y, mid_x, bbox.top), #NW
                    rasterio.coords.BoundingBox(mid_x, mid_y, bbox.right, bbox.top),#NE
                ]

                for child_bbox in quadrants:
                    total += self._process_quadtree_node(src=src, bbox=child_bbox, depth=depth-1)

        return total