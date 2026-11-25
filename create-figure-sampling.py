import folium
import pandas as pd
import branca.colormap as cm

data = pd.read_csv("data_formatted_sampling.csv")

# rows without a biome still get a layer
data["ecosystem_label"] = data["ecosystem_label"].fillna("unknown biome")


# 1. base map 

m = folium.Map(
    location=[data["lat"].mean(), data["lng"].mean()],
    zoom_start=8,
    tiles=None,
)

folium.TileLayer(
    tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    attr="Map data: &copy; OpenStreetMap contributors, SRTM | "
         "Map style: &copy; OpenTopoMap (CC-BY-SA)",
    name="Topographic map",
    max_zoom=17,
).add_to(m)

folium.TileLayer(
    "OpenStreetMap",
    name="Street map",
    show=False,
).add_to(m)


# 2. colour scale for altitude (blue = low, red = high)

colormap = cm.LinearColormap(
    colors=["#2c7bb6", "#ffffbf", "#d7191c"],
    vmin=data["altitude"].min(),
    vmax=data["altitude"].max(),
    caption="Altitude (m)",
)
colormap.add_to(m)


def altitude_colour(altitude):
    """Colour for a marker; grey if the altitude is missing."""
    if pd.isna(altitude):
        return "#999999"
    return colormap(altitude)


# 3. one layer per biome 

biome_layers = {}

for biome in sorted(data["ecosystem_label"].unique()):
    layer = folium.FeatureGroup(name=biome)
    layer.add_to(m)
    biome_layers[biome] = layer


#  4. markers 

for _, row in data.iterrows():

    if pd.isna(row["altitude"]):
        altitude_text = "unknown"
    else:
        altitude_text = f"{int(row['altitude'])} m"

    popup_html = f"""
<b>{row['label']}</b>
<br>
Biome: <a href="{row['ecosystem']}" target="_blank">{row['ecosystem_label']}</a>
<br>
Sample material: <a href="{row['material']}" target="_blank">{row['material_label']}</a>
<br>
Altitude: {altitude_text}
<br>
Sampling date: {row['date']}
<br>
<a href="{row['np']}" target="_blank">See nanopublication ...</a>
"""

    folium.CircleMarker(
        location=[row["lat"], row["lng"]],
        radius=8,
        color="black",
        weight=1,
        fill=True,
        fill_color=altitude_colour(row["altitude"]),
        fill_opacity=0.9,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"{row['ecosystem_label']}, {altitude_text}",
    ).add_to(biome_layers[row["ecosystem_label"]])


# 5. layer switch, zoom to data, save 

folium.LayerControl(collapsed=False).add_to(m)

m.fit_bounds([
    [data["lat"].min(), data["lng"].min()],
    [data["lat"].max(), data["lng"].max()],
])

m.save("map-sampling.html")
print("Map saved as map-sampling.html")
