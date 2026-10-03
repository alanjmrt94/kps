"""Tests del modo bandeja."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from utils.tray import run_with_tray, tray_title
from utils.status import PresenceStatus


def test_run_with_tray_missing_deps() -> None:
    """Comprueba run with tray missing deps."""
    with pytest.raises(RuntimeError, match="kps\\[gui\\]"):
        run_with_tray("kps", lambda: None, lambda: None)


def test_run_with_tray_success() -> None:
    """Comprueba run with tray success."""
    mock_icon = MagicMock()
    mock_menu = MagicMock()
    mock_item = MagicMock()
    mock_pystray = MagicMock()
    mock_pystray.Icon.return_value = mock_icon
    mock_pystray.Menu.return_value = mock_menu
    quit_handler: dict[str, object] = {}

    def capture_menu_item(*args: object, **_kwargs: object) -> MagicMock:
        if len(args) >= 2 and callable(args[1]):
            quit_handler["callback"] = args[1]
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
        patch("utils.icons.load_tray_image", return_value=None),
        patch("utils.tray.threading.Thread") as mock_thread,
    ):
        mock_thread.return_value.start = MagicMock()
        mock_icon.run.side_effect = lambda: called.append("run")
        run_with_tray("kps", lambda: called.append("quit"), lambda: called.append("main"))
        mock_thread.assert_called()
        mock_icon.run.assert_called_once()
        quit_cb = quit_handler["callback"]
        assert callable(quit_cb)
        quit_cb(mock_icon, None)
        assert called == ["run", "quit"]
        mock_icon.stop.assert_called_once()


def test_tint_tray_image_without_pil() -> None:
    """Comprueba tint tray image without pil."""
    from utils.tray import tint_tray_image

    sentinel = object()
    with patch.dict("sys.modules", {"PIL": None, "PIL.Image": None}):
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "PIL" or name.startswith("PIL."):
                raise ImportError
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", fake_import):
            assert tint_tray_image(sentinel, (1, 2, 3, 4)) is sentinel


def test_tray_title_includes_status() -> None:
    """Comprueba tray title includes status."""
    assert tray_title("kps 2.1.0", PresenceStatus.AWAY) == "kps 2.1.0 — ausente"


def test_apply_tray_state() -> None:
    """Comprueba apply tray state."""
    from utils.tray import apply_tray_state

    icon = MagicMock()
    apply_tray_state(icon, "kps", MagicMock(), PresenceStatus.PAUSED)
    assert "pausado" in icon.title


def test_base_image_from_assets() -> None:
    """Comprueba base image from assets."""
    from utils.tray import _base_image

    sentinel = object()
    with patch("utils.icons.load_tray_image", return_value=sentinel):
        assert _base_image() is sentinel
