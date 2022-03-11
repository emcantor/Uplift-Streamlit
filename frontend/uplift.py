import streamlit as st
import ast
import json
from se_tools import sql_tools
import pandas as pd

def new_uplift():
    # title of app
    st.title('Pull New Uplift')

    @st.cache
    def campaign_names(app_name, os):
        if os == 'Both':
            os = "'ANDROID', 'IOS'"
        else:
            os = "'" + os.upper() + "'"
        df = sql_tools.pull_from_presto("select distinct campaign_name from dim_campaign where app_name = '" + app_name + "' and os in (" +  os + ")", verbose=False)
        return df
    
    @st.cache
    def app_name_function(company):
        df = sql_tools.pull_from_presto(f"select distinct app_name from dim_campaign dc inner join dim_bundle_identifier dbi on dc.bundle_identifier = dbi.bundle_identifier inner join dim_company dco on dco.company_id = dbi.company_id where company_name = '{company}'", verbose=False)
        return df

    @st.cache
    def company_name_function():
        df = sql_tools.pull_from_presto("select distinct company_name from dim_company", verbose=False)
        return df

    with st.container():
        pre_post = st.selectbox('Pre Or Post Launch',('postlaunch', 'prelaunch'))
        comp_name = st.selectbox('Company Name', company_name_function())
        app_names = app_name_function(comp_name)
        app_name = st.selectbox('App Name', app_names)
        os = st.radio('OS', ('Android', 'iOS', 'Both'))
        cname = campaign_names(app_name, os)
        campaign_name = st.multiselect('Campaign Names', cname)
        page = st.radio("One Time or Recurring?", ('One Time', 'Recurring'))
        if page == 'One Time':
            start_date = st.date_input('Start Date')
            end_date = st.date_input('End Date')
            end_date_action = end_date
            window = None
            frequency = None
            dow = None
        else:
            window = st.number_input('How Many Days?', step=1, min_value=1)
            frequency = st.radio('How Often Should This Run?', ('Daily', 'Weekly', 'BiWeekly', 'Monthly'))
            if frequency == 'Daily':
                pass
            else:
                dow = st.radio('What Day Should The Report Run', ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'))
            start_date = None
            end_date = None
            end_date_action = None

        controlgroup = st.slider('Control Group Size', step=10, min_value=0, max_value=30, value=20)            
        email = st.text_input('Email', placeholder='Separate Emails With Comma')
        email = email.split(',')

        if page == 'One Time':
            st.button('Pull', on_click=lambda: to_json())
        else:
            st.button('Schedule', on_click=lambda: to_json())
        

    def to_json():
        # Create unique uplift key
        params = {
                "pre_post": pre_post,
                "app_name": app_name,
                "os": os,
                "page": page,
                "campaign_names": campaign_name,
                'begin_date': str(start_date),
                'end_date_targeting' : str(end_date),
                'end_date':  str(end_date_action),
                'window' : window,
                'frequency' : frequency,
                'control_group_size': controlgroup,
                'email': email,
                'status': 'recurring' if frequency else 'to_run',
                'time_added': str(pd.to_datetime('now'))
            }
        # Create unique uplift key
        uplift_key = str(abs(hash(frozenset(str(params.items()) + str(pd.Timestamp.now())))))
        with open('../uplifts_data.json') as json_file:
            uplifts_data = json.load(json_file)
        uplifts_data[uplift_key] = params
        with open('../uplifts_data.json', 'w') as f:
            json.dump(uplifts_data, f, ensure_ascii=False)
        if frequency:
            with open('../scheduled.txt', 'a') as f:
                f.write('\n')
                f.write(uplift_key)