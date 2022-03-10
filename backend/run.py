import json
from se_tools import sql_tools
import pandas as pd
import os
import logging
import sys

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
    # uplift_key: unique key
    # ud: uplift data: all the uplift data (params only when recently added)
    
    # TO-DO: adapt below line to execute recurring uplifts
    if ud['status'] != 'to_run':
        continue
    
    # Create raw_data folder and logfile
    if not os.path.exists('raw_data/' + uplift_key):
        os.mkdir('raw_data/' + uplift_key)
    open('../logs/' + uplift_key + '.log', 'a').close()
    logging.basicConfig(level=logging.INFO, filename='../logs/' + uplift_key + '.log', filemode='w', format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    log = logging.getLogger(__name__)
    
    # Pull bundle_ids and campaign_ids
    bundles = sql_tools.pull_from_presto("select os, bundle_identifier from dim_campaign where app_name = '" + ud['app_name'] + "' order by 1", verbose=False).bundle_identifier.unique()
    update_uplift_data(uplift_key, 'bundle_a', bundles[0])
    update_uplift_data(uplift_key, 'bundle_i', bundles[1] if len(bundles) > 1 else bundles[0])
    cids = sql_tools.pull_from_presto("select campaign_id from dim_campaign where campaign_name in ('" + "','".join(ud['campaign_names']) + "') order by 1", verbose=False).campaign_id.unique()
    print(cids)
    update_uplift_data(uplift_key, 'campaign_ids', list(cids))
    
    # Pull users lists
    # update_uplift_data(uplift_key, 'status', 'pulling_user_lists')
    update_uplift_data(uplift_key, 'progress', 10)
    sql_tools.create_targeted_users_table(
        start_date = ud['begin_date'],
        end_date = ud['end_date_targeting'],
        bundle_ids = [ud['bundle_a'], ud['bundle_i']],
        table_name = '_'.join([ud['bundle_a'], ud['bundle_i']]).replace('.', ''),
        data_local_path = 'raw_data/' + uplift_key + '/',
        campaign_ids = ud['campaign_ids'],
        control_group_size=100*ud['control_group_size'],
        log=log
    )
    
    # Pulling uplift raw data
    update_uplift_data(uplift_key, 'progress', 25)
    with open('queries/ulift_query.sql') as f:
        q = f.read()
        q = q.replace('%begin_date', ud['begin_date'])
        q = q.replace('%end_date_targeting', ud['end_date_targeting'])
        q = q.replace('%end_date', ud['end_date'])
        q = q.replace('%bundle_a', ud['bundle_a'])
        q = q.replace('%bundle_i', ud['bundle_i'])
        q = q.replace('%table_name', '_'.join([ud['bundle_a'], ud['bundle_i']]).replace('.', ''))
        q = q.replace('%campaign_ids_e', " and affiliation.campaignid in (" + ",".join([str(c) for c in ud['campaign_ids']]) + ")" if len(ud['campaign_ids']) >0 else "")
        q = q.replace('%campaign_ids', " and dc.campaign_id in (" + ",".join([str(c) for c in ud['campaign_ids']]) + ")" if len(ud['campaign_ids']) >0 else "")
        log.info(q)
            
    uplift = sql_tools.pull_from_presto(q, verbose=False)
    update_uplift_data(uplift_key, 'progress', 70)
    update_uplift_data(uplift_key, 'status', 'to_run')