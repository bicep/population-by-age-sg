import re

def extract_landuse(description):
    """
    Extract land use information from the Description field.
    """
    match = re.search(r"<th>LU_DESC<\/th>\s*<td>([^<]+)<\/td>", description)
    return match.group(1).strip() if match else None

def parse_age_range(age_range):
    """
    Parse the age_range string and return the lower bound of the range as an integer.
    Handles formats like '40_to_44' and '90_and_over'.
    """
    if "to" in age_range:
        # 🟨 Split on 'to' and return the first number
        return int(age_range.split("_to_")[0])
    elif "and_over" in age_range:
        # 🟨 Extract the number before 'and_over'
        return int(age_range.split("_and_over")[0])
    return 0  # Default if the format is unrecognized
