import json
import streamlit as st
import pandas as pd
from st_aggrid.shared import GridUpdateMode
from st_aggrid import AgGrid
from st_aggrid.shared import JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from streamlit_autorefresh import st_autorefresh


status_style_jscode = JsCode(
    """
function(params) {
    if (params.value == 'failed') {
        return {
            'color': 'white',
            'backgroundColor': 'red'
        }
    } else if  (params.value == 'done') {
        return {
            'color': 'black',
            'backgroundColor': 'lightGreen'
        }
    } else if  (params.value == 'running') {
        return {
            'color': 'black',
            'backgroundColor': 'orange'
        }
    }
};
"""
)


def display():
    # Run the autorefresh about every 2000 milliseconds (2 seconds) and stop
    # after it's been refreshed 100 times.
    count = st_autorefresh(interval=10*1000, limit=100, key="fizzbuzzcounter")
    st.title('Incrementality Results')
    df = pd.read_json('../uplifts_data.json', orient='index',
                      convert_axes=False, dtype={'uplift_key': 'str'}).fillna('')
    preview_cols = ['app_name', 'time_added', 'status', 'url']
    df = df.reset_index(drop=True)
    df['time_added'] = pd.to_datetime(df['time_added']).apply(
        lambda x: x.replace(microsecond=0)).astype(str)
    df.sort_values('time_added', ascending=False, inplace=True)
    df = df[df.status != 'recurring']

    gb = GridOptionsBuilder.from_dataframe(df[preview_cols])
    gb.configure_column("status", cellStyle=status_style_jscode)
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
        selected = df[df['time_added'] == data['selected_rows']
                      [0]['time_added']].to_dict(orient='records')[0]
        uplift_key = str(int(selected["uplift_key"]))

        if 'widget' not in st.session_state:
            st.session_state['widget'] = 'params'

        def set_widget(new_widget):
            st.session_state['widget'] = new_widget

        def update_uplift(uplift_key, key, value):
            with open('../uplifts_data.json') as f:
                d = json.load(f)
            d[uplift_key][key] = value
            with open('../uplifts_data.json', 'w') as f:
                json.dump(d, f)

        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            st.write('Selected row ID: `' + uplift_key + '`')
        with col2:
            st.button('Show Params', on_click=set_widget, args=('params', ))
        with col3:
            st.button('Re-run Uplift', on_click=update_uplift,
                      args=(uplift_key, 'status', 'to_run'))
        with col4:
            st.button('Inspect Logs', on_click=set_widget, args=('logs', ))
        if st.session_state['widget'] == 'params':
            st.write(selected)
        elif st.session_state['widget'] == 'logs':
            with open('../logs/' + str(uplift_key) + '.log') as f:
                logs = f.read()
            st.write('```' + logs + '```')
