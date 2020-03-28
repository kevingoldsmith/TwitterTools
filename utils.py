
import configparser
import twitter
import os
import json
import time

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

def dump_to_monthly_json_file(data_directory, year, month, data):
    directory = "%s/%i" % (data_directory, year)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open("%s/%i-%i.json" % (directory, year, month), "w") as f:
        f.write(json.dumps(data, indent=2))
    time.sleep(1)
