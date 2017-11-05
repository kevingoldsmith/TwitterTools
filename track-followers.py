import os
import twitter
from prettytable import PrettyTable
import dateutil.parser
import datetime
import pickle
from collections import OrderedDict
import textwrap
import argparse


def output_line(line, write_to_stdout=True, file=None):
    if write_to_stdout:
        print line
    if not file is None:
        file.write(line.encode('utf8'))
        file.write('\n')


def get_people_string(people_list):
    def show_date(status):
        if p.get('status'):
            lastpostdate = dateutil.parser.parse(p['status']['created_at'])
            now = datetime.datetime.now(dateutil.tz.tzutc())
            datediff = datetime.datetime(now.year, now.month, now.day) - datetime.datetime(lastpostdate.year, lastpostdate.month, lastpostdate.day)
            return datediff.days
        else:
            return 'none'

    pl = [[p['screen_name'], p['name'], show_date(p), p['following']] for p in people_list]

    pt = PrettyTable(field_names=['screen_name', 'name', 'last_post', 'following'])
    pt.align['screen_name'], pt.align['name'], pt.align['last_post'], pt.align['following'] = 'l', 'l', 'l', 'l'
    [pt.add_row(p) for p in pl]
    return pt.get_string(sortby="last_post", reversesort=True)


def get_lost_people_string(people_list, followers_over_time):
    def show_date(status):
        if p.get('status'):
            lastpostdate = dateutil.parser.parse(p['status']['created_at'])
            now = datetime.datetime.now(dateutil.tz.tzutc())
            datediff = datetime.datetime(now.year, now.month, now.day) - datetime.datetime(lastpostdate.year, lastpostdate.month, lastpostdate.day)
            return datediff.days
        else:
            return 'none'

    pl = [[p['screen_name'], p['name'], show_date(p), p['following'], find_when_friend_started_following_me(p['id'], followers_over_time)] for p in people_list]

    pt = PrettyTable(field_names=['screen_name', 'name', 'last_post', 'following', 'since'])
    pt.align['screen_name'], pt.align['name'], pt.align['last_post'], pt.align['following'], pt.align['since'] = 'l', 'l', 'l', 'l', 'l'
    [pt.add_row(p) for p in pl]
    return pt.get_string(sortby="last_post", reversesort=True)


def get_people_details(id_list):
    people = []
    chunks = [id_list[x:x+100] for x in xrange(0, len(id_list), 100)]
    for chunk in chunks:
        people.extend(t.users.lookup(user_id=','.join(str(x) for x in chunk)))
    return people


def get_tweets_since_time(start_time):
    tweets = t.statuses.user_timeline(count=25)
    return_tweets = [tw for tw in tweets if dateutil.parser.parse(tw['created_at']) > start_time]
    last_tweet = tweets[-1]
    if (dateutil.parser.parse(last_tweet['created_at']) > start_time):
        tweets = t.statuses.user_timeline(count=25, max_id=last_tweet['id']-1)
        return_tweets.extend([tw for tw in tweets if dateutil.parser.parse(tw['created_at']) > start_time])

    return return_tweets


def print_tweet(tweet, write_to_stdout=True, file=None):
    output_line(u'{:=<70}'.format(u''), write_to_stdout, file)
    for l in textwrap.wrap(tweet['text'], width=66):
        output_line(u'= {:<66} ='.format(l), write_to_stdout, file)
    output_line(u'= {:<66} ='.format(u''), write_to_stdout, file)
    output_line(u'= {:<66} ='.format(tweet['created_at']), write_to_stdout, file)
    output_line(u'{:=<70}'.format(u''), write_to_stdout, file)
    output_line(u'\n', write_to_stdout, file)


def diff_two_id_sets(followers1, followers2):
    s = set(followers1)
    new_follower_ids = [x for x in followers2 if x not in s]

    s = set(followers2)
    lost_follower_ids = [x for x in followers1 if x not in s]

    return new_follower_ids, lost_follower_ids


def find_when_friend_started_following_me(friend_id, followers_over_time):
    #check the first item, easy out
    keys = followers_over_time.keys()
    s = set(followers_over_time[keys[0]])
    if friend_id in s:
        return None

    def linear_search():
        for i in range(1, len(keys)):
            s = set(followers_over_time[keys[i]])
            if friend_id in s:
                return keys[i]
        return None

    def binary_search(lo=0, hi=None, found=None):
        if lo == hi:
            if found is not None:
                return keys[found]
            return None
        hi = hi if hi is not None else len(followers_over_time)
        mid = lo+(hi-lo)/2
        s = set(followers_over_time[keys[mid]])
        if friend_id in s:
            return binary_search(lo, mid, mid)

        return binary_search(mid+1, hi, found)

    bin = binary_search()
    if bin is not None:
        return bin

    return linear_search()

write_to_stdout = True
test_mode = False
write_log = True

#when run as a script, do initialization
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Track twitter follower changes since last run.')
    parser.add_argument('--verbose', '-v', action='store_true', dest='verbose')
    parser.add_argument('--test', '-t', action='store_true', dest='test')
    ns = parser.parse_args()
    write_to_stdout = ns.verbose
    test_mode = ns.test

if test_mode:
    write_to_stdout = True
    write_log = False

now = datetime.datetime.now(dateutil.tz.tzutc())

MY_TWITTER_CREDS = os.path.expanduser('~/.my_app_credentials')
CONSUMER_KEY = "8tWGuEOJr7HEC9J6D8SqQ"
CONSUMER_SECRET = "jsiPRnMsham9Ulc3Y95Ld9J0WySvtRy4rpEAqKkbw"
TWITTER_APP_NAME = "dlizer"

if not os.path.exists(MY_TWITTER_CREDS):
    twitter.oauth_dance(TWITTER_APP_NAME, CONSUMER_KEY, CONSUMER_SECRET, MY_TWITTER_CREDS)

oauth_token, oauth_secret = twitter.read_token_file(MY_TWITTER_CREDS)

t = twitter.Twitter(auth=twitter.OAuth(
    oauth_token, oauth_secret, CONSUMER_KEY, CONSUMER_SECRET))

followers_ids = t.followers.ids()['ids']
followers_over_time = OrderedDict()

logfile = None
if write_log:
    logfile = open('followers.log', 'a')

output_line('=======================================================', write_to_stdout, logfile)
output_line('Followers: {0} at {1}'.format(len(followers_ids), now), write_to_stdout, logfile)

try:
    with open('followers.txt', 'r') as f:
        followers_over_time = pickle.load(f)
        followers_last_time = next(reversed(followers_over_time))
        follower_ids_last_time = followers_over_time[followers_last_time]

        s = set(follower_ids_last_time)
        new_follower_ids = [x for x in followers_ids if x not in s]
        if (len(new_follower_ids) > 0):
            output_line('New Followers', write_to_stdout, logfile)
            output_line(get_people_string(get_people_details(new_follower_ids)), write_to_stdout, logfile)

        s = set(followers_ids)
        lost_follower_ids = [x for x in follower_ids_last_time if x not in s]
        if (len(lost_follower_ids) > 0):
            output_line('Lost Followers', write_to_stdout, logfile)
            try:
                output_line(get_lost_people_string(get_people_details(lost_follower_ids), followers_over_time), write_to_stdout, logfile)
            except:
                output_line('error printing lost followers: probably a spammer', write_to_stdout, logfile)
        tweets = get_tweets_since_time(followers_last_time)
        for tw in reversed(tweets):
            print_tweet(tw, write_to_stdout, logfile)

except IOError:
    pass

followers_over_time[now] = followers_ids

if not test_mode:
    with open('followers.txt', 'w') as f:
        pickle.dump(followers_over_time, f)
else:
    output_line('NOTE: output not written to followers.txt', write_to_stdout, logfile)

finish_time = datetime.datetime.now(dateutil.tz.tzutc())
execution_time = finish_time - now
output_line('execution in {0} seconds'.format(execution_time.total_seconds()), write_to_stdout, logfile)

if not logfile is None:
    logfile.flush()
    logfile.close()
