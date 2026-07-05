"""Tests de uinput vía ctypes (sin hardware)."""


# pylint: disable=missing-function-docstring,missing-class-docstring,protected-access
from __future__ import annotations

from unittest.mock import patch

import pytest

from utils import uinput_device


def test_pack_input_event_size() -> None:
    data = uinput_device._pack_input_event(1, 2, 3)
    assert len(data) == 24


def test_pack_user_device_has_name() -> None:
    data = uinput_device._pack_user_device("kps-test")
    assert data.startswith(b"kps-test")


def test_uinput_device_emit_and_close() -> None:
    mock_fd = 7
    with (
        patch.object(uinput_device.os, "open", return_value=mock_fd),
        patch.object(uinput_device.os, "write") as mock_write,
        patch.object(uinput_device.os, "close") as mock_close,
        patch.object(uinput_device.fcntl, "ioctl"),
    ):
        with uinput_device.UInputDevice((uinput_device.REL_X,)) as device:
            device.emit(uinput_device.REL_X, 10)
        assert mock_write.call_count >= 2
        mock_close.assert_called_once_with(mock_fd)


def test_uinput_device_open_failure() -> None:
    with patch.object(uinput_device.os, "open", side_effect=PermissionError("denied")):
        with pytest.raises(PermissionError):
            uinput_device.UInputDevice((uinput_device.REL_X,))


def test_emit_on_closed_device() -> None:
    device = uinput_device.UInputDevice.__new__(uinput_device.UInputDevice)
    device._fd = None
    with pytest.raises(OSError, match="cerrado"):
        device.emit(uinput_device.REL_X, 1)


def test_uinput_device_rel_and_key_capabilities() -> None:
    mock_fd = 11
    with (
        patch.object(uinput_device.os, "open", return_value=mock_fd),
        patch.object(uinput_device.os, "write"),
        patch.object(uinput_device.os, "close"),
        patch.object(uinput_device.fcntl, "ioctl") as mock_ioctl,
    ):
        with uinput_device.UInputDevice((uinput_device.REL_X, uinput_device.BTN_LEFT)) as device:
            device.emit(uinput_device.BTN_LEFT, 1)
    assert mock_ioctl.call_count >= 5


def test_uinput_device_destroy_error_still_closes() -> None:
    mock_fd = 9

    def ioctl_side_effect(_fd: int, op: int, *_args: object) -> None:
        if op == uinput_device.UI_DEV_DESTROY:
            raise OSError("destroy")

    with (
        patch.object(uinput_device.os, "open", return_value=mock_fd),
        patch.object(uinput_device.os, "write"),
        patch.object(uinput_device.os, "close") as mock_close,
        patch.object(uinput_device.fcntl, "ioctl", side_effect=ioctl_side_effect),
    ):
        device = uinput_device.UInputDevice((uinput_device.KEY_LEFTSHIFT,))
        device.close()
    mock_close.assert_called_once_with(mock_fd)
