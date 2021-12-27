import logging
import os

import gi

gi.require_version('Gdk', '4.0')
from gi.repository import Gdk

from utils.const import Display


def log(domain):
    if domain != 'kps':
        domain = 'kps.%s' % domain
    return logging.getLogger(domain)


def is_display(display):
    # XWayland reports as Display X11, so try with env var
    is_wayland = os.environ.get('XDG_SESSION_TYPE') == 'wayland'
    if is_wayland and display == Display.WAYLAND:
        return True

    default = Gdk.Display.get_default()
    if default is None:
        log('kps').warning('Could not determine window manager')
        return False
    return default.__class__.__name__ == display.value
