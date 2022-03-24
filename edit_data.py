import pandas as pd
import json
from se_tools import sql_tools

uplifts_data_json_path = 'uplifts_data.json'


# def get_country(x):
#     return sql_tools.pull_from_presto("select selling_entity from dim_campaign where app_name = '" + x['app_name'] + "'").selling_entity.values[0].split(' ')[-1]


with open(uplifts_data_json_path) as json_file:
    d = json.load(json_file)

for key, value in d.items():
    # d[key]['frequency_type'] = 'recurring' if d[key]['status'] == 'recurring' else 'one-off'
    # d[key]['date_added'] = str(pd.to_datetime(d[key]['time_added']).date())
    # d[key]['selling_entity'] = get_country(d[key])
    # d[key]['time_added'] = str(pd.to_datetime(
    #     d[key]['time_added']).replace(microsecond=0))
    if d[key]['selling_entity'] == 'US':
        d[key]['selling_entity'] = '🇺🇸'
    elif d[key]['selling_entity'] == 'EMEA':
        d[key]['selling_entity'] = '🇫🇷'
    elif d[key]['selling_entity'] == 'DE':
        d[key]['selling_entity'] = '🇩🇪'

with open(uplifts_data_json_path, 'w') as f:
    json.dump(d, f)
