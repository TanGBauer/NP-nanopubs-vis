import re
import pandas as pd

# ISO 6709 style coordinates, e.g. "+46.575707+14.395198+740"
# latitude, longitude, and an optional altitude (plus an optional "/" at the end)
coordinate_pattern = re.compile(
    r"^([+-]\d+(?:\.\d+)?)([+-]\d+(?:\.\d+)?)([+-]\d+(?:\.\d+)?)?/?$"
)


def parse_coordinates(value):
    """Split '+lat+lng+alt' into three numbers. Returns None for missing parts."""
    if pd.isna(value):
        return None, None, None

    match = coordinate_pattern.match(str(value).strip())
    if match is None:
        print(f"Warning: could not parse coordinates '{value}'")
        return None, None, None

    lat = float(match.group(1))
    lng = float(match.group(2))

    altitude = None
    if match.group(3) is not None:
        altitude = float(match.group(3))

    return lat, lng, altitude


def short_label(value):
    """'moor - A wetland found in ...' -> 'moor'"""
    if pd.isna(value):
        return None
    return str(value).split(" - ", 1)[0].strip()


def extract_date(value):
    """'2026-05-02T12:00:00Z' -> '2026-05-02'"""
    if pd.isna(value):
        return None
    return str(value).split("T")[0]


data = pd.read_csv("sparql-query-sampling.csv")

rows = []

for _, row in data.iterrows():
    lat, lng, altitude = parse_coordinates(row["coordinates"])

    new_row = {
        "np": row["np"],
        "label": row["label"],
        "date": extract_date(row["timepoint"]),
        "timepoint": row["timepoint"],
        "lat": lat,
        "lng": lng,
        "altitude": altitude,
        "ecosystem": row["ecosystem"],
        "ecosystem_label": short_label(row["ecosystem_label"]),
        "ecosystem_description": row["ecosystem_label"],
        "material": row["material"],
        "material_label": short_label(row["material_label"]),
        "material_description": row["material_label"],
        "purpose": row["purpose"],
        "purpose_label": short_label(row["purpose_label"]),
    }
    rows.append(new_row)

formatted = pd.DataFrame(rows)

# rows without coordinates can't be shown on a map
missing = formatted["lat"].isna().sum()
if missing > 0:
    print(f"Warning: {missing} rows have no usable coordinates and will be dropped")
formatted = formatted.dropna(subset=["lat", "lng"])

print(f"{len(formatted)} rows written to data_formatted_sampling.csv")

formatted.to_csv("data_formatted_sampling.csv", index=False)
