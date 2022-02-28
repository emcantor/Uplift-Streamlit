import gspread

gc = gspread.service_account(filename=r'/Volumes/GoogleDrive/My Drive/Eric/striped-micron-337817-6f1dab287a75.json')
worksheet = gc.open(r'Uplift Test').sheet1
next_row = len(worksheet.get_all_values()) + 1


def update_sheet(pre_post, type, and_bundle, ios_bundle, start_date, end_date, end_date_action, campaigns, controlgroup, target_custom_actions, email):
    worksheet.update(f'A{next_row}', pre_post)
    worksheet.update(f'B{next_row}', type)
    worksheet.update(f'C{next_row}', and_bundle)
    worksheet.update(f'D{next_row}', ios_bundle)
    worksheet.update(f'E{next_row}', start_date)
    worksheet.update(f'F{next_row}', end_date)
    worksheet.update(f'G{next_row}', end_date_action)
    worksheet.update(f'H{next_row}', campaigns)
    worksheet.update(f'I{next_row}', controlgroup)
    worksheet.update(f'J{next_row}', target_custom_actions)
    worksheet.update(f'L{next_row}', email)
    worksheet.update(f'M{next_row}', 'to_run')