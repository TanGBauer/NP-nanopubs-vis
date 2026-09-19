import folium
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
from adjustText import adjust_text

def plot_folium_map(df: pd.DataFrame):
    """Create an interactive map with folium"""
    center_lat = df["lat"].mean()
    center_lon = df["lng"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=3
    )
    for _, row in df.iterrows():
        folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=f"""
Taxon <i>Planomonospora</i> sp. <a href={row["nucseq"]}>{row["nucseq_id"]}</a>
<br>
Sample type: <a href={row["sampletype"]}>{row["sampletype_label"]}</a>
<br>
Sample date: {row['timepoint'].split('T')[0]}
<br>
<a href={row["np"]}>See details ...</a>
"""
        ).add_to(m)
    m.save("map.html")

def plot_geopandas_map(df: pd.DataFrame):
    """Plot locations and metadata on static map using geopandas and matplotlib"""
    world = gpd.read_file(
        "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
    )

    gdf = gpd.GeoDataFrame(
        df,
        geometry=[
            Point(lon, lat)
            for lon, lat in zip(df["lng"], df["lat"])
        ],
        crs="EPSG:4326"
    )

    fig, ax = plt.subplots(figsize=(10, 8))

    ax.set_xlim(
        gdf.total_bounds[0] - 8,
        gdf.total_bounds[2] + 8
    )

    ax.set_ylim(
        gdf.total_bounds[1] - 5,
        gdf.total_bounds[3] + 5
    )

    world.plot(
        ax=ax,
        color="lightgrey",
        edgecolor="white"
    )

    label_df = gdf.drop_duplicates(
        subset=['lat', 'lng']
    )

    for sampletype, subset in label_df.groupby("sampletype_label"):
        subset.plot(
            ax=ax,
            markersize=30,
            label=sampletype,
            edgecolors = "white",
        )

    ax.legend(title="Sample Type")

    texts = []
    for idx, row in label_df.iterrows():
        txt = ax.text(
            row.geometry.x,
            row.geometry.y,
            f"{row['timepoint'].split('-')[0]}",
            fontsize=9

        )
        txt.set_url(row["np"])
        texts.append(
            txt
        )
    adjust_text(texts, ax=ax)

    plt.savefig("map.svg")


data = pd.read_csv("data_formatted.csv")

plot_folium_map(data)
plot_geopandas_map(data)






