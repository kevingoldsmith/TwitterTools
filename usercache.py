import os
import json
import atexit
import twitter
import datetime
from utils import copy_dict_items

def _savecache(cache, path):
    with open(path, 'w') as f:
        f.write(json.dumps(cache))

class TwitterUserCache:

    cache = {} # class variable is the right choice here

    def __init__(self, twobj, data_directory='data'):
        super().__init__()
        self._twobj = twobj
        self._data_directory = data_directory
        self._data_path = os.path.join(self._data_directory, 'user_cache.json')
        # load cache from file
        if os.path.exists(self._data_path):
            with open(self._data_path, 'r') as f:
                self.cache = json.load(f)
        atexit.register(_savecache, self.cache, self._data_path)
    

    def is_cached(self, twitter_id):
        key = str(twitter_id)
        if not key in self.cache:
            return False

        dt = datetime.datetime.fromisoformat(self.cache[key]['cached_at'])
        cached_time = datetime.datetime.utcnow() - dt
        if cached_time.days > 30:
            return False

        return True


    def get_user_data(self, twitter_id):
        key = str(twitter_id)
        
        # have cached id
        if self.is_cached(twitter_id):
            return self.cache[key]

        user_info = self._twobj.users.show(user_id=twitter_id)
        new_user_info = { 'cached_at': datetime.datetime.utcnow().isoformat() }
        copy_dict_items(['id', 'name', 'screen_name', 'description', 'url', 'followers_count', 'created_at', 'statuses_count'], user_info, new_user_info)
        self.cache[key] = new_user_info
        
        # need to cache ID
        return self.cache[key]


    def get_users_data(self, twitter_id_list):
        cache_people = []
        lookup_ids = []

        for id in twitter_id_list:
            if self.is_cached(id):
                cache_people.append(self.cache[str(id)])
            else:
                lookup_ids.append(id)
        
        people = []
        chunks = [lookup_ids[x:x+100] for x in range(0, len(lookup_ids), 100)]
        for chunk in chunks:
            people.extend(self._twobj.users.lookup(user_id=','.join(str(x) for x in chunk)))
        
        for person in people:
            new_user_info = { 'cached_at': datetime.datetime.utcnow().isoformat() }
            copy_dict_items(['id', 'name', 'screen_name', 'description', 'url', 'followers_count', 'created_at', 'statuses_count'], person, new_user_info)
            self.cache[person['id']]=new_user_info
            cache_people.append(new_user_info)

        return cache_people
