import rasterio
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from rasterio.transform import from_origin



class ExtractTif():
    """
    Converts a TIF file into a GeoDataFrame to use. Auto values are for the city of Melbourne

    """
    def __init__(self,
                 input_paths = r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\TifFiles\GHS_2025_pop_density_145_-35_melbourne_canberra.tif",
                 output_path = r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\ParquetFiles\melbourne_population_density.parquet",
                 lat_middle = -37.8136,
                 lon_middle = 144.9631,
                 zoom_level = 10,
                 width_px = 850,
                 height_px = 625,
                 geo_mask = True):
        
        print("Starting Extraction...")
        self.tif_paths = input_paths if isinstance(input_paths, list) else [input_paths]
        self.output_gdf_path = output_path

        #Please note that these are all standardised and can be changed depending on data
        self.arcseconds_to_metres = 30.87  # Latitude conversion factor
        self.grid_resolution = 3  # 3x3 arcseconds
        self.geo_mask = geo_mask

        self.lat_middle = lat_middle
        self.lon_middle = lon_middle

        degrees_per_pixel = 360 / (256 * (2 ** zoom_level))
        self.lon_span = degrees_per_pixel * width_px* 1.1 # Just in case - it cant hurt to get a bit more information
        self.approx_lat_span = degrees_per_pixel * height_px * 1.1

        self.process_files()


    
    def open_file(self, file_path):
        """
        Opens the TIF file and returns metadata related to that.
        """
        with rasterio.open(file_path) as dataset:
            transform = dataset.transform
            nodata = dataset.nodata
            pop_density = dataset.read(1)  # Read first band
            rows, cols = pop_density.shape
        
        print(f"Opened {file_path}. Raster shape: {rows} x {cols}")


        valid_mask = ~np.isnan(pop_density) if nodata is None else (pop_density != nodata)
    
        # Sum up total population from all valid cells
        total_population = np.sum(pop_density[valid_mask])

        print(f"Total Population in file: {total_population:.0f}")

        return transform, nodata, pop_density, rows, cols


    def process_single_file(self, transform, nodata, pop_density, rows, cols):
        """
        Opens a raster file, converts it into lat/lon and applies the geo mask if neccesary
        """

        print(f"Converting into lat/lon & Flattening arrays...")

        grid_row, grid_col = np.meshgrid(range(rows), range(cols), indexing="ij")

        lon, lat = rasterio.transform.xy(transform, grid_row, grid_col)

        lon, lat, pop_density = np.array(lon).flatten(), np.array(lat).flatten(), pop_density.flatten()


        valid_mask = ~np.isnan(pop_density) if nodata is None else (pop_density != nodata)
        lon, lat, pop_density = lon[valid_mask], lat[valid_mask], pop_density[valid_mask]

        print("Applying geographic mask...")
        lon, lat, pop_density = self.apply_geo_mask(lon, lat, pop_density)

        dy = self.grid_resolution * self.arcseconds_to_metres
        dx = dy * np.cos(np.radians(lat))
        area = dx * dy

        # Remove zero-population cells
        pop_density = np.round(pop_density)
        nonzero_mask = pop_density > 0
        return lon[nonzero_mask], lat[nonzero_mask], pop_density[nonzero_mask], area[nonzero_mask]

    def apply_geo_mask(self, lon, lat, pop_density):
        """
        Applies a geographic mask to filter data within a box calculated based on the zoom level. If Bounds exceedes data box, another dataset will be needed to fill that gap.
        """

        lon_min = round(self.lon_middle - self.lon_span / 2, 4)
        lon_max = round(self.lon_middle + self.lon_span / 2, 4)
        lat_min = round(self.lat_middle - self.approx_lat_span / 2, 4)
        lat_max = round(self.lat_middle + self.approx_lat_span / 2, 4)

        print(f"Determined Bounds as {lon_min}, {lon_max}, {lat_min}, {lat_max}")

        if self.geo_mask:
            print("Applying Geographic Mask...")
            mask = (lat_min <= lat) & (lat <= lat_max) & (lon_min <= lon) & (lon <= lon_max)
            return lon[mask], lat[mask], pop_density[mask]
        return lon, lat, pop_density

    def process_files(self):
        """
        Processes one or more TIF files and concatonates the results.
        """
        all_data = []

        for tif_path in self.tif_paths:
            transform, nodata, pop_density, rows, cols = self.open_file(tif_path)
            lon, lat, pop_density, area = self.process_single_file(transform, nodata, pop_density, rows, cols)

            # Convert to GeoDataFrame
            print(f"Creating GeoDataFrame...")
            gdf = gpd.GeoDataFrame(
                {"longitude": lon, "latitude": lat, "population": pop_density},
                geometry=[Point(x, y) for x, y in zip(lon, lat)],
                crs="EPSG:4326"  # WGS 84
            )
            all_data.append(gdf)

        self.gdf = gpd.GeoDataFrame(pd.concat(all_data, ignore_index=True))
        print(f"Merged data from {len(all_data)} file/s.")

        self.gdf.to_parquet(self.output_gdf_path)
        print(f"GeoDataFrame saved as '{self.output_gdf_path}'")

        #print(f"Mean population density: {self.gdf['population'].mean()}")



if __name__ == "__main__":
    cities = {
        "Melbourne": {
            "lat_middle": -37.8136,
            "lon_middle": 144.9631,
            "input_paths": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\TifFiles\GHS_2025_pop_density_145_-35_melbourne_canberra.tif",
            "output_path": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\ParquetFiles\melbourne_population_density.parquet",
            "geo_mask": False
        },
        "Brisbane": {
            "lat_middle": -27.4705,
            "lon_middle": 153.0260,
            "input_paths": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\TifFiles\GHS_2025_pop_density_155_-25_brisbane.tif",
            "output_path": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\ParquetFiles\brisbane_population_density.parquet"
        },
        "Sydney": {
            "lat_middle": -33.8688,
            "lon_middle": 151.1093,
            "input_paths": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\TifFiles\GHS_2025_pop_density_155_-35_sydney.tif",
            "output_path": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\ParquetFiles\sydney_population_density.parquet"
        },
        "Perth": {
            "lat_middle": -31.9514,
            "lon_middle": 115.9617,
            "input_paths": r"C:\Userytfgs\blake\OneDrive\Documents\GitHub\MapPopulation\data\TifFiles\GHS_2025_pop_density_115_-35_perth.tif",
            "output_path": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\ParquetFiles\perth_population_density.parquet"
        },
        "Adelaide": {
            "lat_middle": -34.9285,
            "lon_middle": 138.6007,
            "input_paths": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\TifFiles\GHS_2025_pop_density_135_-35_adelaide.tif",
            "output_path": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\ParquetFiles\adelaide_population_density.parquet"
        },
        "Auckland": {
            "lat_middle": -36.8509,
            "lon_middle": 174.7645,
            "input_paths": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\TifFiles\GHS_2025_pop_density_175_-35_auckland.tif",
            "output_path": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\ParquetFiles\auckland_population_density.parquet"
        },
        "Tokyo": {
            "lat_middle": 35.6764,
            "lon_middle": 139.7300,
            "zoom_level": 9,
            "input_paths": [r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\TifFiles\GHS_2025_pop_density_145_35_easttokyo.tif",
                            r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\TifFiles\GHS_2025_pop_density_135_35_westtokyo_osaka_nagoya.tif"],
            "output_path": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\ParquetFiles\tokyo_population_density.parquet"
        },
        "Osaka": {
            "lat_middle": 34.6937,
            "lon_middle": 135.5023,
            "input_paths": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\TifFiles\GHS_2025_pop_density_135_35_westtokyo_osaka_nagoya.tif",
            "output_path": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\ParquetFiles\osaka_population_density.parquet"
        },
        "Nagoya": {
            "lat_middle": 35.1815,
            "lon_middle": 136.9066,
            "input_paths": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\TifFiles\GHS_2025_pop_density_135_35_westtokyo_osaka_nagoya.tif",
            "output_path": r"C:\Users\blake\OneDrive\Documents\GitHub\MapPopulation\data\ParquetFiles\nagoya_population_density.parquet"
        }
    }

    #for city_params in cities.values():
        #ExtractTif(**city_params)
    ExtractTif(**cities["Osaka"])   
    ExtractTif(**cities["Nagoya"])