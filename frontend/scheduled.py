

from ast import IsNot
from this import d
from sqlalchemy import null
import streamlit as st
from se_tools import sql_tools
import pandas as pd
from st_aggrid.shared import GridUpdateMode
from st_aggrid import AgGrid
from st_aggrid.shared import JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from streamlit_autorefresh import st_autorefresh


def scheduled():
    st.title('Scheduled')

    df_scheduled = pd.read_csv(
        '../scheduled.txt', sep='/n', names=['uplift_key'], dtype={'uplift_key': float})

    df_all = pd.read_json('../uplifts_data.json',
                          orient='index').reset_index(drop=True)

    # https://stackoverflow.com/questions/69578431/how-to-fix-streamlitapiexception-expected-bytes-got-a-int-object-conver
    df_all['campaign_names'] = df_all['campaign_names'].astype(str)
    df_all['uplift_key'] = df_all['uplift_key'].astype(float)

    df = pd.merge(df_scheduled, df_all, how='inner', on='uplift_key')

    preview_cols = ['selling_entity', 'app_name', 'date_added',
                    'window', 'frequency', 'dow', 'url']

    gb = GridOptionsBuilder.from_dataframe(df[preview_cols])
    gb.configure_column("url",
                        # headerName="Link",
                        cellRenderer=JsCode(
                            '''function(params) {return '<a target="_blank" href="' + params.value + '" >' + params.value + '</a>'}'''),
                        width=300)
    gb.configure_selection(selection_mode="single", use_checkbox=True)

    gridOptions = gb.build()
    data = AgGrid(
        df[preview_cols],
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED
    )
    if "selected_rows" in data and len(data['selected_rows']) > 0:
        st.write(df[df['time_added'] == data['selected_rows']
                    [0]['time_added']].to_dict(orient='records'))
