import streamlit as st
from PIL import Image
import gspread
from se_tools import sql_tools
import pandas as pd
from uplift import new_uplift
from display import display
from scheduled import scheduled


st.set_page_config(page_title='Incrementality Tools and Status', page_icon=Image.open(
    'img/logo.png'), layout='wide')

if 'page' not in st.session_state:
    st.session_state['page'] = 'display'


def set_page(new_page):
    st.session_state['page'] = new_page


st.sidebar.title("Incrementality Tools and Status")
st.sidebar.button("Incrementality Results",
                  on_click=set_page, args=('display', ))
st.sidebar.button("Uplift Request Form",
                  on_click=set_page,  args=('new', ))
st.sidebar.button("Scheduled Uplifts List",
                  on_click=set_page, args=('scheduled',))

if st.session_state['page'] == 'display':
    display()
elif st.session_state['page'] == 'new':
    new_uplift()
elif st.session_state['page'] == 'scheduled':
    scheduled()
