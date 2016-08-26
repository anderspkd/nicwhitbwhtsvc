from __future__ import unicode_literals, print_function

import youtube_dl
import dbus
import subprocess
import os

from time import sleep

# prefex for the dbus process of omxplayer
TMP_PREFIX = '/tmp/omxplayerdbus.'

# Conversion constants from microseconds to whatever
TIME_UNITS = {'us' : 1,
              'ms' : 1000,
              's'  : 10**6,
              'm'  : (10**6)*60}

class VideoPlayer(object):

    def __init__(self, url_or_file, fetch_with_ytdl=False, cmd='/home/pi/omxplayer/omxplayer', args=['-o', 'hdmi']):

        # Set file to play. Can be gotten via. youtube-dl
        if fetch_with_ytdl and self._is_url(url_or_file):
            print('fetching with youtube-dl')
            self.ydl_result = self._fetch_with_ytdl(url_or_file)
            if 'url' in self.ydl_result:
                self.video_link = self.ydl_result['url']
            else:
                raise NameError('could not fetch {} with youtube-dl'.format(url_or_file))
        else:
            self.video_link = url_or_file

        # Start the video player
        self.args = args + [self.video_link]
        devnull = open(os.devnull, 'w')
        self._process = subprocess.Popen([cmd] + self.args, stdout=devnull)

        # wait until the dbus files are present. Maybe someone removed them...
        while not os.path.isfile(TMP_PREFIX + 'pi'):
            pass

        self._init_dbus()

    # Helper functions. Meant to be for internal use only
    def _init_dbus(self):
        with open(TMP_PREFIX + 'pi') as f:
            os.putenv('DBUS_SESSION_BUS_ADDRESS', f.read().strip())
        with open(TMP_PREFIX + 'pi.pid') as f:
            os.putenv('DBUS_SESSION_BUS_PID', f.read().strip())

        for tries in range(20):
            try:
                bus = dbus.SessionBus()
                self.player = bus.get_object('org.mpris.MediaPlayer2.omxplayer',
                                             '/org/mpris/MediaPlayer2',
                                             introspect=False)
                self.root_iface = dbus.Interface(self.player, dbus_interface='org.mpris.MediaPlayer2')
                self.player_iface = dbus.Interface(self.player, dbus_interface='org.mpris.MediaPlayer2.Player')
            except:
                print('.', end='')
                sleep(0.5)
                continue
            break
        print(' found dbus connection')


    # TODO: clear object perhaps?
    def _kill(self):
        print('Exiting...')
        self.root_iface.Quit()

    def _is_url(self, url):
        """Test if [url] is a valid url"""

        # TODO: make more serious
        return url[:4] == 'http' or url[:5] == 'https'

    def _fetch_with_ytdl(self, url):
        """Fetch a direct file url with youtube-dl.
        Should return the highest resolution avaliable
        """

        ydl = youtube_dl.YoutubeDL()
        r = ydl.extract_info(url, download=False)

        if 'formats' in r:
            fmt = [x for x in r['formats'] if 'resolution' in x]
            def res_cmp(it):
                rs = it['resolution'].split('x')
                return int(rs[0]) + int(rs[1])
            video_link = sorted(fmt, key=res_cmp, reverse=True)[0]
            return video_link
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

    def stop(self):
        self._kill()

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
