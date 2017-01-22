from __future__ import unicode_literals, print_function

# Exceptions used by VideoPlayer and Controller classes.

class ControllerException(Exception):
    """Indicates something related to the Controller went wrong. Currently
    used to signal that DbusController failed to initialize

    """
    def __init__(self, v):
        self.v = v
    def __str__(self):
        return 'ControllerException: '+ repr(self.v)


class FetchException(Exception):
    """Parent class for all url fetch/check related exceptions."""
    def __init__(self, url, e):
        self.url = url
        self.e = e
    def __str__(self):
        return ('Url ' + repr(self.url) +
                ' raised generic FetchException:\n' + repr(self.e))


class InvalidUrlException(FetchException):
    """Indicates an invalid url."""
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return 'Invalid url: ' + repr(self.url)


class BadStatusCodeException(FetchException):
    """Indicates a non-200 status-code."""
    def __init__(self, url, status_code):
        self.url = url
        self.status_code = status_code
    def __str__(self):
        return ('Url ' + repr(self.url) +
                ' returned bad status-code (' +
                repr(self.status_code) + ')')


class YoutubeDLException(FetchException):
    """Indicates that Youtube-dl was unable to fetch a resource, connect,
    or whatever.

    """
    def __init__(self, url):
        self.url = url
    def __str__(self):
        return 'Youtube-dl could not fetch resource at ' + repr(self.url)
