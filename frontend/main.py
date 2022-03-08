import streamlit as st
import json
import gspread
from se_tools import sql_tools
import pandas as pd
from uplift import new_uplift
from display import display

st.title('Uplift Request')

menu = st.sidebar.selectbox('Menu', ('Uplifts', 'Uplift Request Form'))

if menu == 'Uplift Request Form':
    new_uplift()
else:
    display()