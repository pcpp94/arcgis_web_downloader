import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs')
NOTEBOOKS_DIR = os.path.join(BASE_DIR, 'notebooks')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
RASTER_DIR = os.path.join(BASE_DIR, 'rasters')
MAP_RASTER_DIR = os.path.join(BASE_DIR, 'maps_raster')
SHAPEFILE_DIR = os.path.join(BASE_DIR, 'shapefiles')