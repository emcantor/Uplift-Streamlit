import streamlit as st

# title of app
st.title('Uplift')


with st.container():
    pre_post = st.selectbox('Pre Or Post Launch',('prelaunch', 'postlaunch'))

    type = st.selectbox(
        'Uplift Type',
        ('custom_actions', 'reopens', 'installs'))

    ios_bundle = st.text_input('iOS Bundle ID')
    and_bundle = st.text_input('Android Bundle ID')

    start_date = st.date_input('Start Date')
    end_date = st.date_input('End Date')
    end_date_action = st.date_input('End Date Action', end_date)
    campaigns = st.text_input('Please Put All Campaign IDs With Comma and No Spaces', placeholder='ex. 1234,5678,91011')
    controlgroup = st.slider('Control Group Size', step=10, min_value=0, max_value=30)
    target_custom_actions = st.text_input('Target Actions - Please Separate With Comma And No Spaces')
    email = st.text_input('Email')