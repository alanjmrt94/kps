from enum import Enum, unique


class Display(Enum):
    X11 = 'X11Display'
    WAYLAND = 'GdkWaylandDisplay'
    WIN32 = 'GdkWin32Display'
    QUARTZ = 'GdkQuartzDisplay'


@unique
class IdleState(Enum):
    UNKNOWN = 'unknown'
    XA = 'xa'
    AWAY = 'away'
    AWAKE = 'online'

class OsType(Enum):
    UNIX='posix'
    WINDOWS='nt'