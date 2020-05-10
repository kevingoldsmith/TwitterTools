(time python track-followers.py) >> testout.log 2>&1
(time python track_followers_v2.py) >> testout.log 2>&1
(python fix_time.py) >> testout.log 2>&1
(python test_new_followers_format.py) >> testout.log 2>&1