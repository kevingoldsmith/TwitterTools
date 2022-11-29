cp data/followers.json data/followers-backup.json
cp data/new_followers.json data/new_followers-backup.json
cp data/new_follower_count.csv data/new_follower_count-backup.json
cp data/by_followers.json data/by_followers-backup.json
echo "track-followers.py" >> testout.log
(time python track-followers.py) >> testout.log 2>&1
echo "track-followers_v2.py" >> testout.log
(time python track_followers_v2.py) >> testout.log 2>&1
echo "fix_time.py" >> testout.log
(python fix_time.py) >> testout.log 2>&1
echo "test_new_followers_format.py" >> testout.log
(python test_new_followers_format.py) >> testout.log 2>&1
tail -n 100 testout.log