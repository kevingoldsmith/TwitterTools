import os
import datetime
import json
import logging
import sys
import time

import atexit
import twitter
from utils import copy_dict_items

def _savecache(cache, path):
    with open(path, 'w') as f:
        f.write(json.dumps(cache))

class TwitterUserCache:

    _UPDATE_DAYS = 30
    _SLEEPTIME = 960
    _USER_NOT_FOUND = "USER NOT FOUND"
    _SUSPENDED_USER = "SUSPENDED USER"

    cache = {} # class variable is the right choice here

    def __init__(self, twobj, data_directory='data', root_logger_name=''):
        super().__init__()
        self._twobj = twobj
        logger_name = 'TwitterUserCache'
        if root_logger_name:
            logger_name = root_logger_name + '.' + logger_name
        self._logger = logging.getLogger(logger_name)
        self._data_directory = data_directory
        self._data_path = os.path.join(self._data_directory, 'user_cache.json')
        # load cache from file
        if os.path.exists(self._data_path):
            with open(self._data_path, 'r') as f:
                self.cache = json.load(f)
        self._logger.debug('loaded twitter user cache: %d items', len(self.cache))
        self._clean_cache()
        atexit.register(_savecache, self.cache, self._data_path)
    

    def _clean_cache(self):
        items_to_remove = []
        now = datetime.datetime.utcnow()
        for key in self.cache.keys():
            dt = datetime.datetime.fromisoformat(self.cache[key]['cached_at'])
            cached_time = datetime.datetime.utcnow() - dt
            # why keep cache items 2*longer than when we replace them? maybe useful for deleted accounts?
            if cached_time.days > 2*self._UPDATE_DAYS:
                items_to_remove.append(key)
        self._logger.debug('cleaning twitter user cache: %d to remove', len(items_to_remove))
        for item in items_to_remove:
            del self.cache[item]


    def is_cached(self, twitter_id):
        key = str(twitter_id)
        if not key in self.cache:
            return False

        dt = datetime.datetime.fromisoformat(self.cache[key]['cached_at'])
        cached_time = datetime.datetime.utcnow() - dt
        if cached_time.days > self._UPDATE_DAYS:
            return False

        return True

    
    def add_to_cache(self, twitter_user_data):
        new_user_info = { 'cached_at': datetime.datetime.utcnow().isoformat() }
        copy_dict_items(['id', 'name', 'screen_name', 'description', 'url', 'followers_count', 'created_at', 'statuses_count', 'profile_image_url_https', 'following', 'status'], twitter_user_data, new_user_info)
        self.cache[str(twitter_user_data['id'])] = new_user_info
        return new_user_info


    def get_user_data(self, twitter_id):
        self._logger.debug("get_user_data: %d", twitter_id)
        key = str(twitter_id)
        user_info = {}
        
        if self.is_cached(twitter_id):
            return self.cache[key]

        while True:
            try:
                user_info = self._twobj.users.show(user_id=twitter_id)
                break
            except twitter.TwitterHTTPError as e:
                self._logger.debug("got error code %d", e.e.code)
                if e.e.code == 403 or e.e.code == 404:
                    error_string = self._SUSPENDED_USER if e.e.code == 403 else self._USER_NOT_FOUND
                    user_info = {
                        'id': twitter_id,
                        'name': error_string,
                        'screen_name': error_string,
                        'description': error_string,
                        'url': error_string,
                        'followers_count': 0,
                        'created_at': None,
                        'statuses_count': 0,
                        'profile_image_url_https': None,
                        'following': False,
                        'status': None
                    }
                    break
                elif e.e.code == 429:
                    self._logger.info("too many requests, waiting %i minutes", self._SLEEPTIME/60)
                    time.sleep(self._SLEEPTIME)
                    continue
                else:
                    self._logger.info("TwitterHttpError exception caught", exc_info=e)
                    sys.exit("exception")
            except TimeoutError as te:
                    self._logger.debug("timeout error, sleeping 60 seconds")
                    time.sleep(60)
                    continue

        return self.add_to_cache(user_info)

    def get_users_data(self, twitter_id_list):
        cache_people = []
        lookup_ids = []

        for id in twitter_id_list:
            if self.is_cached(id):
                cache_people.append(self.cache[str(id)])
            else:
                lookup_ids.append(id)
        
        people = []
        retry_people = []
        chunks = [lookup_ids[x:x+100] for x in range(0, len(lookup_ids), 100)]
        for chunk in chunks:
            while True:
                try:
                    self._logger.debug("looking up data for %d ids", len(chunk))
                    people.extend(self._twobj.users.lookup(user_id=','.join(str(x) for x in chunk)))
                    break
                except twitter.TwitterHTTPError as e:
                    self._logger.debug("got error code %d", e.e.code)
                    if e.e.code == 404:
                        self._logger.info("invalid user(s), adding %i people to retry list", len(chunk))
                        retry_people.extend(chunk)
                        break
                    elif e.e.code == 429:
                        self._logger.info("too many requests, waiting %i minutes", self._SLEEPTIME/60)
                        time.sleep(self._SLEEPTIME)
                        continue
                    else:
                        self._logger.info("TwitterHttpError exception caught", exc_info=e)
                        sys.exit("exception")
                except TimeoutError as te:
                    self._logger.debug("timeout error, sleeping 60 seconds")
                    time.sleep(60)
                    continue
        
        for person in people:
            cache_people.append(self.add_to_cache(person))

        self._logger.debug("retrying %d people", len(retry_people))
        for retry_id in retry_people:
            self.get_user_data(retry_id)

        return cache_people
