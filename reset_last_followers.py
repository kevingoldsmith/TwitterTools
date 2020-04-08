import os
import json
from collections import OrderedDict
from utils import diff_two_id_sets, dict_to_ordereddict

DATA_DIR = 'data'
DATA_FILE = 'followers.json'

data_path = os.path.join(DATA_DIR, DATA_FILE)

followers_dict = {}
with open(data_path, 'r') as f:
    followers_dict = json.load(f)

followers_over_time = dict_to_ordereddict(followers_dict)
last_index = next(reversed(followers_over_time))
print("removing index: {}".format(last_index))
followers_dict.pop(last_index)

with open(data_path, 'w') as f:
    json.dump(followers_dict, f)
