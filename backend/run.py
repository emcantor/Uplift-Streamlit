import json
from se_tools import sql_tools, gsheet_tools, s3_tools
import os
import shutil
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
    return uplifts_data


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

        # Hardcode dates if frequency_type=recurring
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
        update_uplift_data(uplift_key, 'status', '10%')
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
        update_uplift_data(uplift_key, 'status', '25%')
        queries = {}
        for query_file in os.listdir('queries/'):
            with open('queries/' + query_file) as f:
                q = f.read()
                q = q.replace('%begin_date', ud['begin_date'])
                q = q.replace('%end_date_targeting', ud['end_date_targeting'])
                q = q.replace('%end_date', ud['end_date'])
                q = q.replace('%bundle_a', ud['bundle_a'])
                q = q.replace('%bundle_i', ud['bundle_i'])
                q = q.replace('%table_name', table_name)
                q = q.replace('%campaign_ids_e', " and affiliation.campaignid in (" + ",".join(
                    [str(c) for c in ud['campaign_ids']]) + ")" if len(ud['campaign_ids']) > 0 else "")
                q = q.replace('%campaign_ids_dc', " and dc.campaign_id in (" + ",".join(
                    [str(c) for c in ud['campaign_ids']]) + ")" if len(ud['campaign_ids']) > 0 else "")
                q = q.replace('%campaign_ids_t', " and t.campaign_id in (" + ",".join(
                    [str(c) for c in ud['campaign_ids']]) + ")" if len(ud['campaign_ids']) > 0 else "")

        # users = 
        exposed= sql_tools.create_or_update_presto_table_from_query(
            q['exposed.sql'])
        users_exposed_rollup = sql_tools.create_or_update_presto_table_from_query(
            q['users_exposed_rollup.sql'])

        campaign_platform_rollup_tt = sql_tools.create_presto_table(
            df=None, query=queries['campaign_platform_rollup.sql'], verbose=False)
        cost_platform_rollup_tt = sql_tools.create_presto_table(
            df=None, query=queries['cost_platform_rollup.sql'], verbose=False)

        queries['uplift.sql'] = queries['uplift.sql'].replace('%cost_platform_rollup_tt', cost_platform_rollup_tt).replace(
            '%campaign_platform_rollup_tt', campaign_platform_rollup_tt)
        log.info(queries['uplift.sql'])
        uplift = sql_tools.pull_from_presto(
            queries['uplift.sql'], verbose=False).fillna('')
        update_uplift_data(uplift_key, 'status', '70%')

        # Creating output
        gc = gsheet_tools.authenticate()
        template = gc.open_by_key(
            "1-t0SPjI_VQRBdl9xgE5g3q8EIxEGQruJu3TC7FQyNQs")

        wks_name = 'Incrementality Reporting ' + ' | ' + \
            ud['app_name'] + ' ' + ud['begin_date'] + ' - ' + ud['end_date']
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
            'I5': ud['control_group_size'] / 100
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

        url = "https://docs.google.com/spreadsheets/d/%s" % spreadsheet.id
        update_uplift_data(
            uplift_key, 'url', url)

        update_uplift_data(uplift_key, 'status',
                           "done")
        update_uplift_data(uplift_key, 'error_message', '')
        if ud['frequency'] != "None" and ud['frequency'] != None:
            past_uplifts = {
            } if not 'past_uplift' in ud else ud['past_uplifts']
            past_uplifts[str(pd.to_datetime('today').date())] = url
            update_uplift_data(uplift_key, 'past_uplifts', past_uplifts)

        log.info('Pulling raw data')
        raw_data_paths = {}
        for query_file in ['events', 'exposed', 'users']:
            output_name = query_file + '_raw_data.csv'
            raw = sql_tools.pull_from_presto(
                queries[query_file + '.sql'], verbose=False)
            raw.to_csv('raw_data/' + uplift_key +
                       '/' + output_name, index=None)
            s3_tools.upload_s3_file('raw_data/' + uplift_key + '/' + output_name,
                                    's3://sandbox-adikteev/uplift_raw_data/uplift_v3/' + uplift_key + '/' + output_name, make_public=True)
            raw_data_paths[output_name] = 'https://sandbox-adikteev.s3.amazonaws.com/uplift_raw_data/uplift_v3/' + \
                uplift_key + '/' + output_name
        update_uplift_data(uplift_key, 'raw_data_s3_paths', raw_data_paths)
        shutil.rmtree('raw_data/' + uplift_key)

    except Exception as e:
        update_uplift_data(uplift_key, 'status', "failed")
        log.info(e)
        log.info(traceback.format_exc())
        update_uplift_data(uplift_key, 'error_message', traceback.format_exc())
