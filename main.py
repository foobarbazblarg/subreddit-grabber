import praw
import datetime
from ConfigParser import ConfigParser
import OAuth2Util
import os
import markdown
import bleach
import sys
import mysql.connector
from mysql.connector import errorcode

reload(sys)
sys.setdefaultencoding('utf8')

config = ConfigParser()
config.read("./subreddit-grabber.cfg")
subredditName = config.get("subreddit-grabber", "subredditName")
mysqlUser = config.get("subreddit-grabber", "mysqlUser")
mysqlPassword = config.get("subreddit-grabber", "mysqlPassword")
mysqlDatabaseName = config.get("subreddit-grabber", "mysqlDatabaseName")
textFileName = config.get("subreddit-grabber", "textFileName")

def createDatabase():
    print("Creating database " + mysqlDatabaseName)
    cnx = mysql.connector.connect(user=mysqlUser, password=mysqlPassword, host='127.0.0.1')
    cursor = cnx.cursor()
    try:
        cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(mysqlDatabaseName))
        print "Successfully created database."
        return True
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        return False

def getMysqlConnection():
    try:
        return mysql.connector.connect(user=mysqlUser, password=mysqlPassword, host='127.0.0.1', database=mysqlDatabaseName)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your mysql user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            if createDatabase():
                return getMysqlConnection()
        else:
            print(err)
        return None

def createNewTextFile():
    with open(textFileName, "w") as f:
        pass

def createNewTable(connection):
    tableDropStatement = 'DROP TABLE `submissions`'
    tableCreateStatement = (
        "CREATE TABLE `submissions` ("
        "  `id` int NOT NULL AUTO_INCREMENT,"
        "  `title` text,"
        "  `authorName` text,"
        "  `authorCreationDate` date,"
        "  `authorRedditAgeAtTimeOfPosting` int,"
        "  `timestamp` TIMESTAMP,"
        "  `score` int,"
        "  `upvotes` int,"
        "  `downvotes` int,"
        "  `url` text,"
        "  `text` mediumtext,"
        "  `html` mediumtext,"
        "  PRIMARY KEY (`id`)"
        ") ENGINE=InnoDB")
    try:
        connection.cursor().execute(tableDropStatement)
    except mysql.connector.errors.ProgrammingError:
        pass
    connection.cursor().execute(tableCreateStatement)

def insertRow(connection, title='', authorName='', authorCreationDate=None, authorRedditAgeAtTimeOfPosting=0, timestamp=None, score=0, upvotes=0, downvotes=0, url='', text='', html=''):
    cursor = connection.cursor()
    datetimeFormat = '%Y-%m-%d %H:%M:%S'
    insertStatement = ("INSERT INTO submissions "
               "(title, authorName, authorCreationDate, authorRedditAgeAtTimeOfPosting, timestamp, score, upvotes, downvotes, url, text, html) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    insertData = (title, authorName, authorCreationDate.strftime(datetimeFormat), authorRedditAgeAtTimeOfPosting / 60 / 60 / 24, timestamp.strftime(datetimeFormat), score, upvotes, downvotes, url, text, html)
    cursor.execute(insertStatement, insertData)
    connection.commit()
    cursor.close()

def printAndSaveToTextFile(aString):
    print aString
    with open(textFileName, "a") as f:
        f.write(aString + '\n')

mysqlConnection = getMysqlConnection()
if not mysqlConnection:
    exit()
createNewTable(mysqlConnection)
createNewTextFile()

# def loginOAuthAndReturnRedditSession():
#     redditSession = praw.Reddit(user_agent='Test Script by /u/foobarbazblarg')
#     o = OAuth2Util.OAuth2Util(redditSession, print_log=True, configfile="./reddit-oauth-credentials.cfg")
#     # TODO:  Testing comment of refresh.  We authenticate fresh every time, so presumably no need to do o.refresh().
#     # o.refresh(force=True)
#     return redditSession
#
# redditSession = loginOAuthAndReturnRedditSession()

reddit = praw.Reddit(user_agent='subreddit-grabber')
#reddit = loginOAuthAndReturnRedditSession()

# By using get_new(limit=None), a max of 1000 submissions are answered.  Grrr...
# for submission in reddit.get_subreddit(subredditName).get_new(limit=None):
for submission in praw.helpers.submissions_between(reddit, subredditName, lowest_timestamp=None, highest_timestamp=None, newest_first=True):
    try:
        if submission.author:
            authorName = submission.author.name.encode('utf-8')
            authorCreationDate = datetime.datetime.utcfromtimestamp(submission.author.created_utc)
            authorRedditAgeAtTimeOfPosting = int(submission.created_utc - submission.author.created_utc)
        else:
            authorName = '[deleted]'
            authorCreationDate = datetime.datetime.now()
            authorRedditAgeAtTimeOfPosting = 0
        text = submission.selftext
        if text is not None:
            text = text.encode('utf-8')
        timestamp = datetime.datetime.utcfromtimestamp(submission.created_utc)
        html = submission.selftext_html
        if html is not None:
            html = html.encode('utf-8')
        title = submission.title.encode('utf-8')
        upvotes = submission.ups
        downvotes = submission.downs
        score = submission.score
        url = submission.url
        printAndSaveToTextFile('Title:  ' + title)
        printAndSaveToTextFile('Timestamp:  ' + str(timestamp))
        printAndSaveToTextFile('Author:  ' + authorName)
        printAndSaveToTextFile('Author created:  ' + str(authorCreationDate))
        printAndSaveToTextFile('Author reddit age at time of posting:  ' + str(authorRedditAgeAtTimeOfPosting / 60 / 60 / 24))
        printAndSaveToTextFile('score:  ' + str(score) + ' (' + str(upvotes) + ' up, ' + str(downvotes) + ' dn)')
        printAndSaveToTextFile('URL:  ' + url)
        printAndSaveToTextFile('')
        printAndSaveToTextFile(text)
        printAndSaveToTextFile('======================================================================')
        insertRow(mysqlConnection, title=title, authorName=authorName, authorCreationDate=authorCreationDate, authorRedditAgeAtTimeOfPosting=authorRedditAgeAtTimeOfPosting, timestamp=timestamp, score=score, upvotes=upvotes, downvotes=downvotes, url=url, text=text, html=html)
    except praw.errors.NotFound:
        pass

mysqlConnection.close()
exit()
