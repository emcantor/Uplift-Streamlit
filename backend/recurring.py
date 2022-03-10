import schedule
import os
import sys
import time
import json
from utils import file_len, read_uplifts_data
import logging

logging.basicConfig(level=logging.INFO, filename='../logs/scheduled.log', filemode='a', format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',)
log = logging.getLogger(__name__)
    
    
scheduled_count = file_len('../scheduled.txt')
uplifts_data = read_uplifts_data('../uplifts_data.json')

def run_uplift(uplift_key):
    log.info("Setting " + uplift_key + " next in run pipe.")
    uplifts_data = read_uplifts_data('../uplifts_data.json')
    uplifts_data[uplift_key]['status'] = 'to_run'
    with open('../uplifts_data.json', 'w') as f:
        json.dump(uplifts_data, f)
    

for k, v in uplifts_data.items():
    if v['frequency'] == 'Daily':
        schedule.every().day.at(v['time_added']).do(run_uplift, uplift_key=k)
    elif v['frequency'] == 'Weekly':
        schedule.every().monday.at(v['time_added']).do(run_uplift, uplift_key=k)
    elif v['frequency'] == 'BiWeekly':
        schedule.every(2).monday.at(v['time_added']).do(run_uplift, uplift_key=k)
    elif v['frequency'] == 'Monthly':
        schedule.every().month.at(v['time_added']).do(run_uplift, uplift_key=k)
    elif v['frequency'] == 'Minute':
        schedule.every().minute.at(":00").do(run_uplift, uplift_key=k)
            
    
while 1: 
    if file_len('../scheduled.txt') != scheduled_count:
        log.info('Detected new scheduled uplift, restarting')
        os.execv(sys.executable, ['python'] + sys.argv)
    schedule.run_pending()
    time.sleep(1)

    

