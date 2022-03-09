import json
from se_tools import sql_tools
import pandas as pd
import os
import logging
import sys

# Master JSON containing the ud, status and output path of all uplifts
uplifts_data_json_path = '../uplifts_data.json'

# Define a function that'll update the JSON file everytime the script makes progress
def update_uplift_data(uplifts_data, ts, key, data):
    global uplifts_data_json_path
    uplifts_data[ts][key] = data
    with open(uplifts_data_json_path, 'w') as f:
        json.dump(uplifts_data, f)
    return ud

# Read in the master JSON
with open(uplifts_data_json_path) as json_file:
    uplifts_data = json.load(json_file)
    
for ts, ud in uplifts_data.items():
    # ts: timestamp when the uplift was added from the frontend
    # ud: all the uplift data (ud only when recently added)
    
    # TO-DO: adapt below line to execute recurring uplifts
    if ud['status'] != 'to_run':
        continue
    
    # Create unique uplift key
    uplift_key = str(abs(hash(frozenset(str(ud.items()) + str(pd.Timestamp.now())))))
    update_uplift_data(uplifts_data, ts, 'uplift_key', uplift_key)
    # Create raw_data folder and logfile
    os.mkdir('raw_data/' + uplift_key)
    open('../logs/' + uplift_key + '.log', 'a').close()
    logging.basicConfig(level=logging.INFO, filename='../logs/' + uplift_key + '.log', filemode='w')
    log = logging.getLogger(__name__)
    
    # Pull users lists
    update_uplift_data(uplifts_data, ts, 'status', 'pulling_user_lists')
    sql_tools.create_targeted_users_table(
        start_date = ud['begin_date'],
        end_date = ud['end_date_targeting'],
        bundle_ids = [ud['bundle_a'], ud['bundle_i']],
        table_name = '_'.join([ud['bundle_a'], ud['bundle_i']]).replace('.', ''),
        data_local_path = 'raw_data/' + uplift_key + '/',
        targeting_list_ids = ud['targeting_list_ids'],
        campaign_ids = ud['campaign_ids'],
        log=log
    )
    