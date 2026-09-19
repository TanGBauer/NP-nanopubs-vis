import folium
import pandas as pd

data = pd.read_csv("data_formatted.csv")

#set up  the basemap 

center_lateral = data["lat"].mean()
center_longitudinal = data["lng"].mean()

m = folium.Map(
    location=[center_lateral, center_longitudinal],
    zoom_start=3
)

# feature group per sample type - actual filtering mechanism

sample_types = data["sampletype_label"].unique()

layers = {}
for stype in sample_types:
    layers[stype] = folium.FeatureGroup(name=stype)


#optional add on -color couding
available_colors = ["blue", "green", "purple", "orange", "red", "darkred",
                     "cadetblue", "darkgreen", "darkblue", "pink"]

color_map = {}
for i, stype in enumerate(sample_types):
    color_map[stype] = available_colors[i]


#add markers to their layer
for _, row in data.iterrows():
    popup_text = f"""
Taxon <i>Planomonospora</i> sp. <a href={row["nucseq"]}>{row["nucseq_id"]}</a>
<br>
Sample type: <a href={row["sampletype"]}>{row["sampletype_label"]}</a>
<br>
Sample date: {row['timepoint'].split('T')[0]}
<br>
<a href={row["np"]}>See details ...</a>
"""
#added color coding here
    marker_color = color_map[row["sampletype_label"]]
    marker = folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=popup_text,
            icon=folium.Icon(color=marker_color)
        )
    marker.add_to(layers[row["sampletype_label"]])

# add toggle

for layer in layers.values():
    layer.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

#save map

m.save("map-interactive.html")

