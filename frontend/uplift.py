import streamlit as st
import json
import gspread
from se_tools import sql_tools
import pandas as pd

def new_uplift():
    # title of app
    st.header('Pull New Uplift')

    @st.cache
    def campaign_names(app_name, os):
        if os == 'Both':
            os = "'ANDROID', 'IOS'"
        else:
            os = "'" + os.upper() + "'"
        df = sql_tools.pull_from_presto("select distinct campaign_name from dim_campaign where app_name = '" + app_name + "' and os in (" +  os + ")")
        return df

    with st.container():
        pre_post = st.selectbox('Pre Or Post Launch',('postlaunch', 'prelaunch'))
        app_names = sql_tools.pull_from_presto("select distinct app_name from dim_campaign order by 1")
        app_name = st.selectbox('App Name', app_names)
        os = st.radio('OS', ('Android', 'iOS', 'Both'))
        cname = campaign_names(app_name, os)
        campaign_name = st.multiselect('Campaign IDs', cname)
        page = st.radio("One Time or Recurring?", ('One Time', 'Recurring'))
        start_date = ''
        end_date = ''
        end_date_action = ''
        window = ''
        frequency = ''
        if page == 'One Time':
            start_date = st.date_input('Start Date')
            end_date = st.date_input('End Date')
            end_date_action = end_date
        else:
            window = st.number_input('How Many Days?', step=1, min_value=1)
            frequency = st.radio('How Often Should This Run?', ('Daily', 'Weekly', 'BiWeekly', 'Monthly'))
            if frequency == 'Daily':
                pass
            else:
                DoW = st.radio('What Day Should The Report Run', ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'))

        controlgroup = st.slider('Control Group Size', step=10, min_value=0, max_value=30, value=20)            
        email = st.text_input('Email')

        if page == 'One Time':
            st.button('Pull', on_click=lambda: to_json())
        else:
            st.button('Schedule', on_click=lambda: to_json())
        

    def to_json():
        with open('params.json', 'w') as f:
            json.dump({
                "pre_post": pre_post,
                "app_name": app_name,
                "os": os,
                "page": page,
                "campaign_names": ','.join(campaign_name),
                'start_date': '',
        'end_date' : str(end_date),
        'end_date_action':  str(end_date_action),
        'window' : window,
        'frequency' : frequency,
        'controlgroup': controlgroup,
        'email': email
            }, f)