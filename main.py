import subprocess
import praw
import datetime
import pyperclip
from hashlib import sha1
from flask import Flask
from flask import Response
from flask import request
from cStringIO import StringIO
from base64 import b64encode
from base64 import b64decode
from ConfigParser import ConfigParser
import OAuth2Util
import os
import markdown
import bleach
# encoding=utf8
import sys

reload(sys)
sys.setdefaultencoding('utf8')

subredditName = 'opensource'

# def loginOAuthAndReturnRedditSession():
#     redditSession = praw.Reddit(user_agent='Test Script by /u/foobarbazblarg')
#     o = OAuth2Util.OAuth2Util(redditSession, print_log=True, configfile="./reddit-oauth-credentials.cfg")
#     # TODO:  Testing comment of refresh.  We authenticate fresh every time, so presumably no need to do o.refresh().
#     # o.refresh(force=True)
#     return redditSession
#
# redditSession = loginOAuthAndReturnRedditSession()

reddit = praw.Reddit(user_agent='subreddit-grabber')
#reddit = praw.Reddit(user_agent='Test Script by /u/foobarbazblarg')
#reddit = loginOAuthAndReturnRedditSession()
for submission in reddit.get_subreddit(subredditName).get_new(limit=5):
    authorName = submission.author.name.encode('utf-8')
    authorCreationTimestamp = int(submission.author.created)
    text = submission.selftext.encode('utf-8')
    timestamp = int(submission.created)
    html = submission.selftext_html.encode('utf-8')
    title = submission.title.encode('utf-8')
    upvotes = submission.ups
    downvotes = submission.downs
    score = submission.score
    url = submission.url
    print 'Title:  ' + title
    print 'Author:  ' + authorName
    print 'Author reddit age at time of posting:  ' + str(timestamp - authorCreationTimestamp)
    print 'Timestamp:  ' + str(timestamp)
    print 'score:  ' + str(score) + ' (' + str(upvotes) + ' up, ' + str(downvotes) + ' dn)'
    print 'URL:  ' + url
    print ''
    print text
    print '======================================================================'
