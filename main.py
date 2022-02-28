import streamlit as st
import gspread

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
    controlgroup = st.slider('Control Group Size', step=10, min_value=0, max_value=30, value=20)
    target_custom_actions = st.text_input('Target Actions - Please Separate With Comma And No Spaces')
    email = st.text_input('Email')
    st.button('Run', on_click=lambda: update_sheet(pre_post, type, and_bundle, ios_bundle, start_date, end_date, end_date_action, campaigns, controlgroup, target_custom_actions, email))

json = 'placeholder'
spreadsheet = 'Placeholder'
gc = gspread.service_account(filename=fr'{json}')
worksheet = gc.open(fr'{spreadsheet}').sheet1
next_row = len(worksheet.get_all_values()) + 1


def update_sheet(pre_post, type, and_bundle, ios_bundle, start_date, end_date, end_date_action, campaigns, controlgroup, target_custom_actions, email):
    try:
        worksheet.update(f'A{next_row}', f'{pre_post}')
        worksheet.update(f'B{next_row}', f'{type}')
        worksheet.update(f'C{next_row}', f'{and_bundle}')
        worksheet.update(f'D{next_row}', f'{ios_bundle}')
        worksheet.update(f'E{next_row}', f'{start_date}')
        worksheet.update(f'F{next_row}', f'{end_date}')
        worksheet.update(f'G{next_row}', f'{end_date_action}')
        worksheet.update(f'H{next_row}', f'{campaigns}')
        worksheet.update(f'I{next_row}', f'.{controlgroup}')
        worksheet.update(f'J{next_row}', f'{target_custom_actions}')
        worksheet.update(f'L{next_row}', f'{email}')
        worksheet.update(f'M{next_row}', 'to_run')
    except:
        st.error('An Error Occured, Please Contact SE')