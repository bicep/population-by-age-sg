import geopandas as gpd
import pandas as pd
import json
from constants import *
from utils import extract_landuse, parse_age_range
from shapely.geometry import shape

def generate_building_with_types():
    """
    Load and clean OSM buildings and land use datasets.
    
    Parameters:
        osm_path (str): Path to the OSM buildings GeoJSON file.
        landuse_path (str): Path to the land use GeoJSON file.
    
    Returns:
        tuple: Cleaned GeoDataFrames (osm_buildings_cleaned, landuse_layer)
    """

    # Load the datasets
    osm_buildings = gpd.read_file(OSM_PATH)
    landuse_layer = gpd.read_file(LANDUSE_PATH)

    osm_buildings.rename(columns={"building:levels": "building_levels"}, inplace=True)
    landuse_layer["landuse"] = landuse_layer["Description"].apply(extract_landuse)

    # Clean the OSM dataset by dropping rows without building_levels or geometry
    osm_buildings = osm_buildings.dropna(subset=["building_levels", "geometry"])

    # Ensure `building_levels` is numeric (drop invalid entries)
    osm_buildings["building_levels"] = pd.to_numeric(osm_buildings["building_levels"], errors="coerce")
    osm_buildings = osm_buildings.dropna(subset=["building_levels"])
    osm_buildings = osm_buildings[osm_buildings["building_levels"] >= 1]

    # Re-project geometries to EPSG:3414 (Singapore TM) for accurate area calculation
    calculation_crs = "EPSG:3414"  # SVY21 / Singapore TM
    osm_buildings = osm_buildings.to_crs(calculation_crs)
    landuse_layer = landuse_layer.to_crs(calculation_crs)

    # Calculate floor area (geometry area * building levels)
    osm_buildings["floor_area"] = osm_buildings.geometry.area * osm_buildings["building_levels"]

    # Perform spatial join to classify buildings with land use type
    # Use "building_type" to represent land use classification
    osm_with_landuse = gpd.sjoin(osm_buildings, landuse_layer, how="left", predicate="intersects")
    osm_with_landuse["building_type"] = osm_with_landuse["landuse"]  # Adjust this key if necessary

    osm_with_landuse = osm_with_landuse.to_crs(OUTPUT_CRS)

    # Keep only required columns
    osm_filtered = osm_with_landuse[["building_type", "building_levels", "geometry", "floor_area"]]

    final_data = assign_buildings_to_subzones(osm_filtered)

    final_data = final_data.drop(columns=["index_right"])
    final_data.rename(columns={"name": "subzone"}, inplace=True)

    # Save to GeoJSON
    final_data.to_file(BUILDING_DATA, driver="GeoJSON")

    print(f"Processed data saved to {BUILDING_DATA}")

def assign_buildings_to_subzones(residential_gdf):
    """
    Assigns subzones to residential buildings using a spatial join from hardcoded subzone GeoJSON.
    """
    subzones = gpd.read_file(SUBZONE_DATA)
    residential_with_subzones = gpd.sjoin(
        residential_gdf, subzones, how='inner', predicate='intersects'
    )
    return residential_with_subzones

# Function 1: Filter Residential Buildings
def filter_residential_buildings():
    """
    Filters residential buildings from the hardcoded GeoJSON file.
    """
    with open(BUILDING_DATA, 'r') as f:
        geojson_data = json.load(f)
    residential_buildings = [
        feature for feature in geojson_data['features']
        if feature['properties'].get('building_type') == 'RESIDENTIAL'
    ]
    return gpd.GeoDataFrame.from_features(residential_buildings)