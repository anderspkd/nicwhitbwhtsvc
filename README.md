# nicwhitbwhtsvc

A small webapp which can be used to control the `omxplayer` video
player program on a raspberry pi.

The title means

>**N**ow **I** **C**an **W**atch **H**alf **I**n **T**he **B**ag
>**W**ithout **H**aving **T**o **S**witch **V**GA **C**ables

which is also my motivation for writing this application.

# Requirements

Uses `youtube-dl`, `flask` and `dbus-python`, so install
that.

# DBus issues

DBus seems to behave badly -- or maybe I just don't know how to use it
properly. To "fix" issues (such as failing to use `DbusController` any
or all of the following

- remove the socket file in `/var/run/dbus/` and reboot
- remove the `omxplayerdbus.*` files in `/tmp/`
