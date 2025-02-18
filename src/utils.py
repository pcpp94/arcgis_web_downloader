import pandas as pd
import numpy as np
import ast
from shapely.geometry import Polygon, Point, LineString


# Function to create a Point from x and y
def create_point(row):
    if pd.isna(row['geometry.x']):
        return np.nan
    if pd.isna(row['geometry.y']):
        return np.nan
    return Point(row['geometry.x'], row['geometry.y'])

# Function to convert the string to a shapely Polygon
def create_polygon_from_string(coord_string):
    if coord_string is None or (isinstance(coord_string, float) and pd.isnull(coord_string)):
        return np.nan
    if isinstance(coord_string, list):
        if len(coord_string) == 0:  # Check if the evaluated result is empty
            return np.nan
        coordinates = coord_string[0]
        polygon = Polygon(coordinates)   
    else:
        eval_result = ast.literal_eval(coord_string)
        if len(eval_result) == 0:  # Check if the evaluated result is empty
            return np.nan
        coordinates = eval_result[0]
        polygon = Polygon(coordinates)
    return polygon

def create_linestring_from_string(coord_string):
    if coord_string is None or (isinstance(coord_string, float) and pd.isnull(coord_string)):
        return np.nan
    if isinstance(coord_string, list):
        if len(coord_string) == 0:  # Check if the evaluated result is empty
            return np.nan
        coordinates = coord_string[0]
        line = LineString(coordinates)   
    else:
        eval_result = ast.literal_eval(coord_string)
        if len(eval_result) == 0:  # Check if the evaluated result is empty
            return np.nan
        coordinates = eval_result[0]
        line = LineString(coordinates)
    return line


def assigning_geometry(df):

    if ('geometry.rings' in df.columns):
        df['geometry'] = df['geometry.rings'].apply(create_polygon_from_string)
        indices = df[~df['geometry.rings'].isna()].index
        df.loc[indices,'geometry.rings'] = df.loc[indices,'geometry.rings'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        df = df.rename(columns={'geometry.rings' : 'rings'})

    if ('geometry.paths' in df.columns):
        df['geometry'] = df['geometry.paths'].apply(create_linestring_from_string)
        indices = df[~df['geometry.paths'].isna()].index
        df.loc[indices,'geometry.paths'] = df.loc[indices,'geometry.paths'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        df = df.rename(columns={'geometry.paths' : 'paths'})

    if (('geometry.x' in df.columns) and ('geometry.y' in df.columns)):
        df['geometry'] = df.apply(create_point, axis=1)
        df = df.rename(columns={'geometry.x' : 'x' , 'geometry.y' : 'y'})
    
    return df
