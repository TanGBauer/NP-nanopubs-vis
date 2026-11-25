"""
Create a Google Earth (KML) file from the formatted sampling nanopubs.

Input:  data_formatted_sampling.csv   (output of format-input-sampling.py)
Output: map-sampling.kml               (open in Google Earth Pro or Google Earth Web)

- one folder per biome (ecosystem_label) -> tick boxes in Google Earth = biome filter
- point colour by altitude: blue (low) -> red (high)
- each point has a date -> Google Earth Pro shows a time slider
- click a point -> popup with details and link to the nanopub
"""
import pandas as pd
import simplekml

INPUT_CSV = "data_formatted_sampling.csv"
OUTPUT_KML = "map-sampling.kml"

# White circle icon; Google Earth tints it with the colour we set
ICON_URL = "http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"


def altitude_to_rgb(altitude, alt_min, alt_max):
    """Linear colour scale: blue (lowest altitude) -> red (highest altitude)."""
    if pd.isna(altitude):
        return (150, 150, 150)  # grey if altitude is missing
    if alt_max == alt_min:
        t = 0.5
    else:
        t = (altitude - alt_min) / (alt_max - alt_min)
    red = int(255 * t)
    blue = int(255 * (1 - t))
    return (red, 40, blue)


def build_description(row):
    """HTML shown in the popup when clicking a point."""
    lines = []
    lines.append(f"<b>{row['label']}</b><br>")
    lines.append(f"Date: {row['date']}<br>")
    lines.append(f"Altitude: {row['altitude']:.0f} m<br>")
    lines.append(f"Coordinates: {row['lat']:.5f}, {row['lng']:.5f}<br>")
    lines.append(f"Biome: <a href='{row['ecosystem']}'>{row['ecosystem_label']}</a><br>")
    lines.append(f"Material: <a href='{row['material']}'>{row['material_label']}</a><br>")
    lines.append(f"Purpose: {row['purpose_label']}<br><br>")
    lines.append(f"<a href='{row['np']}'>Open nanopublication</a>")
    return "".join(lines)


def main():
    df = pd.read_csv(INPUT_CSV)
    print(f"Read {len(df)} nanopublications from {INPUT_CSV}")

    alt_min = df["altitude"].min()
    alt_max = df["altitude"].max()

    kml = simplekml.Kml(name="Sampling nanopublications")
    kml.document.description = (
        f"{len(df)} sampling nanopublications. "
        f"Colour = altitude, blue = {alt_min:.0f} m, red = {alt_max:.0f} m."
    )

    # Start the view tilted over the centre of the samples (3D perspective)
    kml.document.lookat = simplekml.LookAt(
        latitude=df["lat"].mean(),
        longitude=df["lng"].mean(),
        altitude=0,
        range=40000,   # distance of the camera in metres
        tilt=65,       # 0 = straight down, 90 = horizontal
        heading=0,
        altitudemode=simplekml.AltitudeMode.relativetoground,
    )

    # One folder per biome
    folders = {}
    biomes = sorted(df["ecosystem_label"].dropna().unique())
    for biome in biomes:
        folders[biome] = kml.newfolder(name=biome)

    for i, row in df.iterrows():
        folder = folders[row["ecosystem_label"]]

        point = folder.newpoint(name=row["label"])
        point.coords = [(row["lng"], row["lat"])]   # KML order: longitude, latitude
        point.altitudemode = simplekml.AltitudeMode.clamptoground
        point.timestamp.when = row["date"]
        point.description = build_description(row)

        r, g, b = altitude_to_rgb(row["altitude"], alt_min, alt_max)
        point.style.iconstyle.icon.href = ICON_URL
        point.style.iconstyle.color = simplekml.Color.rgb(r, g, b)
        point.style.iconstyle.scale = 1.2
        point.style.labelstyle.scale = 0   # hide the name label (shown on hover/click)

    kml.save(OUTPUT_KML)
    print(f"Saved {OUTPUT_KML} with {len(biomes)} biome folders")


if __name__ == "__main__":
    main()
