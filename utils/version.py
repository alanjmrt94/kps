import platform

from utils.const import Version

def Py_version():
    return int(platform.python_version()[0])

def App_version():
    return Version
