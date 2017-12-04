#!/usr/bin/python

import argparse

#when run as a script, do initialization
tweet_length = 280
file_name = None
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Break text up suitable for tweetstorms.')
    parser.add_argument('--len', '-l', dest='length', default=280, type=int, help='the length of the output tweets')
    parser.add_argument('filename', help='the input file')
    ns = parser.parse_args()
    file_name = ns.filename
    tweet_length = ns.length

with open(file_name, 'r') as f:
	text = f.read()

# get a list of the sentance endpoints
breakpoints = []
possible_breakpoint = 0
current_tweet_end = tweet_length
while not (current_tweet_end > len(text)):
#this will fail if the sentance and paragraph are both longer than tweet_length, future poblem to fix
	end_of_sentance = text.find('. ', possible_breakpoint+1, current_tweet_end)
	end_of_paragraph = text.find('\n\n', possible_breakpoint+1, current_tweet_end)
	if end_of_paragraph > -1:
		breakpoints.append(end_of_paragraph)
		current_tweet_end = end_of_paragraph + 2 + tweet_length
		possible_breakpoint = end_of_paragraph + 2
	else:
		if end_of_sentance > -1:
			possible_breakpoint = end_of_sentance
		else:
			breakpoints.append(possible_breakpoint+1)
			current_tweet_end = possible_breakpoint+1 + tweet_length

start = 0
tweet = 1
tweet_total = len(breakpoints)+1
for breakpoint in breakpoints:
	print text[start:breakpoint].strip() + ' {0}/{1}'.format(tweet, tweet_total)
	start = breakpoint+1
	tweet += 1
	print

print text[breakpoints[-1]:].strip() + ' {0}/{1}'.format(tweet, tweet_total)
