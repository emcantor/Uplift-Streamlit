import json

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def read_uplifts_data(uplifts_data_json_path):
    # Read in the master JSON
    with open(uplifts_data_json_path) as json_file:
        uplifts_data = json.load(json_file)
    return uplifts_data