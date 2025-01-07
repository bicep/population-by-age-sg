# High-Level Approach for Population and Building Data Processing

This pipeline focuses on processing population data and integrating it with building data to derive elderly rate.

---

### 1. **Spatial join OSM Building with subzone data + calculate floor area data.**
### 2. **Filter out only residential buildings**
### 3. **sum up population count (divided into 5 year age ranges) by subzone (data from singapore statistics department)**
Population count for a given 5 year age range for each subzone `P_ar_sz`
### 4. **Spatial join residential building data from 2 and population count data from 3 using subzone as common column (there are some differences in subzones here due zoning updates)**
Each residential building in particular subzone will have the population count in that subzone for all 5 year age ranges `P_ar_sz` associated with it
eg
| **Building Name** | **Subzone**      | **Age Range** | **total population in that subzone for that age range, or P_ar_sz** |
|--------------------|------------------|---------------|----------------|
| Property 1         | HOLLAND ROAD    | 0-4           | 460            |
| Property 2         | HOLLAND ROAD    | 5-9           | 880            |
| Property 3         | HOLLAND ROAD    | 10-14           | 810            |
### 5. **Get allocated_population from following equation:**
allocated_population for building at 5 year age range = `P_ar_sz` * (`floor area for building`) / (`total floor area for all buildings in subzone`)**