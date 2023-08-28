from enum import Enum, StrEnum, unique

Version = "1.1.1.5"

class Display(StrEnum):
    def __str__(self):
        return str(self.value)
    X11 = 'X11Display'
    WAYLAND = 'GdkWaylandDisplay'
    WIN32 = 'GdkWin32Display'
    QUARTZ = 'GdkQuartzDisplay'


@unique
class IdleState(StrEnum):
    def __str__(self):
        return str(self.value)
    UNKNOWN = 'OS probably not supported'
    XA = 'extended away'
    AWAY = 'away'
    AWAKE = 'awake'

@unique
class OsType(StrEnum):
    def __str__(self):
        return str(self.value)
    UNIX = 'posix'
    WINDOWS = 'nt'
