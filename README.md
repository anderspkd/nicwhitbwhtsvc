# nicwhitbwhtsvc

A small webapp which can be used to control the `omxplayer` video
player program on a raspberry pi.

The title means

>**N**ow **I** **C**an **W**atch **H**alf **I**n **T**he **B**ag
>**W**ithout **H**aving **T**o **S**switch **V**GA **C**ables

which is also my motivation for writing this application.

# Requirements

The server uses `Flask`. The video player uses `dbus-python` and
`youtube-dl`. Note that the `youtube-dl` version install-able with
`pip` is very old (2012ish), and should therefore be avoided. Download
the version on their git and use that instead.
