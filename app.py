import streamlit as st
import pandas as pd
import pydeck as pdk
import h3

st.set_page_config(layout="wide")
st.title("🔥 ZIP vs CBSA Differential Choropleth (H3-Based)")

zip_df = pd.read_parquet("zip5_reference_table.parquet")
cbsa_df = pd.read_parquet("cbsa_reference_table.parquet")
crosswalk = pd.read_parquet("h3_zip_cbsa_crosswalk.parquet")

# Merge and calculate differential
zip_metric_col = "TREND_DEMAND_PCT"
cbsa_metric_col = "TREND_DEMAND_PCT"
    
full = crosswalk.merge(zip_df, on="ZIP5").merge(cbsa_df, on="CBSA", suffixes=("_zip", "_cbsa"))
full["DIFFERENCE"] = full[f"{zip_metric_col}_zip"] - full[f"{cbsa_metric_col}_cbsa"]
    
# Convert H3 to polygon + centroid for map
full["polygon"] = full["h3"].apply(lambda x: h3.h3_to_geo_boundary(x, geo_json=True))
full["lat"] = full["polygon"].apply(lambda coords: sum([pt[1] for pt in coords]) / len(coords))
full["lon"] = full["polygon"].apply(lambda coords: sum([pt[0] for pt in coords]) / len(coords))
    
# Define color function based on positive/negative difference
def get_color(d):
    if d > 5:
        return [231, 76, 60, 160]  # Danger
    elif d > 2:
        return [243, 156, 18, 160]  # Warning
    elif d > 0:
        return [39, 174, 96, 160]  # Success
    elif d > -2:
        return [41, 128, 185, 160]  # Secondary
    else:
        return [127, 127, 127, 160]  # Neutral
    
full["color"] = full["DIFFERENCE"].apply(get_color)
    
# Build pydeck map
hex_layer = pdk.Layer(
"PolygonLayer",
data=full,
get_polygon="polygon",
get_fill_color="color",
pickable=True,
auto_highlight=True,
)
    
view = pdk.ViewState(latitude=full["lat"].mean(), longitude=full["lon"].mean(), zoom=5)
    
st.pydeck_chart(pdk.Deck(
    layers=[hex_layer],
    initial_view_state=view,
    tooltip={"text": "ZIP: {ZIP5}\nΔ: {DIFFERENCE}"}
))
    
st.subheader("Data Preview")
st.dataframe(full[["ZIP5", "CBSA", "DIFFERENCE", f"{zip_metric_col}_zip", f"{cbsa_metric_col}_cbsa"]].head())
