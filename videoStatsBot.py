#!/Library/Frameworks/Python.framework/Versions/3.4/bin/python3

#run with python3

import praw
import logging
from time import sleep
import threading
import requests
from datetime import datetime
from lxml import html

logFile = 'videoStatsBot.log'

def get_logger():
    "returns a logger which logs to file and stdout"
    log = logging.getLogger('_name_')
    logFormat = '[%(asctime)s] [%(levelname)s] - %(message)s'

    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(logging.Formatter(logFormat))
    log.addHandler(streamHandler)

    fileHandler = logging.FileHandler(logFile)
    fileHandler.setFormatter(logging.Formatter(logFormat))
    log.addHandler(fileHandler)

    log.setLevel(level=logging.INFO)
    return log

class Looper:
    "Class for eternally looping a function with pauses and automatic retries"

    def __init__(self, name, func, pause_length=0, data=None):
        """param: name: descritive and unique name for what the passed function does.
        param: func: function to be looped. Must accept a looper as argument e.g. def my_func(looper):.
        param: pause_length: duration to sleep after one loop. Defaults to 0.
        param: data: data for the passed function to access"""
        self.name = name
        self.func = func
        self.pause_length = pause_length
        self.sleepUntilNextTry = 0.1
        self.thread = None
        self.data = None

    def log_some(self, msg, critical=False):
        """log something happing in here to the global logger
        param: msg: message to be logged
        param: critical = whether or not message should be marked critical"""
        s = self.name + ': ' + msg
        if critical:
            log.critical(s)
        else:
            log.info(s)

    def _func_wrapper(self):
        "wrapper for the function passed when initialised. Implements loop, pauses and retries"
        self.log_some('starting')
        while True:
            try:
                self.func(self)
                self.sleepUntilNextTry =  0.1 # reset countdown since this loop worked
                if self.pause_length > 0:
                    self.log_some('pausing for '+ str(self.pause_length) +'s', critical=False)
                    sleep(self.pause_length) # not necessary to put into if, but cleaner
            except Exception as e:
                self.log_some(str(e), critical=True)
                self.sleepUntilNextTry *= 2
                self.log_some('trying again in '+ str(self.sleepUntilNextTry) +'s', critical=True)
                sleep(self.sleepUntilNextTry)
                continue

    def loop(self):
        "start the loop"
        self.thread = threading.Thread(target=self._func_wrapper)
        self.thread.start()

def get_int_from_string(string):
    return ''.join([c for c in string if c in '1234567890'])

def get_date_from_string(string):
    return ''.join([c for c in string if c in '1234567890.'])

def get_video_stats(url):
    video = {}
    req = requests.get(url)
    tree = html.fromstring(req.content)
    # viewCount = tree.xpath('//*[@id="watch7-views-info"]/div[1]')[0]
    video['title'] = tree.xpath('//*[@id="eow-title"]')[0].text.strip()
    # print(title)
    video['url'] = url
    video['viewCount'] = get_int_from_string(tree.xpath('//*[@id="watch7-views-info"]/div[1]')[0].text)
    # print('views: '+str(viewCount))
    video['likes'] = get_int_from_string(tree.xpath('//*[@id="watch8-sentiment-actions"]/span/span[1]/button/span')[0].text)
    # print('likes: '+str(likes))
    video['dislikes'] = get_int_from_string(tree.xpath('//*[@id="watch8-sentiment-actions"]/span/span[3]/button/span')[0].text)
    # print('dislikes: '+str(dislikes))
    video['uploader'] = tree.xpath('//*[@id="watch7-user-header"]/div/a')[0].text
    # print(uploader)
    video['uploaderURL'] = 'https://www.youtube.com' + tree.xpath('//*[@id="watch7-user-header"]/div/a')[0].attrib['href']
    # print(uploaderURL)
    video['retrieved'] = datetime.utcnow()
    return video

def post_video_stats(submission, video):
    replyString = '#/u/VideoStatsBot\n\n['\
        + video['title']\
        + ']('\
        + video['url']\
        + ')  \nby ['\
        + video['uploader']\
        + ']('\
        + video['uploaderURL']\
        + ')  \n'\
        + str(video['viewCount'])\
        + ' Views - '\
        + str(video['likes'])\
        + (' Like - ' if video['likes'] == 1 else ' Likes - ')\
        + str(video['dislikes'])\
        + (' Dislike  \n' if video['dislikes'] == 1 else ' Dislikes  \n')\
        + '***\n'\
        + '^(I am a bot. Data retrieved on: '\
        + str(video['retrieved'])\
        + ' UTC)'
    # print(replyString)
    submission.reply(replyString)

def video_stats_bot(looper):
    for submission in reddit.domain('youtube.com').new(limit=1):
        looper.log_some('video found: ' + submission.id)

        video = get_video_stats(submission.url)
        post_video_stats(submission, video)

def video_stats_bot2(looper):
    for submission in reddit.domain('youtu.be').new(limit=1):
        looper.log_some('video found: ' + submission.id)

        video = get_video_stats(submission.url)
        post_video_stats(submission, video)

def rvideos_stats_bot(looper):
    for submission in reddit.subreddit('videos').new(limit=1):
        looper.log_some('video found: ' + submission.id)

        video = get_video_stats(submission.url)
        post_video_stats(submission, video)

def log_karma(looper):
    "logs my karma"
    me = reddit.user.me()
    ck = me.comment_karma
    lk = me.link_karma
    looper.log_some('comment karma: '+str(ck))
    looper.log_some('link karma: '+str(lk))

# init logger
log = get_logger()

# init reddit
reddit = praw.Reddit('videoStatsBot') # uses praw.ini for login (in same dir as this file)

# init bots
loopers = []
# loopers.append(Looper(name="youtube.com bot", func=video_stats_bot))
# loopers.append(Looper(name="youtu.be bot", func=video_stats_bot2))
loopers.append(Looper(name='/r/videos bot', func=rvideos_stats_bot)) #until enough karma collected
loopers.append(Looper(name='karma logger', func=log_karma, pause_length=3600))

# start bots
for l in loopers:
    l.loop()

# test area
# video_stats_bot()
