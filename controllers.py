from __future__ import unicode_literals, print_function

import dbus
import os
import logging
from errors import ControllerException
from time import sleep

class Controller(object):

    # Only supports killing the video, which is OK since the video
    # will autoplay when the process is started.

    def __init__(self, proc):
        self.logger = logging.getLogger(str(self))
        self._proc = proc
        self._pid = self._proc.pid

    def __str__(self):
        return "SimpleController"

    def _info(self, msg):
        self.logger.info('[%d] %s' % (self._pid, msg))

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
        Controller.__init__(self, proc)
        self.running = False
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
            self._info('Found DBus connection in %r trie(s)' % (tries+1))
            self.running = True
            break

        if not self.running:
            raise ControllerException("Failed to establish dbus connection")

    def __str__(self):
        return "DBusController"

    def play(self):
        self._info('play')
        self.player_iface.Play()

    def stop(self):
        self._info('stop')
        self.player_iface.Stop()

    def quit(self):
        self._info('quit')
        self.root_iface.Quit()
        Controller.quit(self)

    def pause(self):
        self._info('pause')
        self.player_iface.Pause()

    def toggle_play(self):
        self._info('toggle_play')
        self.player_iface.PlayPause()
