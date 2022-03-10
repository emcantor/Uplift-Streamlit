
   
from ast import IsNot
from sqlalchemy import null
import streamlit as st
import json
import gspread
from se_tools import sql_tools
import pandas as pd

def display():
    st.header('Uplifts')
    df = pd.read_json('../uplifts_data.json', orient= 'index')
    style = df[['app_name', 'time_added']]
    st.write(style)

    search = st.text_input('Search By App Name For Full Info')
    text = search.lower()

    if text == '':
        pass
    else:
        full_df=df[df['app_name'].str.lower().str.contains(str(text), na=False)]
        st.write(full_df)