import pandas as pd
import streamlit as st

df_id = pd.read_csv('../scheduled.txt', sep='/n', header=None, engine='python', index_col=0)
df_list = pd.read_json('../uplifts_data.json', orient='index')
df = pd.merge(df_id, df_list, left_index=True, right_index=True)
df_write = df[['bundle_a', 'bundle_i', 'campaign_ids']]
df_write

def scheduled():
    st.header('Scheduled Uplifts')
    st.write(df_write)