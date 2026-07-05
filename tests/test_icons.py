"""Tests de rutas de iconos."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from utils import icons


def test_icons_dir_dev() -> None:
    """Comprueba icons dir dev."""
    path = icons.icons_dir()
    assert path.name == "icons"
    assert path.parent.name == "assets"


def test_icons_dir_bundled() -> None:
    """Comprueba icons dir bundled."""
    with (
        patch.object(icons.sys, "frozen", True, create=True),
        patch.object(icons.sys, "_MEIPASS", "/tmp/kps-bundle", create=True),
    ):
        assert icons.icons_dir() == Path("/tmp/kps-bundle/assets/icons")


def test_resolve_helpers_missing(tmp_path: Path) -> None:
    """Comprueba resolve helpers missing."""
    with patch.object(icons, "icons_dir", return_value=tmp_path):
        assert icons.windows_ico() is None
        assert icons.macos_icns() is None
        assert icons.linux_appimage_png() is None
        assert icons.tray_icon_path() is None
        assert icons.hicolor_tree() is None


def test_resolve_helpers_present(tmp_path: Path) -> None:
    """Comprueba resolve helpers present."""
    (tmp_path / "kps.ico").write_bytes(b"ico")
    (tmp_path / "kps.icns").write_bytes(b"icns")
    (tmp_path / "kps-tray.png").write_bytes(b"png")
    linux = tmp_path / "linux"
    linux.mkdir()
    (linux / "kps.png").write_bytes(b"png256")
    hicolor = linux / "hicolor" / "256x256" / "apps"
    hicolor.mkdir(parents=True)
    (hicolor / "kps.png").write_bytes(b"png256")

    with patch.object(icons, "icons_dir", return_value=tmp_path):
        assert icons.windows_ico() == tmp_path / "kps.ico"
        assert icons.macos_icns() == tmp_path / "kps.icns"
        assert icons.linux_appimage_png() == linux / "kps.png"
        assert icons.tray_icon_path() == tmp_path / "kps-tray.png"
        assert icons.hicolor_tree() == linux / "hicolor"


def test_pyinstaller_icon_datas_empty(tmp_path: Path) -> None:
    """Comprueba pyinstaller icon datas empty."""
    with patch.object(icons, "_dev_icons_root", return_value=tmp_path):
        assert not icons.pyinstaller_icon_datas()


def test_pyinstaller_icon_datas_with_png(tmp_path: Path) -> None:
    """Comprueba pyinstaller icon datas with png."""
    (tmp_path / "kps.png").write_bytes(b"x")
    with patch.object(icons, "_dev_icons_root", return_value=tmp_path):
        assert icons.pyinstaller_icon_datas() == [(str(tmp_path), "assets/icons")]


def test_load_tray_image_missing() -> None:
    """Comprueba load tray image missing."""
    with patch.object(icons, "tray_icon_path", return_value=None):
        assert icons.load_tray_image() is None


def test_load_tray_image_ok(tmp_path: Path) -> None:
    """Comprueba load tray image ok."""
    png = tmp_path / "kps-tray.png"
    mock_image = MagicMock()
    mock_pil = MagicMock()
    mock_pil.Image.open.return_value.convert.return_value = mock_image
    with (
        patch.object(icons, "tray_icon_path", return_value=png),
        patch.dict("sys.modules", {"PIL": mock_pil, "PIL.Image": mock_pil.Image}),
    ):
        assert icons.load_tray_image() is mock_image
