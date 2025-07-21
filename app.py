import streamlit as st
import geopandas as gpd
import pydeck as pdk

st.set_page_config(layout="wide")
st.title("🗺️ ZIP & CBSA Polygon Viewer (No DuckDB, No H3)")

uploaded_zip = st.file_uploader("Upload ZIP GeoParquet", type=["parquet"], key="zip")
uploaded_cbsa = st.file_uploader("Upload CBSA GeoParquet", type=["parquet"], key="cbsa")

if uploaded_zip:
    zip_gdf = gpd.read_parquet(uploaded_zip)
    st.success("ZIP file loaded.")
    st.write(zip_gdf.head())

if uploaded_cbsa:
    cbsa_gdf = gpd.read_parquet(uploaded_cbsa)
    st.success("CBSA file loaded.")
    st.write(cbsa_gdf.head())

if uploaded_zip and uploaded_cbsa:
    st.subheader("📍 Map View")

    # Convert to lat/lon
    zip_gdf = zip_gdf.to_crs(epsg=4326)
    cbsa_gdf = cbsa_gdf.to_crs(epsg=4326)

    zip_centroids = zip_gdf.centroid
    cbsa_centroids = cbsa_gdf.centroid

    zip_layer = pdk.Layer(
        "ScatterplotLayer",
        data=zip_centroids,
        get_position="geometry.coordinates",
        get_radius=500,
        get_fill_color="[255, 100, 100, 150]",
        pickable=True
    )

    cbsa_layer = pdk.Layer(
        "ScatterplotLayer",
        data=cbsa_centroids,
        get_position="geometry.coordinates",
        get_radius=1000,
        get_fill_color="[100, 100, 255, 150]",
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=zip_centroids.y.mean(),
        longitude=zip_centroids.x.mean(),
        zoom=5,
        pitch=0
    )

    st.pydeck_chart(pdk.Deck(
        layers=[zip_layer, cbsa_layer],
        initial_view_state=view_state,
        tooltip={"text": "ZIP or CBSA Area"}
    ))
