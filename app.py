import streamlit as st
import pandas as pd
import pydeck as pdk
import h3
import openai

st.set_page_config(layout="wide")

st.title("📍 ZIP-Level Hotness Map with GPT Insights")

# Upload your Parquet file
uploaded_file = st.file_uploader("Upload your Parquet file", type=["parquet"])

if uploaded_file:
    df = pd.read_parquet(uploaded_file)
    st.success("File loaded!")

    # Preview the data
    st.subheader("Data Preview")
    st.dataframe(df.head())

    # Select lat/lon columns
    lat_col = st.selectbox("Latitude column", df.columns, index=0)
    lon_col = st.selectbox("Longitude column", df.columns, index=1)

    # Optionally compute H3
    if st.checkbox("Add H3 index", value=True):
        resolution = st.slider("H3 resolution", 3, 10, 7)
        df["h3"] = df.apply(lambda row: h3.geo_to_h3(row[lat_col], row[lon_col], resolution), axis=1)

    # Map it
    st.subheader("Map")
    st.map(df[[lat_col, lon_col]])

    # Optional GPT Chat
    st.subheader("🧠 Ask GPT About This Data")

    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = st.text_input("Enter your OpenAI API key", type="password")

    user_msg = st.chat_input("Ask something about this data...")

    if user_msg and st.session_state.openai_api_key:
        subset = df.head(20).to_csv(index=False)
        prompt = f"You are looking at real estate ZIP-level data. Here are the first 20 rows:\n\n{subset}\n\nQuestion: {user_msg}"
        openai.api_key = st.session_state.openai_api_key

        with st.spinner("Thinking..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            st.markdown("**GPT says:**")
            st.write(response.choices[0].message.content)
