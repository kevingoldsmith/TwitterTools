import os
import twitter
import dateutil.parser
import datetime
import textwrap
import json
import utils
import configparser
import boto3


DATA_DIR = 'data'
AWS_CONFIG = 'aws-config.ini'

def load_tweets(file):
    with open(file, 'r') as f:
        return json.load(f)


def get_sentiments(tweets, client):
    sentiment_list = []
    # break into chunks of 25
    n = 25
    batch_list = [tweets[i * n:(i + 1) * n] for i in range((len(tweets) + n - 1) // n )]
    for batch in batch_list:
        tweet_texts = [tweet['text'] for tweet in batch]
        sentiments=client.batch_detect_sentiment(TextList=tweet_texts, LanguageCode='en')
        for sentiment in sentiments['ResultList']:
            sentiment_list.append({'tweet_id': batch[sentiment['Index']]['id'], 'text': batch[sentiment['Index']]['text'], 'sentiment': sentiment})
    return sentiment_list


config_parser = configparser.ConfigParser()
config_parser.read(AWS_CONFIG)
if len(config_parser) == 0:
    print("ERROR: no config file loaded")
    exit(1)

aws_access_key_id = config_parser.get('AWS Parameters', 'access_key_id')
aws_secret_access_key = config_parser.get('AWS Parameters', 'secret_access_key')

client = boto3.client('comprehend', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)


#when run as a script, do initialization
if __name__ == "__main__":
    pass

# walk the data directory looking for missing sentiment files
# find the subdirectoriea
subdirs = os.listdir(DATA_DIR)
iter = filter(lambda file: os.path.isdir(os.path.join(DATA_DIR, file)), subdirs)
subdirs = list(iter)

for dir in sorted(subdirs):
    for month in range(1,13):
        file = os.path.join(DATA_DIR, dir, '{0}-{1}.json'.format(dir, str(month)))
        sentiment_file = os.path.join(DATA_DIR, dir, 'sentiments_{}-{:0>2d}.json'.format(dir, month))
        if os.path.exists(file) and not os.path.exists(sentiment_file):
            print('missing: {}'.format(sentiment_file))
            tweets = load_tweets(file)
            sentiments = get_sentiments(tweets, client)
            utils.dump_to_monthly_json_file(DATA_DIR, dir, month, sentiments, datatype='sentiments')
