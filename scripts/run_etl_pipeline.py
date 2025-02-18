import sys
import argparse

sys.path.insert(0, "/".join(sys.path[0].split("/")[:-1]))

from src.arcgis_client import ARCGIS_Client, projects


def run_all():

    client = ARCGIS_Client()
    client.retrieve_arcgis_gis_projects()

    for project in projects:
        client.create_projects_directories()
        client.querying_projects(project=project)
        client.create_main_folder_directories(project=project)
        for sub_folder in client.sub_folder_list:
            client.querying_sub_folder(project=project, sub_folder=sub_folder)
            client.create_layer_directories(project=project, sub_folder=sub_folder)
            for layer in client.layers_list:
                try:
                    client.downloading_layer(
                        project=project, sub_folder=sub_folder, layer=layer
                    )
                except Exception as e:
                    print(f"Error downloading layer {layer}: {e}")


def run_map_server(project):

    client = ARCGIS_Client()
    client.retrieve_arcgis_gis_projects()

    client.create_projects_directories()
    client.querying_projects(project=project)
    client.create_main_folder_directories(project=project)

    for sub_folder in client.sub_folder_list:
        client.querying_sub_folder(project=project, sub_folder=sub_folder)
        client.create_layer_directories(project=project, sub_folder=sub_folder)
        for layer in client.layers_list:
            try:
                client.downloading_layer(
                    project=project, sub_folder=sub_folder, layer=layer
                )
            except Exception as e:
                print(f"Error downloading layer {layer}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run ARCGIS GIS project scripts."
    )  # --help
    parser.add_argument(
        "--project", type=str, help="Name of the project to run", default=None
    )
    args = parser.parse_args()

    if args.project:
        print(f"Running project: {args.project}")
        run_map_server(project=args.project)
    else:
        print("Running all projects...")
        run_all()
