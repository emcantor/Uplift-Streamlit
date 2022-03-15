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

def set_dow(schedule, dow):
    if dow == 'Monday':
        return schedule.monday
    elif dow == 'Tuesday':
        return schedule.tuesday
    elif dow == 'Wednesday':
        return schedule.wednesday
    elif dow == 'Thursday':
        return schedule.thursday
    elif dow == 'Friday':
        return schedule.friday
    

for k, v in uplifts_data.items():
    hour = v['time_added'][11:].split('.')[0][:5]
    minute = v['time_added'][14:].split('.')[0]
    if v['frequency'] == 'Daily':
        schedule.every().day.at(hour).do(run_uplift, uplift_key=k)
    elif v['frequency'] == 'Weekly':
        set_dow(schedule.every(), v['dow']).do(run_uplift, uplift_key=k)
    elif v['frequency'] == 'BiWeekly':
        set_dow(schedule.every(2), v['dow']).do(run_uplift, uplift_key=k)
    elif v['frequency'] == 'Monthly':
        set_dow(schedule.every(4), v['dow']).do(run_uplift, uplift_key=k)
    elif v['frequency'] == 'Minute':
        schedule.every().minute.at(minute).do(run_uplift, uplift_key=k)


while 1:
    if file_len('../scheduled.txt') != scheduled_count:
        log.info('Detected new scheduled uplift, restarting')
        os.execv(sys.executable, ['python3'] + sys.argv)
    schedule.run_pending()
    time.sleep(1)
