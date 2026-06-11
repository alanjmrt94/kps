"""Constantes, enums y versión de kps."""

import sys
from enum import Enum, unique

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:

    class StrEnum(str, Enum):  # type: ignore[misc]
        """Compatibilidad StrEnum para Python 3.10."""

Version = "1.6.2"  # pylint: disable=invalid-name  # Mayor.minor.patch; usado por App_version()

# Tiempos por defecto (segundos)
DEFAULT_AWAY_TIME = 2
DEFAULT_POLL_INTERVAL = 5

# Configuración persistente
CONFIG_FILENAME = "config.toml"

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
