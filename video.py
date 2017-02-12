from __future__ import unicode_literals, print_function

import youtube_dl
import subprocess
import requests
import logging
from validators.url import url as is_url
import os
from errors import *
from controllers import *

# Conversion constants from microseconds to whatever
TIME_UNITS = {'us' : 1,
              'ms' : 1000,
              's'  : 10**6,
              'm'  : (10**6)*60}

YDL = youtube_dl.YoutubeDL()

logger = logging.getLogger('video')

class VideoPlayer(object):

    controller = None

    def __init__(self, url, fetch=False):
        self.video_proc = None
        logger.info('Creating VideoPlayer with url=%r, fetch=%r', url, fetch)
        try:
            # fetch video url
            if fetch:
                _url = self.__fetch_with_ytdl(url)
            else:
                _url = self.__fetch_directly(url)
            self.url = _url
            self.video_proc = self.__start_video(self.url)


            # If the video started, instantiate a controller
            # object. Will fall back to a generic one if the DBus one
            # didn't work.
            if self.video_proc and self.is_playing():
                try:
                    self.controller = DbusController(self.video_proc)
                except ControllerException as e:
                    logger.warn(e)
                    self.controller = Controller(self.video_proc)
                logger.info('Using controller: %r', repr(self.controller))
        except FetchException as fex:
            logger.warn(fex)


    def __str__(self):
        if not self.video_proc or not self.is_playing():
            return '(DEAD) ' + self.url
        return self.url


    def __start_video(self, video_link, player='omxplayer', player_args=['-o', 'hdmi']):
        self.devnull = open(os.devnull, 'w')
        proc = subprocess.Popen([player] + player_args + [video_link],
                                stdout=self.devnull)
        logger.info('Started video with pid: %d', proc.pid)
        return proc


    def __validate_url(self, url, query_url=False):
        """Test if [url] is valid. If [query_url] is True, will also do a HEAD
        request to check if the resource is actually avaliable.

        """
        if not is_url(url):
            raise InvalidUrlException(url)
        if query_url:
            sc = None
            try:
                sc = requests.head(url).status_code
            except Exception as e:
                raise FetchException(url, e)
            if sc != 200:
                raise BadStatusCodeException(url, sc)
        return True # ftso. comparison and sane behaviour


    def __fetch_directly(self, url):
        """Return [url] if it points to a local file, or it points to
        something reachable on the web.

        """
        if os.path.isfile(url):
            return url
        self.__validate_url(url, query_url=True)
        return url


    def __fetch_with_ytdl(self, url):
        """Fetches the resource that might be avaliable at [url] using
        Youtube-dl.

        """
        self.__validate_url(url)
        try:
            # Extract with YDL.
            ydlr = YDL.extract_info(url, download=False)
            return ydlr['url']
        except Exception as e:
            raise YoutubeDLException(url)


    def is_playing(self):
        """Checks if the process corresponding to the video is still alive."""
        if self.video_proc:
            return self.video_proc.poll() == None
        return False


    def clean_up(self):
        """Cleans up the object."""
        self.video_proc = None
        self.controller = None
        try:
            self.devnull.close()
        except:
            pass
