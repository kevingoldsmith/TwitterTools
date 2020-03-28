import os
import twitter
import dateutil.parser
import datetime
import textwrap
import json
import utils


DATA_DIR = 'data'

#when run as a script, do initialization
if __name__ == "__main__":
    pass

t = utils.oauth_and_get_twitter()

#get the first 200 tweets
tweets = []

cur_tweets = t.statuses.user_timeline(count=200, exclude_replies=0, contributor_details=1, include_rts=1)

while len(cur_tweets) > 0:
    tweets.extend(cur_tweets)
    last_id = cur_tweets[-1]['id']
    print('start-date: {0}, end-date: {1}, cur_tweets: {2}, tweets: {3}'.format(dateutil.parser.parse(cur_tweets[0]['created_at']), dateutil.parser.parse(cur_tweets[-1]['created_at']), len(cur_tweets), len(tweets)))
    cur_tweets = t.statuses.user_timeline(count=200, exclude_replies=0, contributor_details=1, include_rts=1, max_id=last_id-1)

tweets_by_year_and_month = {}
for tweet in tweets:
    created_date = dateutil.parser.parse(tweet['created_at'])
    if not created_date.year in tweets_by_year_and_month:
        tweets_by_year_and_month[created_date.year] = {}
    if created_date.month in tweets_by_year_and_month[created_date.year]:
        tweets_by_year_and_month[created_date.year][created_date.month].append(tweet)
    else:
        tweets_by_year_and_month[created_date.year][created_date.month] = [tweet]

for year in tweets_by_year_and_month:
    for month in tweets_by_year_and_month[year]:
        sorted_tweets = sorted(tweets_by_year_and_month[year][month], key=lambda i: i['created_at'])
        print("saving tweets for {0}-{1}".format(year, month))
        utils.dump_to_monthly_json_file(DATA_DIR, year, month, sorted_tweets)
