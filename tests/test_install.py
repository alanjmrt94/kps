"""Tests de utilidades de instalación (sin ejecutar install.sh)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from utils import install
from utils.const import VENV_DIR_NAME


def test_project_root_contains_kps_py() -> None:
    root = install.project_root()
    assert (root / "kps.py").is_file()
    assert (root / "utils").is_dir()


def test_venv_dir_name() -> None:
    assert install.venv_dir() == install.project_root() / VENV_DIR_NAME


def test_detect_os_returns_known_value() -> None:
    assert install.detect_os() in ("linux", "windows", "macos")


def test_requirements_file_exists() -> None:
    req = install.requirements_file()
    assert req.is_file()


def test_platform_install_script_exists() -> None:
    script = install.platform_install_script()
    assert script.is_file()


def test_describe_uinput_issue_when_device_missing() -> None:
    with (
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "Path") as mock_path,
    ):
        mock_path.return_value.exists.return_value = False
        msg = install.describe_uinput_issue()
    assert "/dev/uinput" in msg


def test_run_import_check_without_venv() -> None:
    with patch.object(install, "venv_python", return_value=Path("/no/venv/python")):
        assert install._run_import_check() is False


def test_can_access_uinput_non_linux() -> None:
    with patch.object(install, "detect_os", return_value="windows"):
        assert install.can_access_uinput() is True


def test_venv_has_system_site_packages_missing(tmp_path: Path) -> None:
    with patch.object(install, "venv_dir", return_value=tmp_path):
        assert install.venv_has_system_site_packages() is False


def test_venv_has_system_site_packages_true(tmp_path: Path) -> None:
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text(
        "include-system-site-packages = true\n",
        encoding="utf-8",
    )
    with patch.object(install, "venv_dir", return_value=venv):
        assert install.venv_has_system_site_packages() is True


def test_detect_os_linux() -> None:
    with patch.object(install.os, "name", "posix"), patch.object(install.sys, "platform", "linux"):
        assert install.detect_os() == "linux"
