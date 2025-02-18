import os
import glob
import json

import geopandas as gpd
import numpy as np
import rasterio
from rasterio import features
from rasterio.enums import MergeAlg
from rasterio.crs import CRS
from rasterio.transform import from_bounds

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.colors import rgb2hex
import plotly.express as px


from .config import RASTER_DIR, OUTPUTS_DIR, MAP_RASTER_DIR
from .utils import raster_categories_mapping, categories_mapping

mapping = categories_mapping()
mapping['long_filenames'] = mapping['level_2'] + "_" + mapping['filename']

files = mapping['file_path'].unique().tolist()
filenames = mapping['filename'].unique().tolist()
long_filenames = mapping['long_filenames'].unique().tolist()


def generate_colors(length):
    # Use matplotlib's colormap to generate distinct colors
    cmap = plt.cm.get_cmap("viridis", length)  # "tab10" or another colormap
    colors = [rgb2hex(cmap(i)) for i in range(length)]
    return colors



class ARCGIS_Rasterize:
    def __init__(self):
        self.file = None
        self.files_list = filenames
        self.gdf = None
        self.rasterized = None
        self.raster_data = None


    def select_arcgis_item(self, long_file):
        """
        Select ARCGIS item.
        long file: {level_2}_{filename}
        """
        if long_file not in long_filenames:
            raise Exception(f"File '{long_file}' not found in the long_filenames.")
        tempo_index = long_filenames.index(long_file)
        self.file = "_".join(".".join(long_file.split(".")[:-1]).split("_")[1:])
        self.file_path = files[tempo_index]
        self.level_2 = ".".join(long_file.split(".")[:-1]).split("_")[0]
        self.gdf = gpd.rarcgis_file(self.file_path)
        self.crs = CRS.from_epsg(self.gdf.crs.to_epsg())


    def getting_vectors_data(self, pixel_size=0.01):
        
        if self.gdf is None:
            raise Exception(f" GeoDataFrames not loaded, run '.select_arcgis_item()'")
        minx, miny, maxx, maxy = self.gdf.total_bounds
        self.pixel_size = pixel_size
        self.width = int((maxx - minx) / pixel_size)
        self.height = int((maxy - miny) / pixel_size)
        self.transform = from_bounds(minx, miny, maxx, maxy, self.width, self.height)                


    def geometry_input_attribute_col_and_legend_col(self, attribute_col, legend_col):

        if self.gdf is None:
            raise Exception(f" GeoDataFrames not loaded, run '.select_arcgis_item()'")
        self.attribute_col = attribute_col
        self.legend_col = legend_col        
        self.geom_value = ((geom,value) for geom, value in zip(self.gdf.geometry, self.gdf[attribute_col]))
        self.category_mapping = dict(self.gdf[[legend_col,attribute_col]].drop_duplicates().values)


    def rasterize_vector(self, all_touched=True, fill_value=0, merge_alg=MergeAlg.replace):

        if (self.gdf is None) or (self.geom_value is None) or (self.transform is None):
            raise Exception(f"Run methods '.getting_vectors_data()' and 'geometry_input_attribute_col_and_legend_col()' before running this method.")           
        
        self.all_touched = all_touched
        self.fill = fill_value
        self.merge_alg = merge_alg
        self.dtype = self.gdf[self.attribute_col].dtype
        rasterized = features.rasterize(self.geom_value,
                                        out_shape = (self.height, self.width),
                                        transform = self.transform,
                                        all_touched = self.all_touched,
                                        fill = self.fill,
                                        merge_alg = self.merge_alg,
                                        dtype = self.dtype)
        self.rasterized = rasterized


    def save_raster_file(self, output_path=None):
        
        if (self.rasterized is None):
            raise Exception(f"'.rasterize_vector()' method has not been run.")           
        if output_path is None:
            self.output_path = os.path.join(RASTER_DIR, f"{self.level_2}_{self.file}.tif")
        else:
            self.output_path = output_path
        # Save the raster to a GeoTIFF file
        with rasterio.open(
            self.output_path,
            "w",
            driver="GTiff",
            height=self.rasterized.shape[0],
            width=self.rasterized.shape[1],
            count=1,  # Single-band raster
            dtype=self.rasterized.dtype,
            crs=self.crs,  # Assign CRS
            transform=self.transform,
        ) as dst:
            dst.write(self.rasterized, 1)
            dst.update_tags(legend=json.dumps(self.category_mapping))

        print(f"Raster {self.file} saved with CRS: {self.crs}")


    def open_raster_with_legend(self, path=None):

        if path is None:
            try:
                path = self.output_path
            except:
                raise Exception("No path given and instance has no self.output_path attribute.")
        with rasterio.open(path) as src:
            self.raster_data = src.rarcgis(1)
            self.metadata = src.tags()
            if "legend" in self.metadata:
                # Parse the legend
                self.legend = json.loads(self.metadata["legend"])
                print("Retrieved legend:", self.legend)
                self.categories = sorted(self.legend.values())
                self.labels = {v: k for k, v in self.legend.items()}


    def plot_raster(self, legend=True):
        
        if self.raster_data is None:
            raise Exception(f"'.open_raster_with_legend()' method has not been run.")  

        num_categories = len(self.categories)
        colors = generate_colors(num_categories)
        cmap = ListedColormap(colors[:len(self.categories)])  # Match number of categories
        norm = BoundaryNorm(self.categories + [max(self.categories) + 1000], cmap.N)

        # Plot the raster
        plt.figure(figsize=(10, 8))
        plt.imshow(self.raster_data, cmap=cmap, interpolation='nearest')
        plt.colorbar(label="Categories")
        plt.title("Rasterized Categories with Legend")

        # Add a custom legend
        custom_legend = [
            plt.Line2D(
                [0], [0],
                marker="o",
                color="w",
                label=f"{self.labels[cat]} ({cat})",
                markersize=10,
                markerfacecolor=cmap(norm(cat))
            )
            for cat in self.categories
        ]
        if legend == True:
          plt.legend(handles=custom_legend, title="Legend", loc="upper left", bbox_to_anchor=(1.3, 1.3), frameon=True)
        plt.show()


    def plotly_raster(self, save=False, show=True):

        category_labels = {cat: self.labels[cat] for cat in self.categories}
        category_map = {cat: self.labels[cat] for cat in self.categories}
        color_scale = px.colors.qualitative.Set3
        category_map = {cat: self.labels[cat] for cat in self.categories}
        hover_text = np.vectorize(lambda val: category_map.get(val, "Unknown"))(self.raster_data)

        fig = px.imshow(
            self.raster_data,
            color_continuous_scale=color_scale,
            title="Rasterized Categories"
        )
        # Customize colorbar labels
        fig.update_layout(
            coloraxis_colorbar=dict(
                title="Categories",
                tickvals=self.categories,
                ticktext=[category_labels[cat] for cat in self.categories]
            )
        )
        # Hide the color bar (color axis)
        fig.update_layout(
            coloraxis_showscale=False  # This removes the color bar
        )
        # Set the category labels for hover text
        fig.update_traces(
            hovertemplate='Category: %{customdata}',
            customdata=hover_text  # Pass the category label array
        )
        # Create a custom legend as annotations
        legend_items = [
            dict(
                x=1.05, y=1 - (i * 0.025),  # Adjust positioning for each category
                xref="paper", yref="paper",
                text=f"<b>{self.labels[cat]}</b> ({cat})",
                showarrow=False,
                font=dict(size=8, color=color_scale[i % len(color_scale)])
            )
            for i, cat in enumerate(self.categories)
        ]
        fig.update_layout(
            annotations=legend_items,
        )
        if save == True:
            fig.write_html(os.path.join(MAP_RASTER_DIR, f"{self.level_2}_{self.file}.html"))
        
        if show == True:
            # Show the plot
            fig.show()