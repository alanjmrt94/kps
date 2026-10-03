"""Tests de autostart."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

from utils.autostart import (
    desktop_entry,
    disable_linux,
    enable_linux,
    launch_command,
    quoted_exec,
    run_autostart,
    systemd_unit,
)


def test_quoted_exec_spaces() -> None:
    """Comprueba quoted exec spaces."""
    line = quoted_exec(["/home/user/My App/kps.AppImage", "--tray"])
    assert "--tray" in line
    assert "My App" in line or "My\\ App" in line or "'/home/user/My App/kps.AppImage'" in line


def test_desktop_and_unit_contain_exec() -> None:
    """Comprueba desktop and unit contain exec."""
    cmd = ["/opt/kps.AppImage", "--tray", "--foreground"]
    desktop = desktop_entry(cmd)
    unit = systemd_unit(cmd)
    assert "Exec=" in desktop
    assert "ExecStart=" in unit
    assert "kps.AppImage" in desktop
    assert "graphical-session.target" in unit


def test_launch_command_prefers_appimage(monkeypatch) -> None:
    """Comprueba launch command prefers appimage."""
    monkeypatch.setenv("APPIMAGE", "/tmp/kps-x86_64.AppImage")
    cmd = launch_command()
    assert cmd[0] == "/tmp/kps-x86_64.AppImage"
    assert "--tray" in cmd


def test_enable_disable_linux(tmp_path: Path, monkeypatch) -> None:
    """Comprueba enable disable linux."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    with patch("utils.autostart._systemctl_user", return_value=False):
        notes = enable_linux()
    desktop = tmp_path / "autostart" / "kps.desktop"
    unit = tmp_path / "systemd" / "user" / "kps.service"
    assert desktop.is_file()
    assert unit.is_file()
    assert notes
    with patch("utils.autostart._systemctl_user", return_value=True):
        disable_linux()
    assert not desktop.exists()
    assert not unit.exists()


def test_run_autostart_status(capsys) -> None:
    """Comprueba run autostart status."""
    code = run_autostart("status")
    assert code == 0
    out = capsys.readouterr().out
    assert "Comando:" in out


def test_enable_macos_and_windows(tmp_path: Path) -> None:
    """Comprueba enable macos and windows."""
    from utils import autostart as auto

    plist = tmp_path / "kps.plist"
    bat = tmp_path / "kps.bat"
    with (
        patch.object(auto, "macos_launch_agent_path", return_value=plist),
        patch.object(auto, "windows_startup_path", return_value=bat),
        patch.object(auto.subprocess, "run"),
    ):
        assert auto.enable_macos()
        assert plist.is_file()
        assert auto.disable_macos()
        assert auto.enable_windows()
        assert bat.is_file()
        assert auto.disable_windows()


def test_run_autostart_enable_linux(tmp_path: Path, monkeypatch, capsys) -> None:
    """Comprueba run autostart enable linux."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    with (
        patch.object(sys, "platform", "linux"),
        patch("utils.autostart._systemctl_user", return_value=True),
    ):
        assert run_autostart("enable") == 0
        assert run_autostart("disable") == 0
    assert "Autostart" in capsys.readouterr().out


def test_run_autostart_enable_macos_windows(tmp_path: Path, capsys) -> None:
    """Comprueba run autostart enable macos windows."""
    from utils import autostart as auto

    plist = tmp_path / "a.plist"
    bat = tmp_path / "a.bat"
    with (
        patch.object(sys, "platform", "darwin"),
        patch.object(auto, "macos_launch_agent_path", return_value=plist),
        patch.object(auto.subprocess, "run"),
    ):
        assert auto.run_autostart("enable") == 0
        assert auto.run_autostart("disable") == 0
    with (
        patch.object(sys, "platform", "win32"),
        patch.object(auto, "windows_startup_path", return_value=bat),
    ):
        assert auto.run_autostart("enable") == 0
        assert auto.run_autostart("disable") == 0
    capsys.readouterr()


def test_status_paths_other_platforms(tmp_path: Path) -> None:
    """Comprueba status paths other platforms."""
    from utils import autostart as auto

    with (
        patch.object(sys, "platform", "darwin"),
        patch.object(auto, "macos_launch_agent_path", return_value=tmp_path / "x.plist"),
    ):
        rows = auto.status_paths()
        assert rows[0][0] == "LaunchAgent"
    with (
        patch.object(sys, "platform", "win32"),
        patch.object(auto, "windows_startup_path", return_value=tmp_path / "x.bat"),
    ):
        rows = auto.status_paths()
        assert rows[0][0] == "Inicio"


def test_launch_command_bundled() -> None:
    """Comprueba launch command bundled."""
    with (
        patch("utils.autostart.os.environ.get", return_value=None),
        patch("utils.autostart.is_bundled", return_value=True),
    ):
        cmd = launch_command()
    assert cmd[0]
    assert "--tray" in cmd


def test_systemctl_and_remove(tmp_path: Path) -> None:
    """Comprueba systemctl and remove."""
    from utils.autostart import _remove, _systemctl_user

    assert _remove(tmp_path / "missing") is False
    with patch("utils.autostart.subprocess.run", side_effect=OSError("no")):
        assert _systemctl_user("status") is False
    with patch("utils.autostart.subprocess.run", return_value=MagicMock()):
        assert _systemctl_user("status") is True


def test_disable_linux_empty(tmp_path: Path, monkeypatch) -> None:
    """Comprueba disable linux empty."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    with patch("utils.autostart._systemctl_user", return_value=True):
        notes = disable_linux()
    assert "no había" in notes[0]


def test_macos_plist_escapes() -> None:
    """Comprueba macos plist escapes."""
    from utils.autostart import macos_plist

    text = macos_plist(["/bin/kps", "a&b<c>"])
    assert "&amp;" in text
    assert "&lt;" in text


def test_windows_paths_without_appdata(monkeypatch) -> None:
    """Comprueba windows paths without appdata."""
    from utils.autostart import windows_startup_path

    monkeypatch.delenv("APPDATA", raising=False)
    path = windows_startup_path()
    assert "Startup" in str(path)


def test_enable_macos_launchctl_oserror(tmp_path: Path) -> None:
    """Comprueba enable macos launchctl oserror."""
    from utils import autostart as auto

    path = tmp_path / "kps.plist"
    with (
        patch.object(auto, "macos_launch_agent_path", return_value=path),
        patch.object(auto.subprocess, "run", side_effect=OSError("x")),
    ):
        auto.enable_macos()
        auto.disable_macos()
    assert not path.exists()


def test_disable_windows_missing(tmp_path: Path) -> None:
    """Comprueba disable windows missing."""
    from utils import autostart as auto

    with patch.object(auto, "windows_startup_path", return_value=tmp_path / "no.bat"):
        assert "no había" in auto.disable_windows()[0]
