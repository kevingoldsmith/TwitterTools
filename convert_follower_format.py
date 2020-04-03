import os
import json
import csv
from collections import OrderedDict
from utils import diff_two_id_sets, dict_to_ordereddict


DATA_DIR = 'data'
DATA_FILE = 'followers.json'

data_path = os.path.join(DATA_DIR, DATA_FILE)

# New JSON file format
# [{
#     iso_time: ''
#     follower_id_list: []
#     new_followers: []
#     lost_followers: []
# }, ....]

# CSV Format
# [{
#     iso_time: ''
#     followers: 0
#     added: 0
#     lost: 0
# }, ...]



try:
    with open(data_path, 'r') as f:
        followers_dict = json.load(f)
        followers_over_time = dict_to_ordereddict(followers_dict)

        new_follower_list = []
        follower_count_list = []
        last_item = None
        count = 0

        for item in followers_over_time.items():
            follower_item = {'iso_time': item[0]}
            follower_count_item = {'iso_time': item[0], 'followers': len(item[1])}
            if not last_item is None:
                new_ids, lost_ids = diff_two_id_sets(last_item[1], item[1])
                if count > 24:
                    follower_item['follower_id_list'] = item[1]
                    count = 0
                else:
                    count += 1
                follower_count_item['added'] = len(new_ids)
                follower_count_item['lost'] = len(lost_ids)
                if len(new_ids) > 0:
                    follower_item['new_followers'] = new_ids
                if len(lost_ids) > 0:
                    follower_item['lost_follers'] = lost_ids
            else:
                follower_item['follower_id_list'] = item[1]
                follower_count_item['added'] = 0
                follower_count_item['lost'] = 0

            new_follower_list.append(follower_item)
            follower_count_list.append(follower_count_item)
            last_item = item
        
        with open(os.path.join(DATA_DIR, 'new_followers.json'), 'w') as f:
            json.dump(new_follower_list, f, indent=2)
        
        with open(os.path.join(DATA_DIR, 'new_follower_count.csv'), 'w', newline='') as f:
            fieldnames = ['iso_time', 'followers', 'added', 'lost']
            writer = csv.DictWriter(f, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            writer.writerows(follower_count_list)

except IOError:
    pass

