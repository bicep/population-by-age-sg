# High-Level Approach for Population and Building Data Processing

This pipeline focuses on processing population data and integrating it with building data to derive elderly rate.

---

### 1. **Prepare Building Geojson Dataset: Spatial join OSM Building with subzone data + calculate floor area data.**
- Calculate the floor area of the buildings (building_level * polygon_area_from_coordinates)
- Spatial join OSM Buildings geojson with subzone geojson- each building has its associated subzone
- Spatial join OSM buildings geojson with landuse layer geojson - each building has its associated building type (residential/commercial/etc...)

| **building_type** | **building_levels** | **floor_area**       | **subzone**        | **geometry**          |
|--------------------|---------------------|-----------------------|---------------------|------------------------|
| residential        | 10.0               | 25680.54998362458     | holland road       | polygon coordinates    |
| business 2         | 4.0                | 6646.7549249990434    | northland          | polygon coordinates    |
| residential        | 1.0                | 205.78635889348112    | sembawang east     | polygon coordinates    |
| residential        | 16.0               | 19367.436393773427    | pasir ris west     | polygon coordinates    |

- Filter out only residential building polygons and associated subzones
### 2. **Prepare total population count per age bracket per subzone**
- Population count dataset from singapore department of statistics has scattered population count entries for given age bracket in different subzones
- Get total population counts for each given 5 year age range for each subzone. This is `P_ar_sz`
### 3. **Combine building data from 1 and population data from 2**
- Spatial join residential building data from 1 and population count data from 2 using subzone as common column (there are some differences in subzones here due to zoning updates)
- Each residential building in particular subzone will have the population count in that subzone for all 5 year age ranges `P_ar_sz` associated with it
eg

| **Building Name** | **Subzone**      | **Age Range** | **Total Population in Subzone for Age Range (P_ar_sz)** |
|--------------------|------------------|---------------|--------------------------------------------------------|
| Property 1         | HOLLAND ROAD    | 0-4           | 460                                                    |
| Property 2         | HOLLAND ROAD    | 5-9           | 880                                                    |
| Property 3         | HOLLAND ROAD    | 0-4           | 460                                                    |


### 4. **Get allocated_population for each building from following equation:**
- Allocated_population for building at 5 year age range = `P_ar_sz` * (`floor area for building` / `total floor area for all buildings in subzone`)**
- Each building will have 19 entries, one for each age range since there are 19 age ranges

| **Building Name** | **Subzone**      | **Age Range** | **Allocated Population**       |
|--------------------|------------------|---------------|---------------------------------|
| Property 1         | HOLLAND ROAD    | 0-4           | 2.2466340148352275             |
| Property 1         | HOLLAND ROAD    | 5-9           | 4.2979085501195655             |
| Property 1         | HOLLAND ROAD    | 10-14         | 3.9560294609055089             |


### 5. **Get elderly population count or total population count for each building:**
- Sum up the allocated_population for age range 65 and up for elderly
- Sum up the allocated_population for age range 0 and up for total
