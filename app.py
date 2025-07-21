import streamlit as st
import pandas as pd
import pydeck as pdk
import h3
from shapely.geometry import Polygon

st.set_page_config(layout="wide")
st.title("🔥 ZIP vs CBSA Differential Choropleth (H3)")

# Uploads
crosswalk_file = st.file_uploader("Upload H3 Crosswalk", type=["parquet"])
zip_file = st.file_uploader("Upload ZIP-level Metrics", type=["parquet"])
cbsa_file = st.file_uploader("Upload CBSA-level Metrics", type=["parquet"])

if crosswalk_file and zip_file and cbsa_file:
    # Load all data
    crosswalk = pd.read_parquet(crosswalk_file)
    zip_data = pd.read_parquet(zip_file)
    cbsa_data = pd.read_parquet(cbsa_file)

    # Merge metrics
    df = crosswalk.merge(zip_data, on="ZIP5").merge(cbsa_data, on="CBSA", suffixes=("_zip", "_cbsa"))

    metric = st.selectbox("Choose metric to compare", [col for col in df.columns if "_zip" in col])
    zip_metric = metric
    cbsa_metric = metric.replace("_zip", "_cbsa")

    df["DIFFERENCE"] = df[zip_metric] - df[cbsa_metric]

    # Get polygon boundary for each H3
    df["polygon"] = df["h3"].apply(lambda x: h3.h3_to_geo_boundary(x, geo_json=True))
    df["lat"] = df["polygon"].apply(lambda coords: sum([p[1] for p in coords]) / len(coords))
    df["lon"] = df["polygon"].apply(lambda coords: sum([p[0] for p in coords]) / len(coords))

    # Map Layer
    hex_layer = pdk.Layer(
        "PolygonLayer",
        data=df,
        get_polygon="polygon",
        get_fill_color="[255 * (DIFFERENCE > 0), 100, 255 * (DIFFERENCE < 0), 140]",
        pickable=True,
        auto_highlight=True,
    )

    view = pdk.ViewState(latitude=df["lat"].mean(), longitude=df["lon"].mean(), zoom=5)
    st.pydeck_chart(pdk.Deck(layers=[hex_layer], initial_view_state=view, tooltip={"text": "ZIP: {ZIP5}\nΔ: {DIFFERENCE}"}))

    st.subheader("Data Preview")
    st.dataframe(df[["ZIP5", "CBSA", "DIFFERENCE", zip_metric, cbsa_metric]].head())
