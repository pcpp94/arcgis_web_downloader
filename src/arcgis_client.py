import os
import pandas as pd 
import numpy as np
import logging
import datetime
import re
import json
import requests
from bs4 import BeautifulSoup
import geopandas as gpd

from .config import OUTPUTS_DIR
from .utils import assigning_geometry, ad_hoc_attributes_tweaks
from .decorators import retry
from .logger_config import setup_logger

logger = setup_logger()


projects = []


class ARCGIS_Client:
    '''
    base_url example: "https://minesportal.minem.pe"
    item example: "/server/rest/services"
    '''
    def __init__(self, base_url: str, item: str):
        self.base_url = base_url
        self.item = item
        self.url_1 = f"{base_url}{item}/"
        self.url = None
        self.feature_params = None
        self.to_scrape_1 = None
        self.to_scrape_2 = None
        self.to_scrape_final = None


    def retrieve_arcgis_gis_projects(self):
        """
        This function retrieves the GIS projects from the ARCGIS website.
        """

        response = requests.get(self.url_1)
        soup = BeautifulSoup(response.content, "html.parser")

        links = soup.find_all("a")
        to_scrape_1 = {}
        starting_str = "/server/rest/services/"

        for link in links:
            if link.get("href").startswith(starting_str):
                url_ = link.get("href")
                name_ = link.text
                to_scrape_1[name_] = url_
        
        self.to_scrape_1 = to_scrape_1
        self.project_list = list(to_scrape_1.keys())
        print("Attributes to_scrape_1 and project_list have been created.")
    

    def create_projects_directories(self):
        """
        This function creates directories for each project in the outputs directory.
        """
        if self.to_scrape_1 is None:
            self.retrieve_arcgis_gis_projects()

        for name in self.to_scrape_1.keys():
            if name not in os.listdir(OUTPUTS_DIR):
                os.mkdir(os.path.join(OUTPUTS_DIR,f"{name}"))
                print(f"Created directory for {name}")


    def querying_projects(self, project: str):
        """
        This functions queries the subitems within the chosen directory.

        Args:
            project (str): Project [From self.project_list]
        """

        if self.to_scrape_1 is None:
            self.retrieve_arcgis_gis_projects()
        
        item = self.to_scrape_1[project]
        self.project = project

        self.url = f"https://minesportal.arcgis.pe{item}/"
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, "html.parser")

        links = soup.find_all("a")
        to_scrape_2 = {}
        starting_str = item

        for link in links:
            if link.get("href").startswith(starting_str):
                url_ = link.get("href")
                name_ = link.text
                to_scrape_2[name_] = url_
        
        self.to_scrape_2 = to_scrape_2
        self.sub_folder_list = list(to_scrape_2.keys())
        self.sub_folder_list = [x.split("/")[1] for x in self.sub_folder_list if len(x.split("/")) > 1]
        print("Attributes to_scrape_2 and sub_folder_list have been created.")


    def create_main_folder_directories(self, project: str):
        """
        This function creates directories for each project in the outputs directory.
        """
        if self.to_scrape_1 is None:
            self.retrieve_arcgis_gis_projects()
        if self.to_scrape_2 is None:
            self.querying_projects(project)

        for name in self.sub_folder_list:
            if name not in os.listdir(os.path.join(OUTPUTS_DIR, project)):
                os.mkdir(os.path.join(OUTPUTS_DIR, project, f"{name}"))
                print(f"Created directory for {project}/{name}")


    def querying_sub_folder(self, project: str, sub_folder: str):


        if self.to_scrape_2 is None:
            self.querying_projects(project)

        self.project = project
        self.sub_folder = sub_folder
        item = self.to_scrape_2[f"{project}/{sub_folder}"]

        self.url = f"https://minesportal.arcgis.pe{item}/"
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, "html.parser")

        links = soup.find_all("a")
        to_scrape_3 = {}
        starting_str = item

        for link in links:
            if link.get("href").startswith(starting_str):
                url_ = link.get("href")
                name_ = link.text
                to_scrape_3[name_] = url_
        
        first_bit = "/".join(self.url.split("/")[3:]).rstrip("/")
        pattern =  rf"/{first_bit}/\d+$"
        to_scrape_final = {}

        for name, value in to_scrape_3.items():
            if re.match(pattern, value):
                to_scrape_final[name] = value

        self.to_scrape_final = to_scrape_final
        self.layers_list = list(to_scrape_final.keys())
        print("Attributes to_scrape_3 and layers_list have been created.")


    def create_layer_directories(self, project: str, sub_folder: str):
        
        if self.to_scrape_1 is None:
            self.retrieve_arcgis_gis_projects()
        if self.to_scrape_2 is None:
            self.querying_projects(project)
        if self.to_scrape_final is None:
            self.querying_sub_folder(project, sub_folder)

        for name in self.layers_list:
            if name not in os.listdir(os.path.join(OUTPUTS_DIR, project, sub_folder)):
                os.mkdir(os.path.join(OUTPUTS_DIR, project, sub_folder, f"{name}"))
                print(f"Created directory for {project}/{sub_folder}/{name}")

    @retry(retries=4)
    def downloading_layer(self, project: str, sub_folder: str, layer: str):

        if self.to_scrape_1 is None:
            self.retrieve_arcgis_gis_projects()
        if self.to_scrape_2 is None:
            self.querying_projects(project)
        if self.to_scrape_final is None:
            self.querying_sub_folder(project, sub_folder)
        
        self.querying_item = self.to_scrape_final[layer]
        self.url = f"https://minesportal.arcgis.pe{self.querying_item}/query"
        name_lower = layer.lower().strip().replace(" ","_")
        self.name_lower = name_lower
        self.name = layer

        max_record_count = self.get_metadata_max_records_to_query(self.url)
        if self.name_lower == 'area':
            max_record_count = 100

        self.feature_params = {
            'f': 'json', # Fromat we want.
            'returnGeometry': "true", # We want the coordinates.
            'where': "('1' = '1')", # We want to query everything within the ID we have selected.
            'spatialRel': "esriSpatialRelIntersects",
            'outFields': "*", # All
            'outSR': "4326", # We want the normal coordinates used in the world.
            'resultOffset': 0,  # Starting at the first record
            'resultRecordCount': max_record_count  # Number of records to fetch per request
            }
        
        self.get_request_with_paginating(self.url, self.feature_params)
        self.df = pd.json_normalize(self.all_features)

        with open(os.path.join(OUTPUTS_DIR, project, sub_folder, f"{layer}", f"{name_lower}_fields.json"), "w") as f:
            json.dump(self.fields, f)
        
        self.df.columns = self.df.columns.str.lower()
        self.df = assigning_geometry(self.df)
        #### A function to change the thingies we need.
        self.df = ad_hoc_attributes_tweaks(self.df, name_lower)        
        self.df.to_csv(os.path.join(OUTPUTS_DIR, project, sub_folder, f"{layer}", f"{name_lower}.csv"), index=False)

        to_drop = [x for x in self.df.columns if x in ['rings', 'paths', 'x', 'y']]
        self.gdf = gpd.GeoDataFrame(self.df, geometry='geometry')
        self.gdf = self.gdf.drop(columns=to_drop)
        self.gdf.set_crs(epsg=4326, inplace=True)
        self.gdf = self.gdf.astype({col: str for col in [x for x in self.gdf.select_dtypes('object').columns if 'geometry' not in x]})
        self.gdf.to_file(os.path.join(OUTPUTS_DIR, project, sub_folder, f"{layer}", f"{name_lower}.geojson"), driver='GeoJSON')
        print(f"Saved {project}, {sub_folder}, {layer}, {name_lower}")


    def get_request_with_paginating(self, url, feature_params):

        if self.url is None:
            self.url = url
        if self.feature_params is None:
            self.feature_params = feature_params
        
        self.all_features = []
        self.fields = []

        while True:
            # Make the request
            self.response = requests.get(url, params=self.feature_params)
            data = self.response.json() 
            # Add features to the list
            if 'features' in data:
                self.all_features.extend(data['features'])
                print(f"{datetime.datetime.now().strftime('%H:%M:%S')}: Retrieved {len(data['features'])} features ({self.project}/{self.sub_folder}/{self.name})")
                logger.setLevel(logging.INFO)
                logger.info(f"{datetime.datetime.now().strftime('%H:%M:%S')}: Retrieved {len(data['features'])} features ({self.project}/{self.sub_folder}/{self.name})")
            else:
                break
            # Check if the number of records fetched is less than the limit
            if len(data['features']) < self.feature_params['resultRecordCount']:
                break
            # Update the offset for the next query
            self.feature_params['resultOffset'] += self.feature_params['resultRecordCount']
        # Add fields alias, etc
        if 'fields' in data:
            self.fields = data['fields']
        return self.all_features, self.fields


    def get_metadata_max_records_to_query(self, url_query):

        # Try and get it if stated:
        try:
            response = requests.get("/".join(url_query.split("/")[:-1])+"?f=json").json()
            with open(os.path.join(OUTPUTS_DIR, self.project, self.sub_folder, f"{self.name}", f"{self.name_lower}_metadata.json"), "w") as f:
                json.dump(response, f)
            value = int(response['maxRecordCount'])
        except:
            value = 1000
        return value


    def get_max_records_to_query_option2(self, url_query):

        response = requests.get("/".join(url_query.split("/")[:-1]))
        soup = BeautifulSoup(response.content, "html.parser")

        # Try and get it if stated:
        try:
            for div in soup.find_all("div"):
                if "MaxRecordCount" in div.get_text():
                    text = div.get_text()
                    # Extract the value after 'MaxRecordCount:'
                    start_index = text.find("MaxRecordCount:") + len("MaxRecordCount:")
                    value = text[start_index:].split('<br/>')[0].strip().split("\n")[0]
                    value = int(value)
        except:
            value = 1000
        
        return value
