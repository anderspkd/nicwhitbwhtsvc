from __future__ import unicode_literals

import youtube_dl
import dbus

from subprocess import Popen, PIPE
from os import putenv

# prefex for the dbus process of omxplayer
TMP_PREFIX = '/tmp/omxplayerdbus'

# Conversion constants from microseconds to whatever
TIME_UNITS = {'us' : 1,
              'ms' : 1000,
              's'  : 10**6,
              'm'  : (10**6)*60}

class VideoPlayer(object):

    def __init__(self, url_or_file, fetch_with_ytdl=False, cmd='omxplayer', args=['-o', 'hdmi']):

        # Set file to play. Can be gotten via. youtube-dl
        if fetch_with_ytdl and _is_url(url_or_file):
            self.file_link = _fetch_with_ytdl(url_or_file)
        else:
            self.file_link = url_or_file

        # Start the video player
        self.args = args + [self.file_link]
        self._process = Popen([cmd] + self.args)

        # Open dbus connection to video process
        # TODO: Add the properties interface (at least)
        self._init_env()
        self.bus = dbus.SessionBus()
        self.player = bus.get_object('org.mpris.MediaPlayer2.omxplayer',
                                     '/org/mpris/MediaPlayer2')
        self.player_iface = dbus.Interface(self.player,
                                           dbus_interface='org.mpris.MediaPlayer2.Player')

    # Helper functions. Meant to be for internal use only
    def _init_env(self):
        with open(TMP_PREFIX + 'pi') as f:
            putenv('DBUS_SESSION_BUS_ADDRESS', f.read().strip())
        with open(TMP_PREFIX + 'pi.pid') as f:
            putenv('DBUS_SESSION_BUS_PID', f.read().strip())

    def _is_url(self, url):
        """Test if [url] is a valid url"""

        # TODO: make more serious
        return url[:4] == 'http' or url[:5] == 'https'

    def _fetch_with_ytdl(self, url):
        """Fetch a direct file url with youtube-dl.
        Should return the highest resolution avaliable
        """

        with youtube_dl.YoutubeDL as ydl:
            r = ydl.extract_info(url, download=False)

        # title = r['title'] if 'title' in r else 'untitled'

        if 'formats' in r:
            fmt = [x for x in r['formats'] if 'resolution' in x]
            def res_cmp(it):
                rs = it['resolution'].split('x')
                return int(rs[0]) + int(rs[1])
            file_link = sorted(fmt, key=res_cmp, reverse=True)[0]
            return file_link
        else:
            # Make less generic
            raise Exception

    def _convert_num(self, t, step, fn):
        try:
            multp = TIME_UNITS[step]
            r = str(int(t) * multp)
            return fn(r)
        except:
            print('"_convert_num" failed with args: {}, {}, {}'.format(t, step, fn))
            raise

    # Outward interface
    def pause(self):
        self.player_iface.Pause()

    def play(self):
        self.player_iface.Play()

    def toggle_play(self):
        self.player_iface.PlayPause()

    def mute(self):
        self.player_iface.Mute()

    def unmute(self):
        self.player_iface.Unmute()

    def seek(self, t, step='s'):
        to = self._convert_num(t, step, dbus.Int64)
        self.player_iface.Seek(to)

    def set_position(self, t, step='s'):
        to = self._convert_num(t, step, dbus.Int64)
        self.player_iface.SetPosition(to)
