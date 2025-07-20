import streamlit as st
import pandas as pd
import pydeck as pdk
import h3
import requests

st.set_page_config(layout="wide")
st.title("🏙️ CBSA and ZIP-Level Real Estate Insights")

# === Load ZIP and CBSA data ===
zip_df = pd.read_parquet("data/zip5_gdf.parquet")
cbsa_df = pd.read_parquet("data/cbsa_gdf.parquet")

# === Tabs to separate views ===
tab1, tab2 = st.tabs(["📍 ZIP Choropleth", "🏙️ CBSA Explorer"])

# === ZIP-Level Map ===
with tab1:
    st.subheader("ZIP Hotness by H3")
    score_col = st.selectbox("Score column", zip_df.columns)

    resolution = st.slider("H3 Resolution", 3, 10, 7)
    
    # If geometry exists, convert to centroid
    if "geometry" in zip_df.columns:
        zip_df["centroid_lat"] = zip_df["geometry"].apply(lambda g: g.centroid.y if hasattr(g, "centroid") else None)
        zip_df["centroid_lon"] = zip_df["geometry"].apply(lambda g: g.centroid.x if hasattr(g, "centroid") else None)
        lat_col, lon_col = "centroid_lat", "centroid_lon"
    else:
        lat_col = st.selectbox("Latitude column", zip_df.columns)
        lon_col = st.selectbox("Longitude column", zip_df.columns)
    
    # Only compute H3 where lat/lon are valid
    zip_df = zip_df.dropna(subset=[lat_col, lon_col])
    zip_df["h3"] = zip_df.apply(lambda row: h3.geo_to_h3(float(row[lat_col]), float(row[lon_col]), resolution), axis=1)

    hex_df = zip_df.groupby("h3")[score_col].mean().reset_index()
    hex_df["geometry"] = hex_df["h3"].apply(lambda x: h3.h3_to_geo_boundary(x, geo_json=True))
    hex_df["centroid"] = hex_df["h3"].apply(lambda x: h3.h3_to_geo(x))

    hex_layer = pdk.Layer(
        "PolygonLayer",
        data=hex_df,
        get_polygon="geometry",
        get_fill_color=f"[{score_col} * 10, 100, 150, 140]",
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=hex_df["centroid"].apply(lambda x: x[0]).mean(),
        longitude=hex_df["centroid"].apply(lambda x: x[1]).mean(),
        zoom=6,
        pitch=0
    )

    st.pydeck_chart(pdk.Deck(layers=[hex_layer], initial_view_state=view_state))

# === CBSA-Level Analysis ===
with tab2:
    st.subheader("CBSA Indicators")
    st.dataframe(cbsa_df)

    cbsa_col = st.selectbox("Choose a CBSA column to explore", cbsa_df.columns)
    st.bar_chart(cbsa_df.set_index("METRO")[cbsa_col])
