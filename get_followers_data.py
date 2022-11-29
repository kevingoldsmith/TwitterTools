import argparse
import os
import json
import logging
import datetime
import dateutil.parser
import time

import etlutils.date
from utils import oauth_and_get_twitter, test_valid_loading
from usercache import TwitterUserCache

DATA_DIR = 'data'
FOLLOWERS_DATA_FILE = 'new_followers.json'
LOG_FILE = 'get-followers-data.log'

console_log_level = logging.INFO
logfile_log_level = logging.DEBUG
start_date = None

now = datetime.datetime.now(dateutil.tz.tzutc())

#when run as a script, do initialization
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Track twitter follower changes since last run.')
    parser.add_argument('--verbose', '-v', action='store_true', dest='verbose')
    parser.add_argument('--verbose_log', '-V', action='store_true', dest='verbose_log')
    parser.add_argument('--start', '-s', dest='start_date')
    ns = parser.parse_args()
    if ns.verbose:
        console_log_level = logging.DEBUG
    if ns.verbose_log:
        logfile_log_level = logging.DEBUG
    if ns.start_date:
        start_date = etlutils.date.mkdate(ns.start_date)

# Set up logging
logger = logging.getLogger('get_followers_data')
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

try:
    logger.debug('loading: %s', FOLLOWERS_DATA_FILE)
    with open(os.path.join(DATA_DIR, FOLLOWERS_DATA_FILE), 'r') as f:
        followers_checkpoints = json.load(f)
    logger.debug('%s: %d entries', FOLLOWERS_DATA_FILE, len(followers_checkpoints))
except Exception as e:
    logger.exception(e)

test_valid_loading([(FOLLOWERS_DATA_FILE, followers_checkpoints)])

user_cache = TwitterUserCache(t, root_logger_name=logger.name)

for follower_checkpoint in followers_checkpoints:
    after_start_date = True
    if not start_date is None:
        checkpoint_date = dateutil.parser.parse(follower_checkpoint['iso_time'])
        after_start_date = checkpoint_date.date() >= start_date

    if after_start_date and (('follower_id_list' in follower_checkpoint) or ('new_followers' in follower_checkpoint)):
        logger.debug("getting users data for: %s", follower_checkpoint['iso_time'])
        if 'follower_id_list' in follower_checkpoint:
            ids_to_get = follower_checkpoint['follower_id_list']
        else:
            ids_to_get = follower_checkpoint['new_followers']
        users_data = user_cache.get_users_data(ids_to_get)
        if len(users_data) > 0:
            logger.debug("loaded data for %d users", len(users_data))
            time.sleep(15)

finish_time = datetime.datetime.now(dateutil.tz.tzutc())
execution_time = finish_time - now
logger.info('execution in %d micro-seconds.', execution_time.microseconds)
