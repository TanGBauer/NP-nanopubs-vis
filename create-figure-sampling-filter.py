import json
import math

import folium
import pandas as pd
import branca.colormap as cm

data = pd.read_csv("data_formatted_sampling.csv")
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

folium.LayerControl(collapsed=False).add_to(m)


# 2. colour scale for altitude 

colormap = cm.LinearColormap(
    colors=["#2c7bb6", "#ffffbf", "#d7191c"],
    vmin=data["altitude"].min(),
    vmax=data["altitude"].max(),
    caption="Altitude (m)",
)
colormap.add_to(m)


#  3. prepare one entry per sample for JavaScript
# Python computes colour, popup and tooltip; JavaScript only draws and filters.

samples = []

for _, row in data.iterrows():

    if pd.isna(row["altitude"]):
        altitude = None
        altitude_text = "unknown"
        colour = "#999999"
    else:
        altitude = float(row["altitude"])
        altitude_text = f"{int(altitude)} m"
        colour = colormap(altitude)

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

    samples.append({
        "lat": float(row["lat"]),
        "lng": float(row["lng"]),
        "altitude": altitude,
        "biome": row["ecosystem_label"],
        "date": row["date"],
        "colour": colour,
        "popup": popup_html,
        "tooltip": f"{row['ecosystem_label']}, {altitude_text}",
    })

# slider range, rounded outwards to the nearest 10 m
alt_min = int(math.floor(data["altitude"].min() / 10) * 10)
alt_max = int(math.ceil(data["altitude"].max() / 10) * 10)


#  4. one checkbox per biome 

biome_counts = data["ecosystem_label"].value_counts()

biome_checkboxes = ""

for biome in sorted(biome_counts.index):
    count = biome_counts[biome]
    biome_checkboxes += f"""
  <label style="display: block;">
    <input type="checkbox" class="biome-box" value="{biome}" checked>
    {biome} ({count})
  </label>"""


# 5. the filter panel in html

panel_html = """
<div id="filter-panel" style="
    position: fixed; bottom: 30px; left: 10px; z-index: 1000;
    background: white; padding: 10px 14px; border-radius: 6px;
    box-shadow: 0 1px 5px rgba(0,0,0,0.4);
    font-family: sans-serif; font-size: 13px; width: 260px;
    max-height: 80vh; overflow-y: auto;">

  <b>Filter by altitude</b>
  <br><br>

  Min: <span id="alt-min-label"></span> m
  <input type="range" id="alt-min" style="width: 100%;"
         min="__ALT_MIN__" max="__ALT_MAX__" step="10" value="__ALT_MIN__">

  Max: <span id="alt-max-label"></span> m
  <input type="range" id="alt-max" style="width: 100%;"
         min="__ALT_MIN__" max="__ALT_MAX__" step="10" value="__ALT_MAX__">

  <hr>

  <b>Filter by biome</b>
  <button id="biome-all" style="margin-left: 8px;">All</button>
  <button id="biome-none">None</button>
  <br><br>
  __BIOME_CHECKBOXES__

  <hr>
  <b><span id="sample-count"></span></b>
</div>
"""


# 6. the filter logic - in javascript

filter_js = """
<script>
window.addEventListener("load", function () {

    var map = __MAP_NAME__;
    var samples = __SAMPLES__;
    var markers = [];
    var allMarkerObjects = [];

    // (a) create one marker per sample and remember it
    for (var i = 0; i < samples.length; i++) {
        var sample = samples[i];

        var marker = L.circleMarker([sample.lat, sample.lng], {
            radius: 8,
            color: "black",
            weight: 1,
            fillColor: sample.colour,
            fillOpacity: 0.9
        });
        marker.bindPopup(sample.popup, { maxWidth: 300 });
        marker.bindTooltip(sample.tooltip);
        marker.addTo(map);

        markers.push({ marker: marker, sample: sample });
        allMarkerObjects.push(marker);
    }

    // zoom the map so that all samples are visible
    map.fitBounds(L.featureGroup(allMarkerObjects).getBounds(), { padding: [40, 40] });

    // (b) find the elements in the panel
    var minSlider = document.getElementById("alt-min");
    var maxSlider = document.getElementById("alt-max");
    var minLabel = document.getElementById("alt-min-label");
    var maxLabel = document.getElementById("alt-max-label");
    var countLabel = document.getElementById("sample-count");
    var biomeBoxes = document.getElementsByClassName("biome-box");
    var allButton = document.getElementById("biome-all");
    var noneButton = document.getElementById("biome-none");

    // (c) show only markers that pass ALL filters
    function applyFilter() {

        // --- altitude range ---
        var minAlt = Number(minSlider.value);
        var maxAlt = Number(maxSlider.value);

        if (minAlt > maxAlt) {
            maxSlider.value = minAlt;
            maxAlt = minAlt;
        }

        minLabel.textContent = minAlt;
        maxLabel.textContent = maxAlt;

        // --- which biomes are ticked? ---
        var activeBiomes = [];
        for (var i = 0; i < biomeBoxes.length; i++) {
            if (biomeBoxes[i].checked) {
                activeBiomes.push(biomeBoxes[i].value);
            }
        }

        // --- go through all markers ---
        var visible = 0;

        for (var i = 0; i < markers.length; i++) {
            var sample = markers[i].sample;

            var altitudeOk = (sample.altitude === null) ||
                             (sample.altitude >= minAlt && sample.altitude <= maxAlt);
            var biomeOk = activeBiomes.includes(sample.biome);

            if (altitudeOk && biomeOk) {
                markers[i].marker.addTo(map);
                visible = visible + 1;
            } else {
                map.removeLayer(markers[i].marker);
            }
        }

        countLabel.textContent = visible + " of " + markers.length + " samples shown";
    }

    // (d) run the filter whenever something changes, and once at the start
    minSlider.addEventListener("input", applyFilter);
    maxSlider.addEventListener("input", applyFilter);

    for (var i = 0; i < biomeBoxes.length; i++) {
        biomeBoxes[i].addEventListener("change", applyFilter);
    }

    allButton.addEventListener("click", function () {
        for (var i = 0; i < biomeBoxes.length; i++) {
            biomeBoxes[i].checked = true;
        }
        applyFilter();
    });

    noneButton.addEventListener("click", function () {
        for (var i = 0; i < biomeBoxes.length; i++) {
            biomeBoxes[i].checked = false;
        }
        applyFilter();
    });

    applyFilter();
});
</script>
"""


# 7. fill in the placeholders and add everything to the map

panel_html = panel_html.replace("__ALT_MIN__", str(alt_min))
panel_html = panel_html.replace("__ALT_MAX__", str(alt_max))
panel_html = panel_html.replace("__BIOME_CHECKBOXES__", biome_checkboxes)

filter_js = filter_js.replace("__MAP_NAME__", m.get_name())
filter_js = filter_js.replace("__SAMPLES__", json.dumps(samples))

m.get_root().html.add_child(folium.Element(panel_html))
m.get_root().html.add_child(folium.Element(filter_js))

m.save("map-sampling-filter.html")
print("Map saved as map-sampling-filter.html")
