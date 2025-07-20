import streamlit as st
import pandas as pd
import pydeck as pdk
import h3
import os

st.set_page_config(layout="wide")
st.title("🏙️ ZIP-MSA Hotness Differential Map (H3 Choropleth)")

# === Load Parquet Files ===
zip_df = pd.read_parquet("data/zip5_gdf.parquet")
cbsa_df = pd.read_parquet("data/cbsa_gdf.parquet")

# === Column Selection ===
score_col = st.selectbox("Select metric to compare", [c for c in zip_df.columns if "SCORE" in c or "VALUE" in c])
cbsa_col = st.selectbox("Matching CBSA metric", [c for c in cbsa_df.columns if "SCORE" in c or "VALUE" in c])

zip_cbsa_join_col = st.selectbox("CBSA join key", ["CBSA", "CBSA_CODE", "metro", "METROCODE"])
zip_lat = st.selectbox("ZIP latitude column", [c for c in zip_df.columns if "lat" in c.lower()])
zip_lon = st.selectbox("ZIP longitude column", [c for c in zip_df.columns if "lon" in c.lower()])

resolution = st.slider("H3 Resolution", 3, 10, 7)

# === Merge ZIP + CBSA ===
merged = pd.merge(zip_df, cbsa_df, on=zip_cbsa_join_col, suffixes=("_ZIP", "_MSA"))
merged["DIFFERENTIAL"] = merged[f"{score_col}_ZIP"] - merged[f"{cbsa_col}_MSA"]

# === Compute H3 ===
merged["h3"] = merged.apply(lambda row: h3.geo_to_h3(row[zip_lat], row[zip_lon], resolution), axis=1)

# === Aggregate by H3 ===
hex_df = merged.groupby("h3")["DIFFERENTIAL"].mean().reset_index()
hex_df["geometry"] = hex_df["h3"].apply(lambda x: h3.h3_to_geo_boundary(x, geo_json=True))
hex_df["centroid"] = hex_df["h3"].apply(lambda x: h3.h3_to_geo(x))

# === Map Layer ===
hex_layer = pdk.Layer(
    "PolygonLayer",
    data=hex_df,
    get_polygon="geometry",
    get_fill_color="[255 * (1 - (DIFFERENTIAL + 10)/20), 100, 255 * ((DIFFERENTIAL + 10)/20), 150]",
    pickable=True,
    auto_highlight=True,
)

view_state = pdk.ViewState(
    latitude=hex_df["centroid"].apply(lambda x: x[0]).mean(),
    longitude=hex_df["centroid"].apply(lambda x: x[1]).mean(),
    zoom=5,
)

st.pydeck_chart(pdk.Deck(
    layers=[hex_layer],
    initial_view_state=view_state,
    tooltip={"text": "Diff: {DIFFERENTIAL}"}
))

st.subheader("Underlying H3 + Differential Data")
st.dataframe(hex_df.head(30), use_container_width=True)
