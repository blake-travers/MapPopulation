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

For each query, the backend selects an appropriate resolution based on both the size and complexity of the shape to balance performance. Each shape's algorithmic uncertainty is calculated to a 95% confidence interval, and displayed for the user to consider.

#### Performance
The default "Fast" aggregation method is designed to return 95% of cases in under half a second - regardless of shape size or complexity. This speed is primarily achieved through both Quadtree-based partitioning of COGs and selective resolution sampling.

If the user requires higher precision, "Exact" mode can be toggled which aims to reduce the algorthmic uncertainty by increasing the depth the aggregator reaches. While shapes in "Exact" mode take an average of ~3 seconds and can take up to 10 seconds to calculate, they reduce the algorithmic uncertainty of the shape to less than 0.1% in almost all cases.

#### Interactive Shapes
Supports multiple shapes at once, each listed in a sidebar with its own colour, label, and details. Users can pan to shapes, delete, and view population metrics for each shape independently.

#### Available Settings & Map Controls
Provides a simple interface for switching between calculation modes, toggling map layers, and more. Ambiguous settings have an icon (i) next to them, allowing users to understand all application features.

<img width="2557" height="1273" alt="image" src="https://github.com/user-attachments/assets/0dbc2baa-b945-4dee-b63c-b342281320e7" />

<img width="2556" height="1272" alt="image" src="https://github.com/user-attachments/assets/9c46b1e9-f6f5-44aa-9641-dbfe5e6e6a80" />



## Methodology
#### Data Formatting
The Original Dataset contains a GeoTIFF at 3 arc second resolution. I have downsampled the base raster to ~6.59 arcseconds (because ~6.59*2^14 = 30 degrees), allowing the construction of 72 different Cloud-Optimised GeoTIFFs (COGs) with the base raster (16384x16382), and 14 overviews ranging from 8192x8192 to 1x1 in pixel size. We use all of these overviews as a method to efficiently store and fetch the data required for each depth of the quadtree algorithm in the population aggregator.

In addition to these 30 degree tiles, two 180 degree tiles have also been constructed to allow large, relatively coarse polygons to bypass the limitation of having to partially open many files. With the threshold being an angular span of 25 degrees, this means that even in the worst case a polygon will only need to open a maximum of 4 tiles, reducing open time from up to 3 seconds to a maxmimum of 250 ms.

#### Population Aggregator

The construction of these COGS in such format allows the backend to efficiently call the desired overview level and calculate the estimated population within.

The general pseudocode for the quadtree recursion is as follows:

1. Compare polygon to geographical bounding box of this pixel
2. If polygon does not intersect pixel, or pixel fully encloses polygon, stop
3. Else, polygon must partially intersect the pixel. and we continue
4. If at max depth (i.e. maximum resolution), calculate proportion of pixel inside polygon and stop
5. Else, we recurse down into this pixel's four children at one overview level / depth lower.

#### Frontend
Frontend here


## Limitations
Limitations here

## Acknowledgements
Generative AI has been used in parts of this project to debug, brainstorm, and 
