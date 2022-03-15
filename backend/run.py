import json
from se_tools import sql_tools, gsheet_tools
import pandas as pd
import os
import logging
import traceback


# Master JSON containing the ud, status and output path of all uplifts
uplifts_data_json_path = '../uplifts_data.json'

# Read in the master JSON
with open(uplifts_data_json_path) as json_file:
    uplifts_data = json.load(json_file)

# Define a function that'll update the JSON file everytime the script makes progress


def update_uplift_data(uplift_key, key, data):
    global uplifts_data_json_path
    global uplifts_data
    uplifts_data[uplift_key][key] = data
    with open(uplifts_data_json_path, 'w') as f:
        json.dump(uplifts_data, f)
    return ud


for uplift_key, ud in uplifts_data.items():
    try:
        # uplift_key: unique key
        # ud: uplift data: all the uplift data (params only when recently added)

        # TO-DO: adapt below line to execute recurring uplifts
        if ud['status'] != 'to_run':
            continue

        update_uplift_data(uplift_key, 'status', "running")

        # Create raw_data folder and logfile
        if not os.path.exists('raw_data/' + uplift_key):
            os.mkdir('raw_data/' + uplift_key)
        open('../logs/' + uplift_key + '.log', 'a').close()
        logging.basicConfig(level=logging.INFO, filename='../logs/' + uplift_key + '.log', filemode='w',
                            format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        log = logging.getLogger(__name__)

        # Pull bundle_ids and campaign_ids
        bundles = sql_tools.pull_from_presto("select os, bundle_identifier from dim_campaign where app_name = '" +
                                             ud['app_name'] + "' order by 1", verbose=False).bundle_identifier.unique()
        update_uplift_data(uplift_key, 'bundle_a', bundles[0])
        update_uplift_data(uplift_key, 'bundle_i',
                           bundles[1] if len(bundles) > 1 else bundles[0])
        cids = sql_tools.pull_from_presto("select campaign_id from dim_campaign where campaign_name in ('" + "','".join(
            ud['campaign_names']) + "') order by 1", verbose=False).campaign_id.unique()
        update_uplift_data(uplift_key, 'campaign_ids', [str(c) for c in cids])

        # Set dates if recurring
        if ud['frequency'] != "None" and ud['frequency'] != None:
            update_uplift_data(uplift_key, 'begin_date', str(
                (pd.to_datetime('today') - pd.Timedelta(ud['window'], 'd')).date()))
            update_uplift_data(uplift_key, 'end_date', str(
                pd.to_datetime('today').date()))
            update_uplift_data(uplift_key, 'end_date_targeting',
                               str(pd.to_datetime('today').date()))

        # Pull users lists
        # update_uplift_data(uplift_key, 'status', 'pulling_user_lists')
        table_name = '_'.join(
            [ud['bundle_a'], ud['bundle_i']]).replace('.', '').replace('-', '')
        update_uplift_data(uplift_key, 'progress', 10)
        sql_tools.create_targeted_users_table(
            start_date=ud['begin_date'],
            end_date=ud['end_date_targeting'],
            bundle_ids=[ud['bundle_a'], ud['bundle_i']],
            table_name=table_name,
            data_local_path='raw_data/' + uplift_key + '/',
            campaign_ids=ud['campaign_ids'],
            control_group_size=ud['control_group_size'],
            process=True,
            log=log
        )

        # Pulling uplift raw data
        update_uplift_data(uplift_key, 'progress', 25)
        with open('queries/uplift_query.sql') as f:
            q = f.read()
            q = q.replace('%begin_date', ud['begin_date'])
            q = q.replace('%end_date_targeting', ud['end_date_targeting'])
            q = q.replace('%end_date', ud['end_date'])
            q = q.replace('%bundle_a', ud['bundle_a'])
            q = q.replace('%bundle_i', ud['bundle_i'])
            q = q.replace('%table_name', table_name)
            q = q.replace('%campaign_ids_e', " and affiliation.campaignid in (" + ",".join(
                [str(c) for c in ud['campaign_ids']]) + ")" if len(ud['campaign_ids']) > 0 else "")
            q = q.replace('%campaign_ids', " and dc.campaign_id in (" + ",".join(
                [str(c) for c in ud['campaign_ids']]) + ")" if len(ud['campaign_ids']) > 0 else "")
            log.info(q)

        uplift = sql_tools.pull_from_presto(q, verbose=False).fillna('')
        update_uplift_data(uplift_key, 'progress', 70)

        # Creating output
        gc = gsheet_tools.authenticate()
        template = gc.open_by_key(
            "1-t0SPjI_VQRBdl9xgE5g3q8EIxEGQruJu3TC7FQyNQs")

        # wks_name = 'Incrementality Reporting - ' + \
        #     ud['company_name'] + ' | ' + \
        #     ' - ' + ud['app_name'] + ' ' + \
        #     ud['begin_date'] + ' - ' + ud['end_date']
        wks_name = 'Incrementality Reporting - ' + \
            ' | ' + \
            ' - ' + ud['app_name'] + ' ' + \
            ud['begin_date'] + ' - ' + ud['end_date']
        spreadsheet = gc.copy(template.id, wks_name)
        spreadsheet.values_clear("raw!A:Z")
        spreadsheet.worksheet('raw').update([uplift.columns.values.tolist(
        )] + uplift.values.tolist(), value_input_option='USER_ENTERED')

        # Updating headers
        sheet = spreadsheet.worksheet('ARPU')
        to_update = dict({
            'D5': ud['begin_date'],
            'E5': ud['end_date_targeting'],
            'F5': ud['end_date'],
            'G5': ud['app_name'],
            'H5': uplift.custom_action.unique()[0] if len(uplift.custom_action.unique()) > 0 else 'NO_DATA',
            'I5': ud['control_group_size']
        })
        sheet.batch_update([{'range': key, 'values': [[value]]}
                            for key, value in to_update.items()])

        log.info('Changing permissions to all Adikteev company...')
        spreadsheet.share('adikteev.com', perm_type='domain',
                          role='writer', notify=False)
        for recipient in ud['email']:
            if '@' in recipient:
                log.info('Sharing report with' + recipient)
                spreadsheet.share(recipient.strip(), perm_type='user',
                                  role='writer', notify=True, email_message='Uplift output for ' + wks_name)

        update_uplift_data(
            uplift_key, 'url', "https://docs.google.com/spreadsheets/d/%s" % spreadsheet.id)

        update_uplift_data(uplift_key, 'progress', 100)
        update_uplift_data(uplift_key, 'status',
                           'recurring' if ud['frequency'] != "None" and ud['frequency'] != None else "done")
        update_uplift_data(uplift_key, 'error_massage', '')
        if ud['frequency'] != "None" and ud['frequency'] != None:
            past_uplifts = {
            } if not 'past_uplift' in ud else ud['past_uplifts']
            past_uplifts[str(pd.to_datetime('today').date())] = 'url'
            update_uplift_data(uplift_key, 'past_uplifts', past_uplifts)

    except Exception as e:
        update_uplift_data(uplift_key, 'status', "failed")
        log.info(e)
        log.info(traceback.format_exc())
        update_uplift_data(uplift_key, 'error_massage', traceback.format_exc())
