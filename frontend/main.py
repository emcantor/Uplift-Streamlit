import streamlit as st
import json
import gspread
from se_tools import sql_tools
import pandas as pd
from uplift import new_uplift
from display import display
from scheduled import scheduled

st.title('Uplift Request')

menu = st.sidebar.selectbox('Menu', ('Uplifts', 'Uplift Request Form', 'Scheduled Uplifts'))

if menu == 'Uplift Request Form':
    new_uplift()
elif menu == 'Scheduled Uplifts':
    scheduled()
else:
    display()