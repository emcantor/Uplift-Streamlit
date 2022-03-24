import streamlit as st
import ast
import json
from se_tools import sql_tools
import pandas as pd


def new_uplift():

    # title of app
    st.title('Uplift Request Form')

    @st.cache
    def campaign_names(app_name, os):
        if os == 'Both':
            os = "'ANDROID', 'IOS'"
        else:
            os = "'" + os.upper() + "'"
        df = sql_tools.pull_from_presto(
            "select distinct campaign_name from dim_campaign where app_name = '" + app_name + "' and os in (" + os + ")", verbose=False)
        return df

    @st.cache
    def app_name_function(company):
        df = sql_tools.pull_from_presto(
            f"select distinct app_name from dim_campaign dc inner join dim_bundle_identifier dbi on dc.bundle_identifier = dbi.bundle_identifier inner join dim_company dco on dco.company_id = dbi.company_id where company_name = '{company}'", verbose=False)
        return df

    @st.cache
    def company_name_function():
        df = sql_tools.pull_from_presto(
            "select distinct company_name from dim_company", verbose=False)
        return df

    with st.container():
        pre_post = st.selectbox('Pre Or Post Launch',
                                ('postlaunch', 'prelaunch'))
        comp_name = st.selectbox('Company Name', company_name_function())
        app_names = app_name_function(comp_name)
        app_name = st.selectbox('App Name', app_names)
        os = st.radio('OS', ('Android', 'iOS', 'Both'))
        cname = campaign_names(app_name, os)
        campaign_name = st.multiselect(
            'Campaign Names (Leave empty if need All campaigns)', cname)
        page = st.radio("One Time or Recurring?", ('One Time', 'Recurring'))
        if page == 'One Time':
            start_date = st.date_input('Start Date (for events and users)')
            end_date = st.date_input('End Date (for events and users)')
            end_date_action = end_date
            window = None
            frequency = None
            dow = None
        else:
            window = st.number_input(
                'How Many Days? (Select the amount of days the uplift should cover)', step=1, min_value=1)
            frequency = st.radio('How Often Should This Run?',
                                 ('Daily', 'Weekly', 'BiWeekly', 'Monthly'))
            if frequency == 'Daily':
                pass
            else:
                dow = st.radio('What Day Should The Report Run',
                               ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'))
            start_date = None
            end_date = None
            end_date_action = None

        controlgroup = st.slider('Control Group Size',
                                 step=10, min_value=0, max_value=50, value=20)
        email = st.text_input(
            'Email', placeholder='Separate Emails With Comma')
        email = email.split(',')

        if page == 'One Time':
            st.button('Pull', on_click=lambda: to_json())
        else:
            st.button('Schedule', on_click=lambda: to_json())

    def to_json():
        # Pull bundle_ids and campaign_ids
        bundles = sql_tools.pull_from_presto("select os, bundle_identifier from dim_campaign where app_name = '" +
                                             app_name + "' order by 1", verbose=False).bundle_identifier.unique()
        selling_entity = sql_tools.pull_from_presto(
            "select selling_entity from dim_campaign where app_name = '" + app_name + "'").selling_entity.values[0].split(' ')[-1]
        if selling_entity == 'US':
            selling_entity = '🇺🇸'
        elif selling_entity == 'EMEA':
            selling_entity = '🇫🇷'
        elif selling_entity == 'DE':
            selling_entity = '🇩🇪'

        # Create unique uplift key
        params = {
            "pre_post": pre_post,
            "app_name": app_name,
            "os": os,
            "page": page,
            "campaign_names": campaign_name,
            "campaign_ids": [str(c) for c in sql_tools.pull_from_presto("select campaign_id from dim_campaign where campaign_name in ('" + "','".join(
                campaign_name) + "') order by 1", verbose=False).campaign_id.unique()],
            'begin_date': str(start_date),
            'end_date_targeting': str(end_date),
            'end_date':  str(end_date_action),
            'window': window,
            'dow': dow,
            'frequency': frequency,
            'control_group_size': controlgroup,
            'email': email,
            'status': 'waiting_first_run' if frequency else 'to_run',
            'frequency_type': 'recurring' if frequency else 'one-off',
            'time_added': str(pd.to_datetime('now')),
            'date_added': str(pd.to_datetime('now').date()),
            'selling_entity': selling_entity,
            'bundle_a': bundles[0],
            'bundle_i': bundles[1] if len(bundles) > 1 else bundles[0]
        }
        # Create unique uplift key
        uplift_key = str(
            abs(hash(frozenset(str(params.items()) + str(pd.Timestamp.now())))))
        with open('../uplifts_data.json') as json_file:
            uplifts_data = json.load(json_file)
        uplifts_data[uplift_key] = params
        uplifts_data[uplift_key]['uplift_key'] = uplift_key
        with open('../uplifts_data.json', 'w') as f:
            json.dump(uplifts_data, f, ensure_ascii=False)
        if frequency:
            with open('../scheduled.txt', 'a') as f:
                f.write('\n')
                f.write(uplift_key)
        st.session_state['page'] = 'display'
