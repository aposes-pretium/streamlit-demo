import streamlit as st
import pandas as pd
import pydeck as pdk
import h3
import requests
import json

st.set_page_config(layout="wide")

st.title("📍 H3 Choropleth of ZIP-Level Real Estate Data")

# Upload Parquet file
uploaded_file = st.file_uploader("Upload your Parquet file", type=["parquet"])

if uploaded_file:
    df = pd.read_parquet(uploaded_file)
    st.success("File loaded!")

    st.subheader("Data Preview")
    st.dataframe(df.head())

    lat_col = st.selectbox("Latitude column", df.columns, index=0)
    lon_col = st.selectbox("Longitude column", df.columns, index=1)
    score_col = st.selectbox("Metric for choropleth (e.g. HOTNESS_SCORE)", df.columns)

    resolution = st.slider("H3 Resolution", 3, 10, 7)

    df["h3"] = df.apply(lambda row: h3.geo_to_h3(row[lat_col], row[lon_col], resolution), axis=1)

    # Aggregate by H3
    hex_df = df.groupby("h3")[score_col].mean().reset_index()
    hex_df["geometry"] = hex_df["h3"].apply(lambda x: h3.h3_to_geo_boundary(x, geo_json=True))
    hex_df["centroid"] = hex_df["h3"].apply(lambda x: h3.h3_to_geo(x))

    # Format for pydeck
    hex_layer = pdk.Layer(
        "PolygonLayer",
        data=hex_df,
        get_polygon="geometry",
        get_fill_color=f"[{score_col} * 10, 100, 150, 140]",
        pickable=True,
        auto_highlight=True
    )

    view_state = pdk.ViewState(
        latitude=hex_df["centroid"].apply(lambda x: x[0]).mean(),
        longitude=hex_df["centroid"].apply(lambda x: x[1]).mean(),
        zoom=6,
        pitch=0
    )

    st.subheader("Choropleth Map")
    st.pydeck_chart(pdk.Deck(layers=[hex_layer], initial_view_state=view_state, tooltip={"text": f"{score_col}: {{{score_col}}}"}))

    # GPT Section
    st.subheader("🧠 Ask Together AI About This Data")

    user_msg = st.chat_input("Ask a question about your data")

    if user_msg and "TOGETHER_API_KEY" in st.secrets:
        preview = df[[lat_col, lon_col, score_col]].head(10).to_csv(index=False)
        prompt = f"You are analyzing real estate data with lat/lon and a score metric named '{score_col}'. Here are the first 10 rows:\n{preview}\n\nQuestion: {user_msg}"

        headers = {
            "Authorization": f"Bearer {st.secrets['TOGETHER_API_KEY']}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": prompt,
            "max_tokens": 300,
            "temperature": 0.7,
        }

        with st.spinner("Thinking..."):
            response = requests.post("https://api.together.xyz/v1/completions", headers=headers, json=payload)
            answer = response.json()["choices"][0]["text"]
            st.markdown("**LLM says:**")
            st.write(answer)
