"""
Test that the generated new follower files match the source of truth 'followers.json' so that
I can be confident about switching to the new format. This assumes that the various files are
up to date for the same date.
"""

import os
import json
import logging
import sys
import errno
import csv
from utils import diff_two_id_sets
import datetime

DATA_DIR = 'data'
OLD_FOLLOWERS_FILE = 'followers.json'
NEW_FOLLOWERS_FILE = 'new_followers.json'
NEW_BY_FOLLOWERS_FILE = 'by_followers.json'
FOLLOWER_COUNT_FILE = 'new_follower_count.csv'
LOG_FILE = 'test-new-followers.log'

def test_valid_loading(to_test):
    """
    test_valid_loading:
        Assuming a list of tuples of (filename, object), checks if object valid, if not logs and exits
    """
    for item in to_test:
        if not item[1]:
            logger = logging.getLogger('test-new-followers-format.test_valid_loading')
            logger.critical('%s file not loaded', item[0])
            sys.exit(errno.ENOENT)


# Set up logging
logger = logging.getLogger('test-new-followers-format')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s - %(asctime)s (%(levelname)s): %(message)s')
formatter.datefmt = '%Y-%m-%d %H:%M:%S %z'
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)
fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)

old_followers_dict = []
new_followers_list = []
follower_count = []
by_followers_dict = {}

try:
    logger.debug('loading old followers file')
    with open(os.path.join(DATA_DIR, OLD_FOLLOWERS_FILE), 'r') as f:
        old_followers_dict = json.load(f)
    logger.info('%s: %d entries', OLD_FOLLOWERS_FILE, len(old_followers_dict.items()))
    
    logger.debug('loading new followers file')
    with open(os.path.join(DATA_DIR, NEW_FOLLOWERS_FILE), 'r') as f:
        new_followers_list = json.load(f)
    logger.info('%s: %d entries', NEW_FOLLOWERS_FILE, len(new_followers_list))
    
    logger.debug('loading by followers file')
    with open(os.path.join(DATA_DIR, NEW_BY_FOLLOWERS_FILE), 'r') as f:
        by_followers_dict = json.load(f)
    logger.info('%s: %d entries', NEW_BY_FOLLOWERS_FILE, len(by_followers_dict.items()))
    
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

test_valid_loading([(OLD_FOLLOWERS_FILE, old_followers_dict), (NEW_FOLLOWERS_FILE, new_followers_list), (NEW_BY_FOLLOWERS_FILE, by_followers_dict), (FOLLOWER_COUNT_FILE, follower_count)])

# test if the dates that have the full lists are the same (they should be identical)
logger.debug('testing for snapshot equality')
count = 0
for item in new_followers_list:
    if 'follower_id_list' in item:
        count += 1
        if item['follower_id_list'] != old_followers_dict[item['iso_time']]:
            logger.critical('saved id set is inccorect for %s', item['iso_time'])
if count == 0:
    logger.critical('no checkpoints in loaded file')
else:
    logger.debug('found %d checkpoints', count)

# reconstruct with new_followers_list
logger.info('Reconstructing follower_dict from new_followers')
reconstructed_follower_dict={}
follower_id_list = []
for item in new_followers_list:
    logger.debug('reconstructing %s', item['iso_time'])
    if 'follower_id_list' in item:
        logger.debug('follower_id_list in %s', item['iso_time'])
        follower_id_list = item['follower_id_list'].copy()
    else:
        if 'new_followers' in item:
            logger.debug('new followers in %s', item['iso_time'])
            follower_id_list.extend(item['new_followers'])
        if 'lost_followers' in item:
            logger.debug('lost followers in %s', item['iso_time'])
            for lost in item['lost_followers']:
                follower_id_list.remove(lost)
    reconstructed_follower_dict[item['iso_time']] = follower_id_list.copy()

# test the reconstruction on snapshots
logger.debug('testing snapshots')
count = 0
for item in new_followers_list:
    if 'follower_id_list' in item:
        count += 1
        if item['follower_id_list'] != reconstructed_follower_dict[item['iso_time']]:
            logger.critical('reconstructed id set is different than snapshot %s', item['iso_time'])
        if item['follower_id_list'] != old_followers_dict[item['iso_time']]:
            logger.critical('saved id set is inccorect for %s', item['iso_time'])

if count == 0:
    logger.critical('no checkpoints in loaded file')
logger.debug('tested %d snapshots', count)

if len(reconstructed_follower_dict.items()) != len(old_followers_dict.items()):
    logger.critical('reconstructed follower dictionary from new followers list is incorrect length')

# the follower lists are in different orders, so need to sort them
logger.info('validating reconstruction from %s against %s', NEW_FOLLOWERS_FILE, OLD_FOLLOWERS_FILE)
for key in old_followers_dict:
    old_followers_dict[key].sort()
for key in reconstructed_follower_dict:
    reconstructed_follower_dict[key].sort()

for key in old_followers_dict.keys():
    logger.debug('testing %s', key)
    if not key in reconstructed_follower_dict:
        logger.critical('missing date %s in reconstructed follower dictionary', key)
    else:
        if old_followers_dict[key] != reconstructed_follower_dict[key]:
            logger.critical('follower lists are different for %s', key)
            missing_in_new, missing_from_new = diff_two_id_sets(old_followers_dict[key], reconstructed_follower_dict[key])
            if len(missing_in_new) > 0:
                logger.critical('extra items in reconstructed %s', str(missing_in_new))
            if len(missing_from_new) > 0:
                logger.critical('missing from new: %s', str(missing_from_new))
        else:
            logger.debug('follower lists are identical')

logger.info('reconstructing follower_dict from by_followers')
# this is a bit tougher
# start by getting all the checkpoints
# then fill-in the ids from follow to unfollow
# then handle refollows
# this will miss all checkpoints where the follower list didn't change, so need to ignore those
date_set = set()
for key in by_followers_dict:
    value = by_followers_dict[key]
    if 'follow' in value:
        date_set.update(value['follow'])
    else:
        logger.critical('missing a follow list for %s', key)
    if 'unfollow' in value:
        date_set.update(value['unfollow'])
logger.info('found %d dates', len(date_set))

# easier to compare on datetime than strings for less-than
date_list = list(date_set)
date_list.sort()
checkpoint_list = []
for date in date_list:
    checkpoint_list.append({ 'dt': datetime.datetime.fromisoformat(date), 'key': date, 'ids': [] })

# walk the id list and fill in the id from follow to unfollow
for key in by_followers_dict:
    logger.debug('processing id: %s', key)
    follows = by_followers_dict[key]['follow'].copy()
    unfollows = by_followers_dict[key].get('unfollow', []).copy()
    done = False
    while len(follows):
        start_date = datetime.datetime.fromisoformat(follows.pop(0))
        logger.debug('start: %s', start_date.isoformat())
        if unfollows:
            end_date = datetime.datetime.fromisoformat(unfollows.pop(0))
            logger.debug('end: %s', end_date.isoformat())
        else:
            end_date = None
            logger.debug('no end date')
        for item in checkpoint_list:
            if (item['dt'] >= start_date) and ((not end_date) or (end_date > item['dt'])):
                item['ids'].append(int(key))

# build the reconstructed dictionary
reconstructed_by_followers_dict = {}
for item in checkpoint_list:
    reconstructed_by_followers_dict[item['key']] = sorted(item['ids'])

# validate
logger.info('validating reconstruction from %s', NEW_BY_FOLLOWERS_FILE)
for date_key in reconstructed_by_followers_dict.keys():
    logger.debug('testing %s', date_key)
    if not date_key in old_followers_dict:
        logger.critical('missing date %s in original follower dictionary', date_key)
    else:
        if old_followers_dict[date_key] != reconstructed_by_followers_dict[date_key]:
            logger.critical('follower lists are different for %s', date_key)
            logger.debug('old followers: %d', len(old_followers_dict[date_key]))
            logger.debug('reconstructed followers %d', len(reconstructed_by_followers_dict[date_key]))
            missing_in_new, missing_from_new = diff_two_id_sets(old_followers_dict[date_key], reconstructed_by_followers_dict[date_key])
            if len(missing_in_new) > 0:
                logger.critical('extra items in reconstructed %s', str(missing_in_new))
            if len(missing_from_new) > 0:
                logger.critical('missing from new: %s', str(missing_from_new))
        else:
            logger.debug('follower lists are identical')
