# Map Population Application
Draw a Shape on a Map to find out its Population


### Website Link
https://blake-travers.github.io/MapPopulation/


## Overview
Map Population is an interactive tool that allows users to draw any shape on a world map and estimate the total population contained within it.

This tool is optimised to return population calculations in under half a second regardless of region size or shape complexity - made possible through the use of Quadtrees and Cloud-Optimised GeoTIFFs (COGs) in the backend aggregator.

## Features
#### Population, Resolution & Uncertainty
Calculates the total population contained within any user-drawn shape. Supports shapes of all sizes - from suburbs to countries, using detailed global population rasters at up to 6 arc-second (≈200m at equator) resolution.

For each query, the backend selects an appropriate resolution based on both the size and complexity of the shape to balance performance. Each shape's algorithmic uncertainty is calculated to a 95% confidence interval, and displayed for the user to consider.

#### Performance
The default "Fast" aggregation method is designed to return 95% of cases in under half a second - regardless of shape size or complexity. This speed is primarily achieved through both Quadtree-based partitioning of COGs and selective resolution sampling.

If the user requires higher precision, "Exact" mode can be toggled which aims to reduce the algorthmic uncertainty by increasing the depth the aggregator reaches. While shapes in "Exact" mode take an average of ~3 seconds and can take up to 10 seconds to calculate, they reduce the algorithmic uncertainty of the shape to less than 0.1% in almost all cases.

#### Interactive Shapes
Supports multiple shapes at once, each listed in a sidebar with its own colour, label, and details. Users can pan to shapes, delete, and view population metrics for each shape independently.


#### Zero-Setup Web App
This tool runs entirely on a browser, I've aimed to make use as easy as possible, requiring no sign in, and working on all display devices.

#### Available Settings & Map Controls
Provides a simple interface for switching between calculation modes, toggling map layers, and more. Ambiguous settings have an icon (i) next to them, allowing users to understand all application features.

<img width="2557" height="1273" alt="image" src="https://github.com/user-attachments/assets/0dbc2baa-b945-4dee-b63c-b342281320e7" />

<img width="2553" height="1266" alt="image" src="https://github.com/user-attachments/assets/786a73a1-a93e-435b-8c7e-8444a6436759" />


## Methodology
#### Data Formatting
Data Formatting here

#### Population Aggregator
Population Aggregator here

#### Frontend
Frontend here


## Limitations
Limitations here

## Acknowledgements
Achknowledgements here
