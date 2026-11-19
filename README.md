# Evaluating Sentinel-1 flood extent estimates for the 2023 Deyr flood in Beledweyne, Somalia

Processing scripts, output tables, derived rasters and figures that accompany the manuscript.

## Contents
- `scripts/` Python analysis scripts, numbered in the order in which they were written. Scripts 01 to 09 and 120 to 122 use Google Earth Engine and need an Earth Engine project, which is set by the placeholder `YOUR_EARTH_ENGINE_PROJECT`. All paths are relative to the root of this folder, so run scripts from the root, and place the downloaded inputs in `data/` as described below.
- `tables/` Output tables (CSV and JSON) used in the manuscript and supplementary material. Files starting `revision` and `revision2` hold the checks added in response to reviewers.
- `rasters/` Derived 10 m rasters in EPSG:32638 on one grid with origin 498000 m easting and 560000 m northing. `full_flag_*` are the flag layers after the cluster filter step is applied locally, `full_domain` is the analysed area, `full_lulc` is the land-cover map, `full_perm` is permanent water and `hand_10m` is height above nearest drainage from MERIT Hydro. Files starting `aoi_` are the Earth Engine exports used for the maps.
- `figures/` PNG figures.

## Workflow in 4 steps
1. Build the land-cover map and the water and terrain masks (scripts 06, 07, 09, 33).
2. Calculate the median-filtered backscatter change against the mean of the 9 and 21 October scenes (scripts 03, 04, 07, 09).
3. Apply the VV and VH thresholds with the dark-surface exclusion and the minimum cluster size (scripts 17, 19, 20, 21).
4. Tabulate flagged area by land-cover class and score against UNOSAT (scripts 24, 34, 64 to 70, 121 to 125).

## Inputs not included
Sentinel-1, Sentinel-2, WorldCover, Dynamic World, Global Surface Water, MERIT Hydro, Copernicus DEM, CHIRPS and Open Buildings are read from Earth Engine or from their providers. The UNOSAT product FL20231105SOM is available from https://unosat.org/products/ and is expected under `data/raw/unosat_FL20231105SOM/extracted`.

## Licence
Scripts are released under the MIT licence (see LICENSE). Tables, rasters and figures may be reused with attribution (CC BY 4.0).
