import streamlit as st
from generateMap import PopulationMapApp

st.set_page_config(layout="wide")


#Remove top padding, and change sidebar size
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.3rem !important;
    }

    [data-testid="stSidebar"] {
        min-width: 200px !important;  /* Set default width */
        max-width: 200px !important;  /* Lock width to prevent resizing */
    }
    </style>
    """,
    unsafe_allow_html=True
)

MAPS = {
    "Melbourne": {
        "input_file": "data/ParquetFiles/melbourne_population_density.parquet",
        "lat_middle": -37.8136,
        "lon_middle": 144.9631,
    },
    "Perth": {
        "input_file": "data/ParquetFiles/perth_population_density.parquet",
        "lat_middle": -31.9514,
        "lon_middle": 115.9617,
    },
    "Sydney": {
        "input_file": "data/ParquetFiles/sydney_population_density.parquet",
        "lat_middle": -33.8688,
        "lon_middle": 151.1093,
    },
    "Brisbane": {
        "input_file": "data/ParquetFiles/brisbane_population_density.parquet",
        "lat_middle": -27.4705,
        "lon_middle": 153.0260,
    },
    "Adelaide": {
        "input_file": "data/ParquetFiles/adelaide_population_density.parquet",
        "lat_middle": -34.9285,
        "lon_middle": 138.6007,
    },
    "Auckland": {
        "input_file": "data/ParquetFiles/auckland_population_density.parquet",
        "lat_middle": -36.8509,
        "lon_middle": 174.7645,
    },
    "Tokyo": {
        "input_file": "data/ParquetFiles/tokyo_population_density.parquet",
        "zoom_level": 9,
        "lat_middle": 35.6764,
        "lon_middle": 139.7300,
    },
    "Osaka": {
        "input_file": "data/ParquetFiles/osaka_population_density.parquet",
        "lat_middle": 34.6937,
        "lon_middle": 135.5023,
    },
    "Nagoya": {
        "input_file": "data/ParquetFiles/nagoya_population_density.parquet",
        "lat_middle": 35.1815,
        "lon_middle": 136.9066,
    }
}
st.sidebar.header("Select a City:")

selected_city = st.sidebar.radio(label="Select a City:", options=list(MAPS.keys()))

# Display Selected City
st.header(f"Calculate Population of a shape in {selected_city}")

# Initialize Map Application
PopulationMapApp(
    input_file=MAPS[selected_city]["input_file"],
    lat_middle=MAPS[selected_city]["lat_middle"],
    lon_middle=MAPS[selected_city]["lon_middle"],
    zoom_level=MAPS[selected_city].get("zoom_level", 10)
)

st.write(f"Coordinates = ({MAPS[selected_city]['lon_middle']}, {MAPS[selected_city]['lat_middle']})")

st.write("")
st.write("Dataset: Schiavina, Marcello; Freire, Sergio; Alessandra Carioli; MacManus, Kytt (2023): GHS-POP R2023A - GHS population grid multitemporal (1975-2030). European Commission, Joint Research Centre (JRC) [Dataset] doi: 10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE PID: http://data.europa.eu/89h/2ff68a52-5b5b-4a22-8f40-c41da8332cfe")
