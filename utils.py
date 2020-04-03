
import configparser
import twitter
import os
import json
import time
import datetime
import dateutil.relativedelta
from collections import OrderedDict

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


def dump_to_monthly_json_file(data_directory, year, month, data, datatype=''):
    directory = os.path.join(data_directory, str(year))
    if not os.path.isdir(directory):
        os.makedirs(directory)
    if len(datatype) > 0:
        datatype = '{}_'.format(datatype)
    with open('{}/{}{}-{:0>2d}.json'.format(directory, datatype, year, month), "w") as f:
        f.write(json.dumps(data, indent=2))
    time.sleep(1)


def find_newest_saved_month(data_directory, end_year):
    check_date = datetime.datetime.now()
    done = False

    if os.path.isdir(data_directory):
        while not done:
            if os.path.isdir(os.path.join(data_directory, str(check_date.year))):
                if os.path.exists(os.path.join(data_directory, str(check_date.year), '%i-%i.json' % (check_date.year, check_date.month))):
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


def diff_two_id_sets(followers1, followers2):
    s = set(followers1)
    new_follower_ids = [x for x in followers2 if x not in s]

    s = set(followers2)
    lost_follower_ids = [x for x in followers1 if x not in s]

    return new_follower_ids, lost_follower_ids

