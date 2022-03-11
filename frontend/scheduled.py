import pandas as pd
import streamlit as st

df_id = pd.read_csv('../scheduled.txt', sep='/n', names=['index'])
df_list = pd.read_json('../uplifts_data.json',
                       orient='index', convert_axes=False).reset_index()
df_list['index'] = df_list['index'].astype(int)
df = pd.merge(df_id, df_list, how='inner', on='index')
df_write = df[['bundle_a', 'bundle_i', 'campaign_ids']]


def scheduled():
    st.header('Scheduled Uplifts')
    st.write(df_write)
    # st.write(df_id)
    # st.write(df_list)
