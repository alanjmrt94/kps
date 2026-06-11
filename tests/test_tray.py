"""Tests del modo bandeja."""


# pylint: disable=missing-function-docstring,missing-class-docstring,protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from utils.tray import run_with_tray


def test_run_with_tray_missing_deps() -> None:
    with pytest.raises(RuntimeError, match="kps\\[gui\\]"):
        run_with_tray("kps", lambda: None, lambda: None)


def test_run_with_tray_success() -> None:
    mock_icon = MagicMock()
    mock_menu = MagicMock()
    mock_item = MagicMock()
    mock_pystray = MagicMock()
    mock_pystray.Icon.return_value = mock_icon
    mock_pystray.Menu.return_value = mock_menu
    quit_handler: dict[str, object] = {}

    def capture_menu_item(_label: str, callback: object) -> MagicMock:
        quit_handler["callback"] = callback
        return mock_item

    mock_pystray.MenuItem.side_effect = capture_menu_item
    mock_pil = MagicMock()
    mock_pil.Image.new.return_value = MagicMock()

    called: list[str] = []

    with (
        patch.dict(
            "sys.modules",
            {
                "pystray": mock_pystray,
                "PIL": mock_pil,
                "PIL.Image": mock_pil.Image,
            },
        ),
        patch("utils.tray.threading.Thread") as mock_thread,
    ):
        mock_thread.return_value.start = MagicMock()
        mock_icon.run.side_effect = lambda: called.append("run")
        run_with_tray("kps", lambda: called.append("quit"), lambda: called.append("main"))
        mock_thread.assert_called_once()
        mock_icon.run.assert_called_once()
        quit_cb = quit_handler["callback"]
        assert callable(quit_cb)
        quit_cb(mock_icon, None)
        assert called == ["run", "quit"]
        mock_icon.stop.assert_called_once()
