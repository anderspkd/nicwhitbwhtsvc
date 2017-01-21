from __future__ import unicode_literals, print_function

import youtube_dl
import dbus
import subprocess
from validators.url import url as is_url
import os

from time import sleep

# Conversion constants from microseconds to whatever
TIME_UNITS = {'us' : 1,
              'ms' : 1000,
              's'  : 10**6,
              'm'  : (10**6)*60}


class VideoPlayer(object):

    controller = None

    def __init__(self, url, fetch=False):

        self.video_pid = None

        if url:
            if fetch and is_url(url):
                url = self._fetch_with_ytdl(url)
            self.video_pid = self._start_video(url)

            if self.is_playing():
                try:
                    self.controller = DbusController(self.video_pid)
                except:
                    self.controller = Controller(self.video_pid)
                print('Using controller: %r' % self.controller)


    def _start_video(self, video_link, player='omxplayer', player_args=['-o', 'hdmi']):
        devnull = open(os.devnull, 'w')
        pid = subprocess.Popen([player] + player_args + [video_link],
                               stdout=devnull).pid
        print('started video with pid', pid)
        return pid


    def _fetch_with_ytdl(self, url):
        with youtube_dl.YoutubeDL() as ydl:
            r = ydl.extract_info(url, download=False)
        return r['url'] if 'url' in r else ''


    def is_playing(self):
        if self.video_pid:
            try:
                os.kill(self.video_pid, 0)
            except:
                return False
            return True
        return False


class Controller(object):

    # Only supports killing the video, which is OK since the video
    # will autoplay when the process is started.

    def __init__(self, pid):
        self._pid = pid

    def __str__(self):
        return "SimpleController"

    def play(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def quit(self):
        try:
            os.kill(self.pid, 9)
        except:
            print('Nothing to kill')

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

    def __init__(self, pid):
        running = False
        user_file = '/tmp/omxplayerdbus.normal-user'
        pid_file = user_file + '.pid'

        while not (os.path.isfile(user_file)
                   and os.path.isfile(pid_file)):
            sleep(0.2)
            pass

        # Set appropriate environment variables
        with open(user_file) as f:
            os.putenv('DBUS_SESSION_BUS_ADDRESS', f.read().strip())
        with open(pid_file) as f:
            os.putenv('DBUS_SESSION_BUS_PID', f.read().strip())

        for tries in range(20):
            # try to connect 20 times, waiting half a second between each
            try:
                bus = dbus.SessionBus()
                self.player = bus.get_object('org.mpris.MediaPlayer2.omxplayer',
                                             '/org/mpris/MediaPlayer2',
                                             introspect=False)
                self.root_iface = dbus.Interface(self.player, dbus_interface='org.mpris.MediaPlayer2')
                self.player_iface = dbus.Interface(self.player, dbus_interface='org.mpris.MediaPlayer2.Player')
            except:
                sleep(0.5)
                continue
            print('Found DBus connection in %s trie(s)' % tries+1)
            running = True
            break

        if not running:
            raise RuntimeError("Failed to establish dbus connection")

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
