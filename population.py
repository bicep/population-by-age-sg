import geopandas as gpd
import pandas as pd
import json
from buildings import filter_residential_buildings
from constants import *
from utils import parse_age_range
from shapely.geometry import shape

def aggregate_population_by_subzone_and_age():
    """
    Aggregates population by subzone (SZ) and age range (AG).
    
    Args:
        data (DataFrame): The input population data.
        
    Returns:
        DataFrame: Aggregated population data.
    """
    population_data = pd.read_csv(POPULATION_DATA)
    # Group by SZ and AG, summing up the Pop column
    aggregated_data = (
        population_data.groupby(['PA', 'SZ', 'AG'], as_index=False)['Pop']
        .sum()
    )
    aggregated_data.to_csv("./processed/aggregated_population.csv", index=False)
    return aggregated_data

def allocate_population_to_buildings(residential_with_subzones):
    """
    Distributes population proportionally to buildings based on floor_area for each age bracket.
    Optimized for performance by precomputing population and floor area by subzone and age bracket.
    Retains only necessary columns in the final DataFrame.
    """
    # Precompute total floor area for each subzone
    subzone_areas = residential_with_subzones.groupby('subzone')['floor_area'].sum().to_dict()

    # Allocate population for each building and age bracket
    residential_with_subzones['allocated_population'] = (
        (residential_with_subzones['floor_area'] / residential_with_subzones['subzone'].map(subzone_areas)) *
        residential_with_subzones['population_count']
    ).fillna(0)

    # Select only the necessary columns
    final_columns = [
        'geometry', 'building_type', 'building_levels', 'floor_area', 'PA',
        'subzone', 'age_range', 'allocated_population'
    ]
    
    cleaned_data = residential_with_subzones[final_columns]
    cleaned_data = cleaned_data.rename(columns={'PA': 'planning_area'})
    cleaned_data['planning_area'] = cleaned_data['planning_area'].str.upper()

    return cleaned_data


def generate_population_for_buildings_with_all_age_brackets():
    """
    Generates a GeoJSON with population allocated to residential buildings.
    Adds 'age_range' and 'population_count' properties to the GeoJSON features.
    """
    # Step 1: Filter residential buildings
    residential_buildings = filter_residential_buildings()

    # Step 2: Aggregate population by subzone and age
    aggregated_population = aggregate_population_by_subzone_and_age()

    residential_buildings['subzone'] = residential_buildings['subzone'].str.upper()
    aggregated_population['SZ'] = aggregated_population['SZ'].str.upper()

    # Step 3: Join residential buildings with aggregated population data by subzone
    residential_with_subzones = residential_buildings.merge(
        aggregated_population,
        left_on='subzone',
        right_on='SZ',
        how='inner'
    )

    # Drop the SZ column and rename AG and Pop
    residential_with_subzones = residential_with_subzones.drop(columns=['SZ']).rename(
        columns={
            'AG': 'age_range',
            'Pop': 'population_count'
        }
    )

    # Step 4: Allocate population to buildings
    residential_with_population = allocate_population_to_buildings(residential_with_subzones)

    residential_with_population = residential_with_population.copy()
    if residential_with_population.crs is None:
        # 🟨 Assign a default CRS if not already defined
        residential_with_population.set_crs(OUTPUT_CRS, inplace=True)  # Assuming WGS 84 (EPSG:4326)

    residential_with_population.to_file(POPULATION_ALL_AGES_INTERPOLATED_DATA, driver="GeoJSON")
    print(f"Aggregated GeoJSON saved to {POPULATION_ALL_AGES_INTERPOLATED_DATA}")

def filter_and_aggregate_population_by_age(min_age=65, max_age=None, output_file=POPULATION_ELDERLY_INTERPOLATED_DATA):
    """
    Filters and aggregates population data based on a specified age range.

    Parameters:
    - min_age (int): Minimum age to filter (inclusive).
    - max_age (int or None): Maximum age to filter (inclusive). If None, no upper limit is applied.

    Returns:
    None: Saves the aggregated GeoJSON to a file.
    """
    # Load the GeoJSON file
    with open(POPULATION_ALL_AGES_INTERPOLATED_DATA, 'r') as file:
        geojson = json.load(file)

    filtered_features = []

    # Filter and process features
    for feature in geojson['features']:
        age_range_str = feature['properties'].get('age_range', "")
        try:
            # Parse the age range
            age_start = parse_age_range(age_range_str)
            if age_start >= min_age and (max_age is None or age_start <= max_age):
                filtered_features.append({
                    "geometry": shape(feature['geometry']),
                    "properties": feature['properties']
                })
        except ValueError:
            pass  # Skip features with invalid age ranges

    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(filtered_features)

    # Group and aggregate
    aggregated_gdf = gdf.groupby(
        ['building_levels', 'floor_area', 'planning_area' ,'subzone', 'geometry']
    ).agg({
        'allocated_population': 'sum'  # Sum the allocated population
    }).reset_index()

    # Convert back to GeoDataFrame and set geometry
    aggregated_gdf = gpd.GeoDataFrame(aggregated_gdf, geometry='geometry')

    aggregated_gdf = aggregated_gdf.copy()
    if aggregated_gdf.crs is None:
        aggregated_gdf.set_crs(OUTPUT_CRS, inplace=True)

    # Save compact GeoJSON
    aggregated_gdf.to_file(output_file, driver="GeoJSON")

    print(f"Aggregated GeoJSON saved to {output_file}")

def calculate_elderly_rate():
    """
    Calculate elderly rate and add it to the elderly GeoJSON file.
    
    Args:
        POPULATION_ELDERLY_INTERPOLATED_DATA (str): Path to the elderly GeoJSON file.
        POPULATION_COMBINED_INTERPOLATED_DATA (str): Path to the combined GeoJSON file.
        output_path (str): Path to save the updated GeoJSON file.
    """
    # Load the GeoJSON files
    with open(POPULATION_ELDERLY_INTERPOLATED_DATA, "r") as elderly_file:
        elderly_data = json.load(elderly_file)
    
    with open(POPULATION_COMBINED_INTERPOLATED_DATA, "r") as combined_file:
        combined_data = json.load(combined_file)

    # Ensure features are aligned
    if len(elderly_data["features"]) != len(combined_data["features"]):
        raise ValueError("The number of features in elderly and combined data do not match.")
    
    # Add elderly rate to each feature
    for elderly_feature, combined_feature in zip(elderly_data["features"], combined_data["features"]):
        # Deep equality check for geometries
        if elderly_feature["geometry"] != combined_feature["geometry"]:
            raise ValueError("Mismatch in geometry between elderly and combined data.")
        
        # Calculate elderly rate
        elderly_population = elderly_feature["properties"].get("allocated_population", 0)
        combined_population = combined_feature["properties"].get("allocated_population", 1)  # Avoid division by zero
        elderly_rate = elderly_population / combined_population if combined_population > 0 else 0
        
        # Add elderly rate to the properties
        elderly_feature["properties"]["elderly_rate"] = elderly_rate

    # Convert the updated data to GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(elderly_data["features"])
    
    # Avoid warnings by creating a copy
    gdf = gdf.copy()
    if gdf.crs is None:
        gdf.set_crs(OUTPUT_CRS, inplace=True)
    
    # Save the GeoDataFrame to a new GeoJSON file
    gdf.to_file(POPULATION_ELDERLY_RATE_INTERPOLATED_DATA, driver="GeoJSON")
    print(f"Updated elderly data with rates saved to {POPULATION_ELDERLY_RATE_INTERPOLATED_DATA}")