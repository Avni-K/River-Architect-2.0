import arcpy
from arcpy.sa import Slope  # example tool

arcpy.CheckOutExtension("Spatial")
arcpy.env.workspace = r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
result = Slope(r"C:\path\to\dem.tif")
result.save(r"C:\path\to\out_slope.tif")
arcpy.CheckInExtension("Spatial")
