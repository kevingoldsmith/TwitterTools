"""
TODO:
1. verify that you can re-create followers.json from by_followers.json OR new_followers.json
2. switch this to load those two files
2a. new_followers.json just need the most recent checkpoint (for comparison)
2b. by_followers.json to track when people joined and left
3. decide if it is better to switch
3a. time each (can use the checkpoints in followers.json to test different scenarios, potentially)
3b. write a script to run both and store the timings in a separate file (use logger?)
"""

import os
import twitter
import argparse
import json
from utils import diff_two_id_sets, oauth_and_get_twitter

DATA_DIR = 'data'
DATA_FILE = 'followers.json'
LOG_FILE = 'followers.log'
