from __future__ import unicode_literals, print_function

import youtube_dl
import subprocess
import requests
import logging
from validators.url import url as is_url
import os
from errors import *
from controllers import *

YDL = youtube_dl.YoutubeDL()

logger = logging.getLogger('video')

# for caching urls fetched with ytdl
url_cache = {}

class VideoPlayer(object):

    controller = None

    # used for pretty-printing
    url = ''
    title = ''

    def __init__(self, url, fetch=False):
        self._video_proc = None
        self.url = url

        logger.info('Creating VideoPlayer with url=%r, fetch=%r', url, fetch)

        try:
            # fetch video url
            if fetch:
                if url in url_cache:
                    self.direct_url = url_cache[url]
                else:
                    self.direct_url = self.__fetch_with_ytdl(url)
                    url_cache[url] = self.direct_url
            else:
                self.direct_url = self.__fetch_directly(url)

            logger.info('direct url: %r', self.direct_url)

            # start video if we got
            if self.direct_url:
                self.__start_video(self.direct_url)


            # If the video started, instantiate a controller
            # object. Will fall back to a generic one if the DBus one
            # didn't work.
            if self.is_playing():
                try:
                    self.controller = DbusController(self._video_proc)
                except ControllerException as e:
                    logger.warn(e)
                    self.controller = Controller(self._video_proc)
                logger.info('Using controller: %r', repr(self.controller))
            else:
                logger.info('No video started')
        except FetchException as fex:
            logger.warn(fex)


    def __str__(self):
        s = '%s (%s)' % (self.title, self.url)
        if not self.is_playing():
            return '(DEAD) ' + s
        return s


    def __start_video(self, video_link, player='omxplayer', player_args=['-o', 'hdmi']):
        self.devnull = open(os.devnull, 'w')
        proc = subprocess.Popen([player] + player_args + [video_link],
                                stdout=self.devnull)
        logger.info('Started video with pid: %d', proc.pid)
        self._video_proc = proc


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
        if os.path.isfile(url) or self.__validate_url(url, query_url=True):
            self.title = url.split('/')[-1] # set title to file part of url
            return url
        return None

    def __fetch_with_ytdl(self, url):
        """Fetches the resource that might be avaliable at [url] using
        Youtube-dl.

        """
        self.__validate_url(url)
        try:
            # Extract with YDL.
            ydlr = YDL.extract_info(url, download=False)
            try:
                self.title = ydlr['title']
            except:
                self.title = 'No title'
            return ydlr['url']
        except Exception as e:
            raise YoutubeDLException(url)


    def is_playing(self):
        """Checks if the process corresponding to the video is still alive."""
        if self._video_proc:
            return self._video_proc.poll() == None
        return False


    def clean_up(self):
        """Cleans up the object."""
        self._video_proc = None
        self.controller = None
        try:
            self.devnull.close()
        except:
            pass
