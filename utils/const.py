"""Constantes, enums y versión de kps."""

from enum import StrEnum, unique

Version = "1.4.0"  # pylint: disable=invalid-name  # Mayor.minor.patch; usado por App_version()

# Tiempos por defecto (segundos)
DEFAULT_AWAY_TIME = 2
DEFAULT_POLL_INTERVAL = 5

# Rutas de scripts de movimiento del ratón por plataforma
MOVE_SCRIPT_LINUX = "utils/move.py"
MOVE_SCRIPT_WINDOWS = "utils/move_win.py"
MOVE_SCRIPT_MACOS = "utils/move_mac.py"

VENV_DIR_NAME = ".venv"


class Display(StrEnum):
    """Tipo de display GDK detectado."""

    def __str__(self):
        return str(self.value)

    X11 = "X11Display"
    WAYLAND = "GdkWaylandDisplay"
    WIN32 = "GdkWin32Display"
    QUARTZ = "GdkQuartzDisplay"


@unique
class IdleState(StrEnum):
    """Estado de inactividad del usuario."""

    def __str__(self):
        return str(self.value)

    UNKNOWN = "OS probably not supported"
    XA = "extended away"
    AWAY = "away"
    AWAKE = "awake"


@unique
class OsType(StrEnum):
    """Identificador de familia OS (os.name)."""

    def __str__(self):
        return str(self.value)

    UNIX = "posix"
    WINDOWS = "nt"
