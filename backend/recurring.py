import schedule
import time
import json

def run_uplift(uplift_key):
    print("I'm working...")

# Master JSON containing the ud, status and output path of all uplifts
uplifts_data_json_path = '../uplifts_data.json'

with open(uplifts_data_json_path) as json_file:
    uplifts_data = json.load(json_file)
uplifts_data = {k: v for k, v in uplifts_data.items() if v['frequency']}

for k, v in uplifts_data.items():
    if v['frequency'] == 'Daily':
        schedule.every().day.at(v['time_added']).do(run_uplift(v['uplift_key']))
    elif v['frequency'] == 'Weekly':
        schedule.every().monday.at(v['time_added']).do(run_uplift(v['uplift_key']))
    elif v['frequency'] == 'BiWeekly':
        schedule.every(2).monday.at(v['time_added']).do(run_uplift(v['uplift_key']))
    elif v['frequency'] == 'Monthly':
        schedule.every().month.at(v['time_added']).do(run_uplift(v['uplift_key']))
    
    
while 1:
    schedule.run_pending()
    time.sleep(1)