import streamlit as st
import numpy as np
import folium
import geopandas as gpd
import itertools
import json

from folium.plugins import Draw
from streamlit_folium import st_folium
from shapely.geometry import Point, Polygon
from folium.plugins import HeatMap



class PopulationMapApp:
    """
    The Main functionality behind both initialising the Streamlit-Folium map, and calculating the population of polygons drawn inside
    
    """
    def __init__(self,
                 lat_middle = -37.8136,
                 lon_middle = 144.9631,
                 zoom_level = 10,
                 width_px = 850,
                 height_px = 625,
                 input_file = "data/ParquetFiles/melbourne_population_density.parquet"):
        
        self.input_file = input_file
        self.lat_middle = lat_middle
        self.lon_middle = lon_middle
        self.zoom_level = zoom_level
        self.width_px = width_px
        self.height_px = height_px

        if "gdf" not in st.session_state or st.session_state.current_file != self.input_file:
            self.init_session_states()

        self.col1, self.col2 = st.columns([0.75, 0.25])
        self.draw_data = None

        with self.col1:
            st.write("Draw a Shape on the Map")
            self.init_map()
            self.draw_data = st_folium(self.m, width=self.width_px, height=self.height_px)
            #st.write(f"Map Dimensions = {self.width_px} x {self.height_px}, Zoom Level = {self.zoom_level}")

        self.update_shapes()
        #self.printHighlightedShape()
        self.printAllShapes()

    def init_session_states(self):
        """
        Initialise all the variables that will be kept throughout the session. This is only done once at the start and when a new map is chosen.
        """
        st.session_state.current_file = self.input_file
        st.session_state.gdf = gpd.read_parquet(self.input_file)

        st.session_state.shape_counter = itertools.count(1)  # Persistent unique shape IDs
        st.session_state.polygon_populations = {}  # {shape_id: population}
        st.session_state.shape_map = {}  # {shape_key: shape_id}

    def init_map(self):
        """
        Initialize the Folium map with draw, edit, and deletion toolls
        """

        self.m = folium.Map(
            location=[self.lat_middle, self.lon_middle],
            zoom_start=self.zoom_level,
            zoom_control=False,
            scrollWheelZoom=False,
            dragging=False,
            doubleClickZoom=False,
            tiles=None)
        
        folium.TileLayer(tiles="CartoDB Positron", name="Minimal", overlay=False, control=False).add_to(self.m)

        draw = Draw(export=True,
            draw_options={
            "polyline": False,
            "marker": False,
            "circle": False,
            "rectangle": False,
            "polygon": True,
            "circlemarker": False
        }, edit_options={"edit": True, "remove": True})
        draw.add_to(self.m)

    def calculate_population(self, polygon):
        """
        Calculate the population of the inside of a given polygon
        """
        minx, miny, maxx, maxy = polygon.bounds #Only check values within the rectangular bounds of the polygon

        bbox_filtered = st.session_state.gdf[ #Make the data rectangle smaller based on the bounds
            (st.session_state.gdf["longitude"] >= minx) &
            (st.session_state.gdf["longitude"] <= maxx) &
            (st.session_state.gdf["latitude"] >= miny) &
            (st.session_state.gdf["latitude"] <= maxy)]
        
        inside_points = bbox_filtered[bbox_filtered.within(polygon)] #Determine points inside the polygon
        return inside_points["population"].sum()
    
    def printAllShapes(self):
        """
        Print the population of every shape in all_data
        """
    
        with self.col2:
            st.subheader("Population of All Shapes")
            for shape_index, pop in st.session_state.polygon_populations.items():
                if shape_index in self.valid_shape_indices:
                    st.write(f"**Shape {shape_index}: Population = {pop}**")

    def printHighlightedShape(self):
        """
        Print the population of the highlighted shape
        """

        with self.col2:
            st.subheader("Highlighted Shape")
            if st.session_state.highlighted_index is not None:
                st.markdown(f"**Shape {st.session_state.highlighted_index+1}: Population = {st.session_state.polygon_populations[self.highlighted_index]}**")
            else:
                st.markdown(f"**No shape Selected. Click on an object to select it. Note that Drawing a new object will unhighlight this shape (WIP)**")


    def update_shapes(self):
        """
        Update the shape population tracking system while preserving shape IDs on deletion.

                if "last_clicked" in self.draw_data and isinstance(self.draw_data["last_clicked"], dict):
            last_clicked_point = Point(self.draw_data["last_clicked"]["lng"], self.draw_data["last_clicked"]["lat"])

            for shape_key, shape_id in st.session_state.shape_map.items():
                polygon = Polygon(shape_key)  # Convert shape_key back to Polygon
                if polygon.contains(last_clicked_point):  
                    st.session_state.highlighted_index = shape_id
                    break
        """

        if not self.draw_data or self.draw_data["all_drawings"] is None:
            return

        shape_map_str = {json.dumps(k): v for k, v in st.session_state.shape_map.items()}
        self.valid_shape_indices = []
        for shape_info in self.draw_data["all_drawings"]:
            shape_key = tuple(tuple(round(coord, 6) for coord in point) for point in shape_info["geometry"]["coordinates"][0]) #Create the shape key

            if json.dumps(shape_key) not in shape_map_str: #If a new shape Note that we are converting everything to string for comparison purpopses
                shape_index = next(st.session_state.shape_counter)

                st.session_state.shape_map[shape_key] = shape_index #Set the shape key and shape index
                st.session_state.polygon_populations[shape_index] = self.calculate_population(Polygon(shape_key)) #Set the shape key and the Population


                self.valid_shape_indices.append(shape_index) #If its a new one then we append the index
            else:
                shape_index = st.session_state.shape_map[shape_key]
                self.valid_shape_indices.append(shape_index)

