import os
import twitter
import dateutil.parser
import datetime
import json
import argparse
import utils


DATA_DIR = 'data'


def valid_twitter_year(string):
    value = int(string)
    if (value < 2007) or (value > datetime.datetime.now().year):
        msg = "%r is not a valid tweet year" % string
        raise argparse.ArgumentTypeError(msg)
    return value


def tweet_in_range(tweet, start_date, end_date):
    created_date = dateutil.parser.parse(tweet['created_at'])
    return (created_date >= start_date) and (created_date <= end_date)


#when run as a script, do initialization
year = datetime.datetime.now().year
test_mode = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get all tweets for a certain year.')
    parser.add_argument('--test', '-t', action='store_true', dest='test')
    parser.add_argument('year', nargs=1, type=int, choices=range(2006, datetime.datetime.now().year+1))
    ns = parser.parse_args()
    year = ns.year[0]
    test_mode = ns.test


t = utils.oauth_and_get_twitter()

tweets = []
start_date = datetime.datetime(year-1, 12, 31, tzinfo=dateutil.tz.tzutc())
end_date = datetime.datetime(year+1, 1, 2, tzinfo=dateutil.tz.tzutc())

cur_tweets = t.statuses.user_timeline(count=200, exclude_replies=0, contributor_details=1, include_rts=1)

while len(cur_tweets) > 0:
    tweets.extend([tw for tw in cur_tweets if tweet_in_range(tw, start_date, end_date)])
    last_id = cur_tweets[-1]['id']

    print('start-date: {}'.format(dateutil.parser.parse(cur_tweets[0]['created_at'])))
    print('end-date: {}'.format(dateutil.parser.parse(cur_tweets[-1]['created_at'])))

    if dateutil.parser.parse(cur_tweets[-1]['created_at']) < start_date:
        break

    cur_tweets = t.statuses.user_timeline(count=200, exclude_replies=0, contributor_details=1, include_rts=1, max_id=last_id-1)
    print('cur_tweets: {0}, tweets: {1}'.format(len(cur_tweets), len(tweets)))

with open(os.path.join(DATA_DIR, 'tweetarchive-{}.json'.format(year)), 'w') as f:
    f.write(json.dumps(tweets, indent=2))
