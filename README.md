# Map Population Application
Draw a Shape on a Map to find out its Population

### Website Link
https://blake-travers.github.io/MapPopulation/

## Overview
Map Population is an interactive tool that allows users to draw any shape on a world map and estimate the total population contained within it.

This tool is optimised to return population calculations in under half a second regardless of region size or shape complexity - made possible through the use of Quadtrees and Cloud-Optimised GeoTIFFs (COGs) in the backend aggregator.

## Features
#### Population, Resolution & Uncertainty
MapPopulation calculates the total population contained within any user-drawn shape. Supports shapes of all sizes - from suburbs to countries, using detailed global population rasters at up to 6 arc-second (≈200m at equator) resolution.

For each query, the backend selects an appropriate resolution based on both the size and complexity of the shape to balance performance. Each shape's algorithmic uncertainty is calculated and displayed for the user to consider.

#### Performance
The default "Fast" aggregation method is designed to return 90% of cases in under half a second - regardless of shape size or complexity. This speed is primarily achieved through both Quadtree-based partitioning of COGs and selective resolution sampling.

If the user requires higher precision, "Exact" mode can be toggled which aims to reduce the algorthmic uncertainty by increasing the depth the aggregator reaches. While shapes in "Exact" mode take an average of ~3 seconds and can take up to 10 seconds to calculate, they reduce the algorithmic uncertainty of the shape to less than 0.1% in almost all cases.

#### Interactive Shapes
Supports multiple shapes at once, each listed in a sidebar with its own colour, label, and details. Users can pan to shapes, delete, and view population metrics for each shape independently.

#### Available Settings & Map Controls
Provides a simple interface for switching between calculation modes, toggling map layers, and more. Ambiguous settings have an icon (i) next to them, allowing users to understand all application features.

<img width="2557" height="1273" alt="image" src="https://github.com/user-attachments/assets/0dbc2baa-b945-4dee-b63c-b342281320e7" />

<img width="2556" height="1272" alt="image" src="https://github.com/user-attachments/assets/9c46b1e9-f6f5-44aa-9641-dbfe5e6e6a80" />


## Methodology
#### Data Formatting
The Original Dataset contains a GeoTIFF at 3 arc second resolution. I have downsampled the base raster to ~6.59 arcseconds which allows the construction of 72 Cloud-Optimised GeoTIFFs (COGs). Each raster is of size 16384^2 and spans 30 square degrees across. Each raster contains 14 overviews ranging from 8192x8192 to 1x1 in pixel size, primarily used as a method to efficiently store and fetch the data required for each depth of the quadtree algorithm in the population aggregator.

In addition to these 30 degree tiles, two 180 degree tiles have also been constructed to allow large, relatively coarse polygons to bypass the limitation of having to partially open many files. With the threshold being an angular span of 25 degrees, this means that even in the worst case a polygon will only need to open a maximum of 4 tiles, reducing open time from up to 3 seconds to a maxmimum of 250 ms.

#### Population Aggregation

Population Calculations are performed by a serverless backend hosted in AWS Lambda. Since COGs expose internal overviews, the aggregator can request population values at the appropriate resolution during any point in the quadtree algorithm. This use of quadtrees drastically reduces the arithmetic neccesary for precise computations, and COGs allow the backend to only access overviews & data points as they need.

Population is estimated through a recursive quadtree algorithm. Each "Pixel" in the raster is treated as a node in the quadtree. Aggregation always starts at the coarsest overview level (1x1), and is recursed finer. Simplified pseudocode is as follows:

```text
function process_node(pixel, depth):
    if polygon does not intersect pixel:
        return 0

    elif pixel is fully inside polygon:
        return pixel.population_value

    else, pixel must be partially intersected by polygon:
        if current depth = maximum resolution:
            fraction = proportion of polygon that intersects the pixel
            return pixel.population_value * fraction

        else, we must recurse one level deeper:
            return process_node(child, depth + 1) for each of the four child nodes
```

Maximum "depth" is determined through a combination of metrics, including angular span, shape perimeter, and calculation method. Depth has been fine tuned to average ~250ms for fast mode and ~2000ms for exact mode.

#### Uncertainty Estimates

To ensure calculation transperancy, both the algorithmic and dataset uncertainty have been estimated:
- Algorithmic uncertainty is determined by calculating the ratio of partially intersected nodes to the total number of possible nodes. Through this, and a conservative granularity factor, we can determine the approximate algortihmic uncertainty given for each polygon. Algorithmic uncertainty is the metric shown by default in the frontend.
- Dataset uncertainty is a very coarse estimation of possible variation in the dataset, exclusively based upon the angular span of the polygon aggregated. This value should not be taken verbatim, and only used as a rough guide.

#### Frontend

Frontend is constructed using HTML, CSS & Vanilla Javascript.
Packages used include Leaflet, Leaflet Draw, Leaflet Geometry, and Turf.

#### Limitations

Data used in the aggregator is limited to a "Depth" of 14 (meaning approximately ~200m resolution at the equator). Shapes under 1km^2 are prone to high algorithmic uncertainty.

When a polygon partially overlaps a pixel at maximum resolution (almost always happens), the population is assumed to be uniformly distributed, and the population based on the proportion of polygon inside that pixel is used. While a better estimate than just discounting the pixel entirely, it introduces significant uncertainty into the estimate.

Currently, there is no method of importing / exporting shapes. This is something to consider for future releases.

Upon waking up, the Lambda function takes around 1-2 seconds to warm up the required packages. While measures have been taken to try and minimise the impact this has on calculating population, they aren't universal and you may notice some calculations take an extra second or two if the function is cold.

## Acknowledgements

Generative AI has been used in parts of this project to debug, brainstorm, and refine implementation.

Dataset
Schiavina, Marcello; Freire, Sergio; Alessandra Carioli; MacManus, Kytt (2023): GHS-POP R2023A - GHS population grid multitemporal (1975-2030). European Commission, Joint Research Centre (JRC) [Dataset] doi: 10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE PID: http://data.europa.eu/89h/2ff68a52-5b5b-4a22-8f40-c41da8332cfe

Dataset Methodology
Pesaresi, Martino, Marcello Schiavina, Panagiotis Politis, Sergio Freire, Katarzyna Krasnodębska, Johannes H. Uhl, Alessandra Carioli, et al. (2024). Advances on the Global Human Settlement Layer by Joint Assessment of Earth Observation and Population Survey Data. International Journal of Digital Earth 17 (1). doi:10.1080/17538947.2024.2390454
