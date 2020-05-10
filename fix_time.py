import json
import os

DATA_DIR = 'data'

old_followers = {}
new_followers = []

with open(os.path.join(DATA_DIR, 'followers.json'), 'r') as f:
    old_followers = json.load(f)

with open(os.path.join(DATA_DIR, 'new_followers.json'), 'r') as f:
    new_followers = json.load(f)

last_old_key = sorted(old_followers.keys())[-1]
last_new_key = new_followers[-1]['iso_time']
print(f'last key from old followers {last_old_key}')
print(f'last key from new followers {last_new_key}')

old_followers[last_new_key] = old_followers[last_old_key].copy()
del old_followers[last_old_key]

with open(os.path.join(DATA_DIR, 'followers.json'), 'w') as f:
    json.dump(old_followers, f)

with open(os.path.join(DATA_DIR, 'new_followers.json'), 'w') as f:
    json.dump(new_followers, f)
