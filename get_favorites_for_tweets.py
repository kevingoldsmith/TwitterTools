import os
import twitter
import json
import utils
import fnmatch
import datetime
from usercache import TwitterUserCache

DATA_DIR = u'data'

#when run as a script, do initialization
if __name__ == "__main__":
    pass

t = utils.oauth_and_get_twitter()
tuc = TwitterUserCache(t)

# REVIEW: this will miss added or removed favorites since the favorites file was updated
for root, dirs, files in os.walk(DATA_DIR):
    for file in fnmatch.filter(files, u'tweets*.json'):
        favorite_path = os.path.join(root, file.replace('tweets', 'favorites'))
        if not os.path.exists(favorite_path):
            favorites = []
            with open(os.path.join(root, file), 'r') as f:
                utils.logmsg(f'loading favorites for {file}')
                tweets = json.load(f)
                for tweet in tweets:
                    if tweet['favorite_count'] > 0:
                        ids = utils.get_user_ids_of_post_likes(tweet['id'])
                        try:
                            # remove me, will still get the retweets user
                            ids.remove('14232465')
                        except ValueError:
                            pass
                        if ids:
                            favoriters = tuc.get_users_data(ids)
                            tweet_favorites = { 'updated_at': datetime.datetime.utcnow().isoformat() }
                            utils.copy_dict_items(['id', 'text', 'favorite_count'], tweet, tweet_favorites)
                            tweet_favorites['favorites'] = favoriters
                            favorites.append(tweet_favorites)
            if len(favorites) > 0:
                with open(favorite_path, 'w') as f:
                    f.write(json.dumps(favorites))
