"""
TODO:
1. DONE: verify that you can re-create followers.json from by_followers.json OR new_followers.json
2. DONE: switch this to load those two files
2a. DONE: new_followers.json just need the most recent checkpoint (for comparison)
2b. DONE: by_followers.json to track when people joined and left
3. decide if it is better to switch
3a. DONE: time each (can use the checkpoints in followers.json to test different scenarios, potentially)
3b. DONE: write a script to run both and store the timings in a separate file (use logger?)
4. make new_followers smaller? the checkpoints don't seem necessary. Can I increase the space between them or just drop them all together?
"""

import os
import twitter
import argparse
import json
import csv
import logging
import datetime
import dateutil.parser
from utils import diff_two_id_sets, oauth_and_get_twitter, test_valid_loading, status_date
import sys
from usercache import TwitterUserCache
from prettytable import PrettyTable

DATA_DIR = 'data'
FOLLOWERS_DATA_FILE = 'new_followers.json'
BY_FOLLOWERS_DATA_FILE = 'by_followers.json'
FOLLOWER_COUNT_FILE = 'new_follower_count.csv'
LOG_FILE = 'followers-v2.log'

console_log_level = logging.INFO
logfile_log_level = logging.INFO

now = datetime.datetime.now(dateutil.tz.tzutc())

#when run as a script, do initialization
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Track twitter follower changes since last run.')
    parser.add_argument('--verbose', '-v', action='store_true', dest='verbose')
    parser.add_argument('--verbose_log', '-V', action='store_true', dest='verbose_log')
    ns = parser.parse_args()
    if ns.verbose:
        console_log_level = logging.DEBUG
    if ns.verbose_log:
        logfile_log_level = logging.DEBUG

# Set up logging
logger = logging.getLogger('track_followers_v2')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s - %(asctime)s (%(levelname)s): %(message)s')
formatter.datefmt = '%Y-%m-%d %H:%M:%S %z'
ch = logging.StreamHandler()
ch.setLevel(console_log_level)
ch.setFormatter(formatter)
logger.addHandler(ch)
fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logfile_log_level)
fh.setFormatter(formatter)
logger.addHandler(fh)

t = oauth_and_get_twitter()

followers_checkpoints = []
by_followers = {}
follower_count = []

try:
    logger.debug('loading: %s', FOLLOWERS_DATA_FILE)
    with open(os.path.join(DATA_DIR, FOLLOWERS_DATA_FILE), 'r') as f:
        followers_checkpoints = json.load(f)
    logger.info('%s: %d entries', FOLLOWERS_DATA_FILE, len(followers_checkpoints))
    
    logger.debug('loading: %s', BY_FOLLOWERS_DATA_FILE)
    with open(os.path.join(DATA_DIR, BY_FOLLOWERS_DATA_FILE), 'r') as f:
        by_followers = json.load(f)
    logger.info('%s: %d entries', BY_FOLLOWERS_DATA_FILE, len(by_followers.items()))
    
    logger.debug('loading follower count file')
    with open(os.path.join(DATA_DIR, FOLLOWER_COUNT_FILE), 'r') as f:
        reader = csv.DictReader(f, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        for row in reader:
            for key, value in row.items():
                if isinstance(value, float):
                    row[key] = int(value)
            follower_count.append(row)
    logger.info('%s: %d entries', FOLLOWER_COUNT_FILE, len(follower_count))
except Exception as e:
    logger.exception(e)

test_valid_loading([(FOLLOWERS_DATA_FILE, followers_checkpoints), (BY_FOLLOWERS_DATA_FILE, by_followers), (FOLLOWER_COUNT_FILE, follower_count)])

followers_ids = t.followers.ids()['ids']
logger.info('follower count: %d', len(followers_ids))
last_follower_checkpoint = followers_checkpoints[-1]
if not 'follower_id_list' in last_follower_checkpoint:
    logger.critical('missing follower_id_list in last checkpoint, exiting')
    sys.exit(1)

new_followers, lost_followers = diff_two_id_sets(last_follower_checkpoint['follower_id_list'], followers_ids)

now_iso = now.isoformat()

# update checkpoints
logger.info('updating checkpoints')
new_checkppoint = { 'iso_time': now_iso, 'follower_id_list': followers_ids }
if new_followers:
    new_checkppoint['new_followers'] = new_followers
if lost_followers:
    new_checkppoint['lost_followers'] = lost_followers
del last_follower_checkpoint['follower_id_list']
followers_checkpoints.append(new_checkppoint)

# update by_followers
logger.info('updating by_followers')
for id in lost_followers:
    entry = by_followers[str(id)]
    if not 'unfollow' in entry:
        entry['unfollow'] = [now_iso]
    else:
        entry['unfollow'].append(now_iso)
for id in new_followers:
    if str(id) in by_followers:
        by_followers[str(id)]['follow'].append(now_iso)
    else:
        by_followers[str(id)] = { 'follow': [now_iso] }

# update counts
logger.info('updating_counts')
new_count = { 'iso_time': now_iso, 'followers': len(followers_ids), 'added': len(new_followers), 'lost': len(lost_followers) }
follower_count.append(new_count)

#write out files

logger.debug('saving %s', FOLLOWERS_DATA_FILE)
with open(os.path.join(DATA_DIR, FOLLOWERS_DATA_FILE), 'w') as f:
    json.dump(followers_checkpoints, f)

logger.debug('saving: %s', BY_FOLLOWERS_DATA_FILE)
with open(os.path.join(DATA_DIR, BY_FOLLOWERS_DATA_FILE), 'w') as f:
    json.dump(by_followers, f)

logger.debug('saving: %s', FOLLOWER_COUNT_FILE)
with open(os.path.join(DATA_DIR, FOLLOWER_COUNT_FILE), 'w', newline='') as f:
    fieldnames = ['iso_time', 'followers', 'added', 'lost']
    writer = csv.DictWriter(f, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    writer.writeheader()
    writer.writerows(follower_count)

#output to the user
user_cache = TwitterUserCache(t, root_logger_name=logger.name)
# print out new followers
if new_followers:
    users_data = user_cache.get_users_data(new_followers)
    pl = [[p['screen_name'], p['name'], status_date(p), p['following']] for p in users_data]
    pt = PrettyTable(field_names=['screen_name', 'name', 'last_post', 'following'])
    pt.align['screen_name'], pt.align['name'], pt.align['last_post'], pt.align['following'] = 'l', 'l', 'l', 'l'
    [pt.add_row(p) for p in pl]
    logger.info('\nNew Followers:\n' + pt.get_string())

if lost_followers:
    def get_when_last_started_follow(id, by_followers):
        return dateutil.parser.parse(by_followers[str(id)]['follow'][-1]).strftime('%Y-%m-%d')
    users_data = user_cache.get_users_data(lost_followers)
    pl = [[p['screen_name'], p['name'], status_date(p), p['following'], get_when_last_started_follow(p['id'], by_followers)] for p in users_data]
    pt = PrettyTable(field_names=['screen_name', 'name', 'last_post', 'following', 'since'])
    pt.align['screen_name'], pt.align['name'], pt.align['last_post'], pt.align['following'], pt.align['since'] = 'l', 'l', 'l', 'l', 'l'
    [pt.add_row(p) for p in pl]
    logger.info('\nLost Followers:\n'+pt.get_string())

finish_time = datetime.datetime.now(dateutil.tz.tzutc())
execution_time = finish_time - now
logger.info('execution in %d micro-seconds.', execution_time.microseconds)
