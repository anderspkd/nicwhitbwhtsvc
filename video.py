from __future__ import unicode_literals, print_function

import youtube_dl
import dbus
import subprocess
import requests
from validators.url import url as is_url
import os

from time import sleep

# Thrown when controller initialization fails
class ControllerException(Exception):
    def __init__(self, v):
        self.v = v
    def __str__(self):
        return 'ControllerException: '+ repr(self.v)

# Thrown when we cannot fetch a url.
class FetchException(Exception):
    def __init__(self, url, e):
        self.url = url
        self.e = e
    def __str__(self):
        return ('Url ' + repr(self.url) +
                ' raised generic FetchException:\n' + repr(self.e))

# fetch=True excetions
class InvalidUrlException(FetchException):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return 'Invalid url: ' + repr(self.url)

class BadStatusCodeException(FetchException):
    def __init__(self, url, status_code):
        self.url = url
        self.status_code = status_code
    def __str__(self):
        return ('Url ' + repr(self.url) +
                ' returned bad status-code (' +
                repr(self.status_code) + ')')

class YoutubeDLException(FetchException):
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return 'Youtube-dl could not fetch resource at ' + repr(self.url)


# Conversion constants from microseconds to whatever
TIME_UNITS = {'us' : 1,
              'ms' : 1000,
              's'  : 10**6,
              'm'  : (10**6)*60}

YDL = youtube_dl.YoutubeDL()

class VideoPlayer(object):

    # How we access [url] depends on fetch:
    # fetch=False:
    #  1) test that [url] is valid
    #  2) test that [url] points at something (i.e., returns code 200)
    #  3) fetch it with youtube-dl
    #
    # fetch=True:
    #  1) test if [url] is a local file
    #  2) if it is, play it. If not;
    #  3) test if it is reachable (as above).

    controller = None

    def __init__(self, url, fetch=False):

        self.video_proc = None

        try:
            # Fetch resource using a strategy depending on [fetch].
            if fetch:
                _url = self.__fetch_with_ytdl(url)
            else:
                _url = self.__fetch_directly(url)
            self.video_proc = self.__start_video(_url)


            # If the video started, initialize a DbusController or a
            # generic Controller if that Dbus shits itself.
            if self.video_proc and self.is_playing():
                try:
                    self.controller = DbusController(self.video_proc)
                except ControllerException as e:
                    print(e)
                    self.controller = Controller(self.video_proc)
                print('Using controller:', repr(self.controller))
        except FetchException as fex:
            print(fex)


    def __start_video(self, video_link, player='omxplayer', player_args=['-o', 'hdmi']):
        self.devnull = open(os.devnull, 'w')
        proc = subprocess.Popen([player] + player_args + [video_link],
                                stdout=self.devnull)
        print('started video with pid', proc.pid)
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
        """Fetches a resource directly. For use on files which are directly
        avaliable, e.g., www.example.com/bla.mp4 or file:///bla.mp4.

        """
        if os.path.isfile(url):
            return url
        self.__validate_url(url, query_url=True)
        return url


    def __fetch_with_ytdl(self, url):
        """Fetches the resource that might be avaliable at [url] using
        Youtube-dl

        """
        # We don't want a HEAD request here, as ytdl already does one.
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


class Controller(object):

    # Only supports killing the video, which is OK since the video
    # will autoplay when the process is started.

    def __init__(self, proc):
        self._proc = proc

    def __str__(self):
        return "SimpleController"

    def play(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def quit(self):
        if self._proc:
            self._proc.terminate()

    def toggle_play(self):
        raise NotImplementedError

    def mute(self):
        raise NotImplementedError

    def seek(self, t, step='s'):
        raise NotImplementedError

    def set_position(self, t, step='s'):
        raise NotImplementedError


class DbusController(Controller):

    # Could potentially implement everything supported by the
    # omxplayer dbus interface. Only doing simple stuff atm.

    def __init__(self, proc):
        running = False
        user_file = '/tmp/omxplayerdbus.normal-user'
        pid_file = user_file + '.pid'

        while not (os.path.isfile(user_file)
                   and os.path.isfile(pid_file)):
            sleep(0.2)
            pass

        # Set appropriate environment variables
        with open(user_file) as f:
            e = f.read().strip()
            os.putenv('DBUS_SESSION_BUS_ADDRESS', e)
        with open(pid_file) as f:
            e = f.read().strip()
            os.putenv('DBUS_SESSION_BUS_PID', e)

        for tries in range(20):
            # try to connect 20 times, waiting half a second between each
            try:
                bus = dbus.SessionBus()
                self.player = bus.get_object('org.mpris.MediaPlayer2.omxplayer',
                                             '/org/mpris/MediaPlayer2',
                                             introspect=False)
                self.root_iface = dbus.Interface(self.player, dbus_interface='org.mpris.MediaPlayer2')
                self.player_iface = dbus.Interface(self.player, dbus_interface='org.mpris.MediaPlayer2.Player')
            except Exception as e:
                sleep(0.5)
                continue
            print('Found DBus connection in %s trie(s)' % str(tries+1))
            running = True
            break

        if not running:
            raise ControllerException("Failed to establish dbus connection")

    def __str__(self):
        return "DBusController"

    def play(self):
        self.player_iface.Play()

    def stop(self):
        self.player_iface.Stop()

    def quit(self):
        self.root_iface.Quit()

    def pause(self):
        self.player_iface.Pause()

    def toggle_play(self):
        self.player_iface.PlayPause()
