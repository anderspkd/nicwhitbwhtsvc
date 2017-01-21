from __future__ import unicode_literals, print_function

import youtube_dl
import dbus
import subprocess
from validators.url import url as is_url
import os

from time import sleep

class ControllerException(Exception):
    def __init__(self, v):
        self.v = v
    def __str__(self):
        return 'ControllerException: '+ repr(self.v)

# Conversion constants from microseconds to whatever
TIME_UNITS = {'us' : 1,
              'ms' : 1000,
              's'  : 10**6,
              'm'  : (10**6)*60}

YDL = youtube_dl.YoutubeDL()

class VideoPlayer(object):

    controller = None

    def __init__(self, url, fetch=False):

        self.video_proc = None

        if url:
            if fetch and is_url(url):
                _url = self._fetch_with_ytdl(url)
                if not _url:
                    print('YoutubeDL could not extract url from', url)
                    print('Trying to play url directly')
                else:
                    url = _url
            self.video_proc = self._start_video(url)

            if self.is_playing():
                # Only interested in ControllerExceptions. Fail on
                # everything else.
                try:
                    self.controller = DbusController(self.video_proc)
                except ControllerException as e:
                    print(e)
                    self.controller = Controller(self.video_proc)
                print('Using controller: %r' % self.controller)


    def _start_video(self, video_link, player='omxplayer', player_args=['-o', 'hdmi']):
        self.devnull = open(os.devnull, 'w')
        proc = subprocess.Popen([player] + player_args + [video_link],
                                stdout=self.devnull)
        print('started video with pid', proc.pid)
        return proc


    def _fetch_with_ytdl(self, url):
        r = YDL.extract_info(url, download=False)
        return r['url'] if 'url' in r else ''


    def is_playing(self):
        if self.video_proc:
            return self.video_proc.poll() == None
        return False


    # probably not entirely necessary, but w/e
    def clean_up(self):
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
