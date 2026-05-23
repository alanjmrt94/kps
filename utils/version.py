"""Utilidades de versión de kps y del intérprete Python."""

import platform

from utils.const import Version


def Py_version():  # pylint: disable=invalid-name
    """Devuelve la versión mayor de Python en ejecución."""
    return int(platform.python_version()[0])


def App_version():  # pylint: disable=invalid-name
    """Devuelve la versión de la aplicación kps."""
    return Version
