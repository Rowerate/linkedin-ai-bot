import os
import streamlit as st

def save_brand_logo(uploaded_file):
    os.makedirs("assets", exist_ok=True)
    path = os.path.join("assets", "logo.png")
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

def get_logo_path():
    path = os.path.join("assets", "logo.png")
    return path if os.path.exists(path) else None