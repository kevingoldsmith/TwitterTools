
import configparser
import twitter
import os
import json
import time
import datetime
import dateutil.relativedelta
from collections import OrderedDict
import urllib.request
import re
import logging
import sys
import errno

CONFIG_FILE = 'config.ini'

def oauth_and_get_twitter():
    config_parser = configparser.ConfigParser()
    config_parser.read(CONFIG_FILE)
    if len(config_parser) == 0:
        print("ERROR: no config file loaded")
        exit(1)

    app_name = config_parser.get('Login Parameters', 'app_name')
    api_key = config_parser.get('Login Parameters', 'api_key')
    api_secret = config_parser.get('Login Parameters', 'api_secret')
    oauth_token = config_parser.get('Login Parameters', 'oauth_token', fallback='')
    oauth_secret = config_parser.get('Login Parameters', 'oauth_secret', fallback='')

    if oauth_token == '' or oauth_secret == '':
        oauth_token, oauth_secret = twitter.oauth_dance(app_name, api_key, api_secret)
        config_parser['Login Parameters']['oauth_token'] = oauth_token
        config_parser['Login Parameters']['oauth_secret'] = oauth_secret
        with open(CONFIG_FILE, 'w') as configfile:
            config_parser.write(configfile)

    t = twitter.Twitter(auth=twitter.OAuth(oauth_token, oauth_secret, api_key, api_secret))
    return t


def format_monthly_json_filename(year, month, datatype=''):
    datatype_str = ''
    if len(datatype) > 0:
        datatype_str = f'{datatype}_'
    return f'{datatype_str}{year}-{month:02}.json'


def dump_to_monthly_json_file(data_directory, year, month, data, datatype=''):
    directory = os.path.join(data_directory, str(year))
    if not os.path.isdir(directory):
        os.makedirs(directory)
    filename = os.path.join(directory, format_monthly_json_filename(year,month,datatype))
    with open(filename, "w") as f:
        f.write(json.dumps(data, indent=2))
    time.sleep(1)


def find_newest_saved_month(data_directory, end_year, datatype=''):
    check_date = datetime.datetime.now()
    done = False

    if os.path.isdir(data_directory):
        while not done:
            if os.path.isdir(os.path.join(data_directory, str(check_date.year))):
                if os.path.exists(os.path.join(data_directory, str(check_date.year), format_monthly_json_filename(check_date.year, check_date.month, datatype))):
                    return check_date.year, check_date.month
            check_date = check_date - dateutil.relativedelta.relativedelta(months=1)
            if check_date.year <= end_year:
                done = True
    
    return None, None


def dict_to_ordereddict(unordered_dict):
    sorted_keys = sorted(unordered_dict.keys())
    ordered_dict = OrderedDict()
    for key in sorted_keys:
        ordered_dict[key] = unordered_dict[key]
    return ordered_dict


def diff_two_id_sets(old_ids_input, new_ids_input):
    s = set(old_ids_input)
    new_ids = [x for x in new_ids_input if x not in s]

    s = set(new_ids_input)
    lost_ids = [x for x in old_ids_input if x not in s]

    return new_ids, lost_ids


def get_user_ids_of_post_likes(post_id):
    try:
        json_data = urllib.request.urlopen('https://twitter.com/i/activity/favorited_popup?id=' + str(post_id)).read()
        found_ids = re.findall(r'data-user-id=\\"+\d+', json_data.decode("utf-8"))
        unique_ids = list(set([re.findall(r'\d+', match)[0] for match in found_ids]))
        return unique_ids
    except urllib.request.HTTPError:
        return False


def copy_dict_items(item_list, dict_from, dict_to):
    for item in item_list:
        dict_to[item] = dict_from.get(item, None)


def logmsg(msg):
    time = datetime.datetime.now()
    print("[%04i/%02i/%02i %02i:%02i:%02i]: %s" % (time.year, time.month, time.day, time.hour, time.minute, time.second, msg))


def test_valid_loading(to_test):
    """
    test_valid_loading:
        Assuming a list of tuples of (filename, object), checks if object valid, if not logs and exits
    """
    for item in to_test:
        if not item[1]:
            logger = logging.getLogger('utils.test_valid_loading')
            logger.critical('%s file not loaded', item[0])
            sys.exit(errno.ENOENT)

def status_date(user):
    if user and ('status' in user) and user['status'] and ('created_at' in user['status']):
        lastpostdate = dateutil.parser.parse(user['status']['created_at'])
        now = datetime.datetime.now(dateutil.tz.tzutc())
        datediff = datetime.datetime(now.year, now.month, now.day) - datetime.datetime(lastpostdate.year, lastpostdate.month, lastpostdate.day)
        return datediff.days
    else:
        return 'none'
