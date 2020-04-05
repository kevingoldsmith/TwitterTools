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

# Follower list format (key is follower id)
# {
#     xxxx: {
#       follow: [],
#       unfollow: []
#     }, ...
# ]

# CSV Format
# [{
#     iso_time: ''
#     followers: 0
#     added: 0
#     lost: 0
# }, ...]

def update_follow_dict(follow_dict, date, id_list, added=True):
    key = 'follow'
    if not added:
        key = 'unfollow'
    
    for id in id_list:
        if id in follow_dict:
            if key in follow_dict[id]:
                follow_dict[id][key].append(date)
            else:
                follow_dict[id][key] = [date]
        else:
            follow_dict[id]={ key: [date] }


try:
    with open(data_path, 'r') as f:
        followers_dict = json.load(f)
        print("loaded: {}".format(data_path))
        followers_over_time = dict_to_ordereddict(followers_dict)

        new_follower_list = []
        follower_count_list = []
        follow_dict = {}
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
                    update_follow_dict(follow_dict, item[0], new_ids)
                if len(lost_ids) > 0:
                    follower_item['lost_follers'] = lost_ids
                    update_follow_dict(follow_dict, item[0], lost_ids, False)
            else:
                follower_item['follower_id_list'] = item[1]
                follower_count_item['added'] = 0
                follower_count_item['lost'] = 0
                for id in item[1]:
                    follow_dict[id]={'follow': [item[0]]}

            new_follower_list.append(follower_item)
            follower_count_list.append(follower_count_item)
            last_item = item
        new_follower_list[-1]['follower_id_list'] = last_item[1]
        
        print("writing: {}".format('new_Foolowers.json'))
        with open(os.path.join(DATA_DIR, 'new_followers.json'), 'w') as f:
            json.dump(new_follower_list, f)
        
        print("writing: {}".format('new_follower_count.csv'))
        with open(os.path.join(DATA_DIR, 'new_follower_count.csv'), 'w', newline='') as f:
            fieldnames = ['iso_time', 'followers', 'added', 'lost']
            writer = csv.DictWriter(f, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            writer.writerows(follower_count_list)
        
        print("writing: {}".format('by_followers.json'))
        with open(os.path.join(DATA_DIR, 'by_followers.json'), 'w') as f:
            json.dump(follow_dict, f, indent=2)

except IOError:
    pass

