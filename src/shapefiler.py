import sys
import os
import shutil
import re
import pandas as pd 
sys.path.insert(0,'\\'.join(sys.path[0].split('\\')[:-1]))
from src.utils import shapefile_categories_mapping, categories_mapping
from src.config import SHAPEFILE_DIR, OUTPUTS_DIR
import json
import geopandas as gpd


def extract_description(value):
    match = re.search(r'[\d,<\s-]+\s+(.*)', value)
    return match.group(1).strip() if match else value


mapping = shapefile_categories_mapping()
mapping['long_filenames'] = mapping['level_2'] + "_" + mapping['filename']

files = mapping['file_path'].unique().tolist()
filenames = mapping['filename'].unique().tolist()
long_filenames = mapping['long_filenames'].unique().tolist()
categories = mapping['level_2'].unique().tolist()


class ARCGIS_Shapefiler:
    def __init__(self):
        self.file = None
        self.files_list = filenames
        self.gdf = None
        self.rasterized = None
        self.raster_data = None
        self.level_2 = None


    def select_arcgis_category(self, level_2):
        """
        Select ARCGIS item.
        long file: {level_2}
        """
        self.level_2 = level_2

        if level_2 not in categories:
            raise Exception(f"File '{level_2}' not found in the categories.")

        if self.level_2 not in os.listdir(SHAPEFILE_DIR):
            os.mkdir(os.path.join(SHAPEFILE_DIR,f"{self.level_2}"))


    def shapefiling(self):

        if self.level_2 is None:
            raise Exception("method .select_arcgis_item() needs to be run first.")

        if self.level_2 == 'Bordes2020':
            
            name = 'pe.gis.vecinospaises_pe_wgs'
            if name not in os.listdir(os.path.join(SHAPEFILE_DIR, self.level_2)):
                os.mkdir(os.path.join(SHAPEFILE_DIR, self.level_2,f"{name}"))

            metadata = mapping[(mapping['level_2'] == self.level_2) & (mapping['file'] == name)].reset_index(drop=True)

            gdf = gpd.rarcgis_file(metadata.loc[0,'file_path'])
            gdf.columns = gdf.columns.str.replace("attributes.", "")
            for loc in gdf['name'].unique():
                gdf[gdf['name'] == loc].to_file(os.path.join(SHAPEFILE_DIR, self.level_2, name, f"{loc.strip()}.shp"), driver="ESRI Shapefile")




        if self.level_2 == 'ProtegidaArea':

            metadata = mapping[(mapping['level_2'] == self.level_2)].reset_index(drop=True)

            for num, row in metadata.iterrows():
                if row['file'] not in os.listdir(os.path.join(SHAPEFILE_DIR, self.level_2)):
                    os.mkdir(os.path.join(SHAPEFILE_DIR, self.level_2,f"{row['file']}"))
                
                gdf = gpd.rarcgis_file(row['file_path'])
                gdf.columns = gdf.columns.str.replace("attributes.", "")
                gdf.dissolve()[['geometry']].to_file(os.path.join(SHAPEFILE_DIR, self.level_2, row['file'], f"{row['file']}.shp"), driver="ESRI Shapefile")




        if self.level_2 == 'AguaSubterranea':

            metadata = mapping[(mapping['level_2'] == self.level_2)].reset_index(drop=True)

            for num, row in metadata.iterrows():
                if row['file'] not in os.listdir(os.path.join(SHAPEFILE_DIR, self.level_2)):
                    os.mkdir(os.path.join(SHAPEFILE_DIR, self.level_2,f"{row['file']}"))

                with open(os.path.join(OUTPUTS_DIR, row['level_1'], row['level_2'], row['level_3'], f"{row['file']}_metadata.json")) as koko:
                    metadata = json.load(koko)
                    legend = pd.json_normalize(metadata['drawingInfo']['renderer']['uniqueValueInfos'])[['value', 'label']]
                    legend = dict(legend.astype({"value": 'int'}).values)
                    descriptions = {key: extract_description(value) for key, value in legend.items()}

                gdf = gpd.rarcgis_file(row['file_path'])
                gdf.columns = gdf.columns.str.replace("attributes.", "")
                gdf['legend'] = gdf['ruleid'].map(legend)
                gdf['name'] = gdf['ruleid'].map(descriptions)
                gdf = gdf.dissolve(by='legend').reset_index()

                for num, row2 in gdf.iterrows():
                    gdf[gdf['name'] == row2['name']].to_file(os.path.join(SHAPEFILE_DIR, self.level_2, row['file'], f"{row2['name']}.shp"), driver="ESRI Shapefile")




        if self.level_2 == 'RecursosMineros':

            metadata = mapping[(mapping['level_2'] == self.level_2)].reset_index(drop=True)

            for num, row in metadata.iterrows():
                if row['file'] not in os.listdir(os.path.join(SHAPEFILE_DIR, self.level_2)):
                    os.mkdir(os.path.join(SHAPEFILE_DIR, self.level_2,f"{row['file']}"))

                with open(os.path.join(OUTPUTS_DIR, row['level_1'], row['level_2'], row['level_3'], f"{row['file']}_metadata.json")) as koko:
                    metadata = json.load(koko)
                    try:
                        legend = pd.json_normalize(metadata['drawingInfo']['renderer']['uniqueValueInfos'])[['value', 'label']]
                        legend = dict(legend.astype({"value": 'int'}).values)
                    except:
                        pass

                    gdf = gpd.rarcgis_file(row['file_path'])
                    gdf.columns = gdf.columns.str.replace("attributes.", "")
                    gdf = gdf.dissolve(by='category').reset_index()

                    for num, row2 in gdf.iterrows():
                        gdf[gdf['category'] == row2['category']].to_file(os.path.join(SHAPEFILE_DIR, self.level_2, row['file'], f"{row2['category']}.shp"), driver="ESRI Shapefile")




        if self.level_2 == 'RecursosAgricultura':

            metadata = mapping[(mapping['level_2'] == self.level_2)].reset_index(drop=True)

            for num, row in metadata.iterrows():
                if row['file'] not in os.listdir(os.path.join(SHAPEFILE_DIR, self.level_2)):
                    os.mkdir(os.path.join(SHAPEFILE_DIR, self.level_2,f"{row['file']}"))

                with open(os.path.join(OUTPUTS_DIR, row['level_1'], row['level_2'], row['level_3'], f"{row['file']}_metadata.json")) as koko:
                    metadata = json.load(koko)
                    try:
                        legend = pd.json_normalize(metadata['drawingInfo']['renderer']['uniqueValueInfos'])[['value', 'label']]
                        legend = dict(legend.astype({"value": 'int'}).values)
                    except:
                        pass

                if row['long_filenames'] in ['RecursosAgricultura_area.geojson']:
                    gdf = gpd.rarcgis_file(row['file_path'])
                    gdf.columns = gdf.columns.str.replace("attributes.", "")
                    gdf['tipo'] = gdf['tipo'].str.replace("/","_").str.replace(" -","")
                    gdf = gdf.dissolve(by='tipo').reset_index()

                    for num, row2 in gdf.iterrows():
                        gdf[gdf['tipo'] == row2['tipo']].to_file(os.path.join(SHAPEFILE_DIR, self.level_2, row['file'], f"{row2['tipo']}.shp"), driver="ESRI Shapefile")




        if self.level_2 == 'MapaHabitat':

            metadata = mapping[(mapping['level_2'] == self.level_2)].reset_index(drop=True)

            for num, row in metadata.iterrows():
                if row['file'] not in os.listdir(os.path.join(SHAPEFILE_DIR, self.level_2)):
                    os.mkdir(os.path.join(SHAPEFILE_DIR, self.level_2,f"{row['file']}"))

                with open(os.path.join(OUTPUTS_DIR, row['level_1'], row['level_2'], row['level_3'], f"{row['file']}_metadata.json")) as koko:
                    metadata = json.load(koko)
                    try:
                        legend = pd.json_normalize(metadata['drawingInfo']['renderer']['uniqueValueInfos'])[['value', 'label']]
                        legend = dict(legend.astype({"value": 'int'}).values)
                    except:
                        pass

                if row['long_filenames'] in ['MapaHabitat_terrestre_habitat.geojson']:
                    gdf = gpd.rarcgis_file(row['file_path'])
                    gdf.columns = gdf.columns.str.replace("attributes.", "")
                    gdf['tipo'] = gdf['tipo'].str.replace(",","").str.replace("(","").str.replace(")","")
                    gdf = gdf.dissolve(by='tipo').reset_index()

                    for num, row2 in gdf.iterrows():
                        gdf[gdf['tipo'] == row2['tipo']].to_file(os.path.join(SHAPEFILE_DIR, self.level_2, row['file'], f"{row2['tipo']}.shp"), driver="ESRI Shapefile")
