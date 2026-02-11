# River Architect 2.0

River Architect is an open-access, peer-reviewed (Journal SoftwareX) and Python3-based software for the GIS-based planning of habitat enhancing river design features regarding their lifespans, parametric characteristics, optimum placement in the terrain, and ecological benefits. The main graphical user interface (GUI) provides modules for generating lifespan and design maps, terrain modification (terraforming), assessment of digital elevation models (DEM), habitat assets including fish stranding risk, and project cost-benefits.

## Prerequisites
- Windows with **ArcGIS Pro** installed (ArcPy comes from the ArcGIS Pro Python environment).
- PostgreSQL running locally.
- ArcGIS Pro conda env clone named `ra-env.
- GeoTIFF rasters for depth, velocity, DEM, and grain size that share extent and CRS.

## First-time setup
- Double-click `Setup/setup-ra-env` run as Administrator. It prepares the ArcGIS Pro `ra-env` clone.
- Logs are written to `Setup/setup.log`. 
- Double-click `Setup/check-ra-env` to verify the environment.
- Logs are written to `Setup/check.log`.


## Running the app
- Double-click `Setup/Run.bat` (or run from a normal prompt). 
- Logs are written to `Setup/run.log`.

## Modules 
- **View Database:** browse stored conditions, inspect raster paths, delete records, or load one into the main form.
- **Select/Create Condition:** creates or selects condition from database
- **Populate Condition:** Functionality includes, creating bed shear rasters, sheild rasters, depth to water table and creating morphological unit. 
- **Coming Up lifespan, terraforming, ecohydraulic, and project maker modules** 

- Lifespan and Design mapping to estimate feature longevity and required dimensions across flows.
- Morphology (Terraforming) tools for terrain modification and volume assessments.
- Ecohydraulics modules for seasonal habitat area (SHArea), cover effects, stranding risk, and riparian seedling recruitment.
- Project Maker to draft construction plans and cost-benefit tables.
- Console Tools for advanced workflows beyond the GUI.

