from buildings import *
from population import *
from constants import *

if __name__ == "__main__":
    # generate_building_with_types()
    generate_population_for_buildings_with_all_age_brackets()
    filter_and_aggregate_population_by_age(min_age=65)
    filter_and_aggregate_population_by_age(min_age=0, output_file=POPULATION_COMBINED_INTERPOLATED_DATA)
    calculate_elderly_rate()