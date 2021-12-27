
import time

import uinput

events = (
    uinput.REL_X,
    uinput.REL_Y,
    uinput.BTN_LEFT,
    uinput.BTN_RIGHT,
)
with uinput.Device(events) as device:
    for i in range(3):
        if i == 2:
            device.emit(uinput.REL_X, -75)
        else:
            device.emit(uinput.REL_X, 100)
        time.sleep(0.5)
