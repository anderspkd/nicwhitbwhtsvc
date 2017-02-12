# Conversion constants from whatever to microseconds
TIME_UNITS = {'us' : 1,
              'ms' : 1000,
              's'  : 10**6,
              'm'  : (10**6)*60}

def as_bool(thing, default=False):
    """Ensure thing is a bool."""
    assert type(default) == bool, 'Nice try'
    if type(thing) != bool:
        return default
    return thing

def us2string(us):
    """Convert microseconds to a string of the form H:M:S. Works for
videos upto 24 hours long. I think...

    """
    x = us // TIME_UNITS['s']
    sec = x % 60
    x //= 60
    min = x % 60
    x //= 60
    hour = x % 60
    return '%02d:%02d:%02d' % (hour, min, sec)
