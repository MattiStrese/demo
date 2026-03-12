import streamlit as st

st.set_page_config(page_title="Demo App", page_icon="🚀")

st.title("My First Streamlit Cloud App")

name = st.text_input("Enter your name")

if st.button("Say hello"):
    st.success(f"Hello {name} 👋")

st.write("This app is hosted on Streamlit Community Cloud.")