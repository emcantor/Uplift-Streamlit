import streamlit as st
import json
import gspread
from se_tools import sql_tools
import pandas as pd

def display():
    st.header('Uplifts')
    df = pd.read_json('../uplifts_data.json', orient= 'index')
    style = df
    st.write(style)