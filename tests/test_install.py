"""Tests de utilidades de instalación (sin ejecutar install.sh)."""


# pylint: disable=protected-access,import-outside-toplevel,consider-using-from-import
from __future__ import annotations

import builtins
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from utils import install
from utils.const import VENV_DIR_NAME


def test_project_root_contains_kps_py() -> None:
    """Comprueba project root contains kps py."""
    root = install.project_root()
    assert (root / "kps.py").is_file()
    assert (root / "utils").is_dir()


def test_scripts_dir() -> None:
    """Comprueba scripts dir."""
    assert install.scripts_dir() == install.project_root() / "scripts"


def test_venv_dir_name() -> None:
    """Comprueba venv dir name."""
    assert install.venv_dir() == install.project_root() / VENV_DIR_NAME


def test_venv_python_and_pip_paths() -> None:
    """Comprueba venv python and pip paths."""
    with patch.object(install.sys, "platform", "linux"):
        assert install.venv_python().name == "python3"
        assert install.venv_pip().name == "pip"
    with patch.object(install.sys, "platform", "win32"):
        assert install.venv_python().name == "python.exe"
        assert install.venv_pip().name == "pip.exe"


def test_detect_os_variants() -> None:
    """Comprueba detect os variants."""
    with patch.object(install.os, "name", "posix"), patch.object(install.sys, "platform", "linux"):
        assert install.detect_os() == "linux"
    with patch.object(install.os, "name", "nt"):
        assert install.detect_os() == "windows"
    with patch.object(install.os, "name", "posix"), patch.object(install.sys, "platform", "darwin"):
        assert install.detect_os() == "macos"


def test_requirements_and_install_script_exist() -> None:
    """Comprueba requirements and install script exist."""
    assert install.requirements_file().is_file()
    assert install.platform_install_script().is_file()


def test_run_subprocess() -> None:
    """Comprueba run subprocess."""
    with patch.object(install.subprocess, "run") as mock_run:
        install._run(["echo", "ok"])
        mock_run.assert_called_once()


def test_run_platform_install_linux() -> None:
    """Comprueba run platform install linux."""
    with (
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "_run") as mock_run,
    ):
        install.run_platform_install()
        mock_run.assert_called_once()


def test_run_platform_install_windows() -> None:
    """Comprueba run platform install windows."""
    with (
        patch.object(install, "detect_os", return_value="windows"),
        patch.object(install, "_run") as mock_run,
    ):
        install.run_platform_install()
        mock_run.assert_called_with([str(install.platform_install_script())], shell=True)


def test_run_platform_install_missing_script(tmp_path: Path) -> None:
    """Comprueba run platform install missing script."""
    with patch.object(install, "platform_install_script", return_value=tmp_path / "nope.sh"):
        with pytest.raises(FileNotFoundError):
            install.run_platform_install()


def test_venv_has_system_site_packages_missing(tmp_path: Path) -> None:
    """Comprueba venv has system site packages missing."""
    with patch.object(install, "venv_dir", return_value=tmp_path):
        assert install.venv_has_system_site_packages() is False


def test_venv_has_system_site_packages_true(tmp_path: Path) -> None:
    """Comprueba venv has system site packages true."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("include-system-site-packages = true\n", encoding="utf-8")
    with patch.object(install, "venv_dir", return_value=venv):
        assert install.venv_has_system_site_packages() is True


def test_ensure_venv_existing_compatible(tmp_path: Path) -> None:
    """Comprueba ensure venv existing compatible."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("include-system-site-packages = false\n", encoding="utf-8")
    with (
        patch.object(install, "venv_dir", return_value=venv),
        patch.object(install, "detect_os", return_value="linux"),
    ):
        assert install.ensure_venv() == venv


def test_ensure_venv_recreate_legacy_system_packages(tmp_path: Path) -> None:
    """Comprueba ensure venv recreate legacy system packages."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("include-system-site-packages = true\n", encoding="utf-8")
    with (
        patch.object(install, "venv_dir", return_value=venv),
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install.shutil, "rmtree") as mock_rm,
        patch.object(install, "_run"),
    ):
        install.ensure_venv()
        mock_rm.assert_called_once_with(venv)


def test_ensure_venv_create_new(tmp_path: Path) -> None:
    """Comprueba ensure venv create new."""
    venv = tmp_path / ".venv"
    with (
        patch.object(install, "venv_dir", return_value=venv),
        patch.object(install, "detect_os", return_value="windows"),
        patch.object(install, "_run") as mock_run,
    ):
        install.ensure_venv()
        mock_run.assert_called_once()


def test_install_pip_deps(tmp_path: Path) -> None:
    """Comprueba install pip deps."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    pip = venv / "bin" / "pip"
    pip.parent.mkdir(parents=True)
    pip.touch()
    with (
        patch.object(install, "ensure_venv", return_value=venv),
        patch.object(install, "venv_pip", return_value=pip),
        patch.object(install, "_run") as mock_run,
    ):
        install.install_pip_deps()
        assert mock_run.call_count == 2


def test_install_pip_deps_missing_requirements(tmp_path: Path) -> None:
    """Comprueba install pip deps missing requirements."""
    with patch.object(install, "requirements_file", return_value=tmp_path / "missing.txt"):
        with pytest.raises(FileNotFoundError):
            install.install_pip_deps()


def test_import_check_and_verify() -> None:
    """Comprueba import check and verify."""
    ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    fail = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="err")
    py = MagicMock()
    py.is_file.return_value = True
    with (
        patch.object(install, "venv_python", return_value=py),
        patch.object(install, "_import_check_result", return_value=ok),
    ):
        assert install._run_import_check() is True
        assert install.verify_imports() is True
        assert install.test_package() is True
    with patch.object(install, "_import_check_result", return_value=fail):
        assert install.verify_imports() is False


def test_verify_imports_no_python() -> None:
    """Comprueba verify imports no python."""
    with patch.object(install, "venv_python", return_value=Path("/no/python")):
        assert install.verify_imports() is False


def test_describe_uinput_paths() -> None:
    """Comprueba describe uinput paths."""
    with (
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "Path") as mock_path,
    ):
        mock_path.return_value.exists.return_value = False
        assert "uinput" in install.describe_uinput_issue()
    with (
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "can_access_uinput", return_value=True),
        patch.object(install, "Path") as mock_path,
    ):
        mock_path.return_value.exists.return_value = True
        assert install.describe_uinput_issue() == ""
    with (
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "can_access_uinput", return_value=False),
        patch.object(install, "is_in_uinput_group", return_value=True),
        patch.object(install, "Path") as mock_path,
    ):
        mock_path.return_value.exists.return_value = True
        assert "Cierra sesión" in install.describe_uinput_issue()
    with (
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "can_access_uinput", return_value=False),
        patch.object(install, "is_in_uinput_group", return_value=False),
        patch.object(install, "Path") as mock_path,
    ):
        mock_path.return_value.exists.return_value = True
        assert "install.sh" in install.describe_uinput_issue()


def test_is_in_uinput_group_no_grp_module() -> None:
    """Comprueba is in uinput group no grp module."""
    real_import = builtins.__import__

    def fake_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "grp":
            raise ModuleNotFoundError("No module named 'grp'")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=fake_import):
        assert install.is_in_uinput_group() is False


def test_is_in_uinput_group() -> None:
    """Comprueba is in uinput group."""
    fake_grp = MagicMock()
    fake_grp.getgrnam.side_effect = KeyError
    with patch.dict(sys.modules, {"grp": fake_grp}):
        assert install.is_in_uinput_group() is False
    group = MagicMock(gr_gid=42)
    fake_grp.getgrnam.side_effect = None
    fake_grp.getgrnam.return_value = group
    with (
        patch.dict(sys.modules, {"grp": fake_grp}),
        patch.object(install.os, "getgroups", return_value=[42], create=True),
    ):
        assert install.is_in_uinput_group() is True


def test_can_access_uinput() -> None:
    """Comprueba can access uinput."""
    with patch.object(install, "detect_os", return_value="windows"):
        assert install.can_access_uinput() is True
    with (
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "Path") as mock_path,
        patch.object(install.os, "access", return_value=True),
    ):
        mock_path.return_value.exists.return_value = True
        assert install.can_access_uinput() is True


def test_verify_uinput_device() -> None:
    """Comprueba verify uinput device."""
    py = MagicMock()
    py.is_file.return_value = True
    ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    fail = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="denied")
    with (
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "venv_python", return_value=py),
        patch.object(install.subprocess, "run", return_value=ok),
    ):
        assert install.verify_uinput_device() is True
        assert install.verify_uinput_device(quiet=True) is True
    with (
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "venv_python", return_value=py),
        patch.object(install.subprocess, "run", return_value=fail),
        patch.object(install, "describe_uinput_issue", return_value="hint"),
    ):
        assert install.verify_uinput_device() is False
    fail_no_hint = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="")
    with (
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "venv_python", return_value=py),
        patch.object(install.subprocess, "run", return_value=fail_no_hint),
        patch.object(install, "describe_uinput_issue", return_value=""),
    ):
        assert install.verify_uinput_device() is False
    with patch.object(install, "detect_os", return_value="windows"):
        assert install.verify_uinput_device() is True


def test_verify_runtime_success(tmp_path: Path) -> None:
    """Comprueba verify runtime success."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    with (
        patch.object(install, "venv_dir", return_value=venv),
        patch.object(install, "_run_import_check", return_value=True),
        patch.object(install, "detect_os", return_value="windows"),
    ):
        install.verify_runtime()


def test_verify_runtime_failures(tmp_path: Path) -> None:
    """Comprueba verify runtime failures."""
    with patch.object(install, "venv_dir", return_value=tmp_path / "missing"):
        with pytest.raises(RuntimeError, match="entorno virtual"):
            install.verify_runtime()
    venv = tmp_path / ".venv"
    venv.mkdir()
    with (
        patch.object(install, "venv_dir", return_value=venv),
        patch.object(install, "_run_import_check", return_value=False),
    ):
        with pytest.raises(RuntimeError, match="imports"):
            install.verify_runtime()


def test_verify_setup_alias() -> None:
    """Comprueba verify setup alias."""
    with patch.object(install, "verify_runtime") as mock_rt:
        install.verify_setup()
        mock_rt.assert_called_once()


def test_ensure_venv_runtime_noop_and_exec(tmp_path: Path) -> None:
    """Comprueba ensure venv runtime noop and exec."""
    missing = tmp_path / "missing" / "python3"
    with patch.object(install, "venv_python", return_value=missing):
        install.ensure_venv_runtime()

    vpy = tmp_path / "venv" / "bin" / "python3"
    vpy.parent.mkdir(parents=True)
    vpy.touch()
    with (
        patch.object(install, "venv_python", return_value=vpy),
        patch.object(install.sys, "executable", str(vpy.resolve())),
    ):
        install.ensure_venv_runtime()

    with (
        patch.object(install, "venv_python", return_value=vpy),
        patch.object(install.sys, "executable", "/usr/bin/python3"),
        patch.object(install.os, "execv", side_effect=SystemExit) as mock_exec,
    ):
        with pytest.raises(SystemExit):
            install.ensure_venv_runtime()
        mock_exec.assert_called_once()


def test_setup_environment_and_autoinstall() -> None:
    """Comprueba setup environment and autoinstall."""
    with (
        patch.object(install, "ensure_venv_runtime"),
        patch.object(install, "venv_dir") as mock_venv,
        patch.object(install, "_run_import_check", return_value=True),
        patch.object(install, "verify_runtime") as mock_verify,
    ):
        mock_venv.return_value.is_dir.return_value = True
        install.setup_environment()
        mock_verify.assert_called_once()
    with (
        patch.object(install, "ensure_venv_runtime"),
        patch.object(install, "venv_dir") as mock_venv,
        patch.object(install, "_run_import_check", return_value=False),
        patch.object(install, "autoinstall") as mock_auto,
        patch.object(install, "verify_runtime"),
    ):
        mock_venv.return_value.is_dir.return_value = False
        install.setup_environment()
        mock_auto.assert_called_once()
    with (
        patch.object(install, "run_platform_install"),
        patch.object(install, "verify_imports", return_value=True),
    ):
        install.autoinstall()
    with (
        patch.object(install, "run_platform_install"),
        patch.object(install, "verify_imports", return_value=False),
    ):
        with pytest.raises(RuntimeError):
            install.autoinstall()


def test_autoinstall_alias() -> None:
    """Comprueba autoinstall alias."""
    assert install.Autoinstall is install.autoinstall


def test_verify_runtime_linux_success(tmp_path: Path) -> None:
    """Comprueba verify runtime linux success."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    with (
        patch.object(install, "venv_dir", return_value=venv),
        patch.object(install, "_run_import_check", return_value=True),
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "describe_uinput_issue", return_value=""),
        patch.object(install, "verify_uinput_device", return_value=True),
    ):
        install.verify_runtime()


def test_verify_runtime_linux_uinput_issue(tmp_path: Path) -> None:
    """Comprueba verify runtime linux uinput issue."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    with (
        patch.object(install, "venv_dir", return_value=venv),
        patch.object(install, "_run_import_check", return_value=True),
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "describe_uinput_issue", return_value="sin acceso"),
    ):
        with pytest.raises(RuntimeError, match="sin acceso"):
            install.verify_runtime()


def test_verify_runtime_linux_uinput_verify_fail(tmp_path: Path) -> None:
    """Comprueba verify runtime linux uinput verify fail."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    with (
        patch.object(install, "venv_dir", return_value=venv),
        patch.object(install, "_run_import_check", return_value=True),
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "describe_uinput_issue", return_value=""),
        patch.object(install, "verify_uinput_device", return_value=False),
    ):
        with pytest.raises(RuntimeError, match="uinput"):
            install.verify_runtime()


def test_import_check_result_no_python() -> None:
    """Comprueba import check result no python."""
    missing_python = MagicMock()
    missing_python.is_file.return_value = False
    with patch.object(install, "venv_python", return_value=missing_python):
        assert install._run_import_check() is False


def test_verify_imports_failure_empty_stderr() -> None:
    """Comprueba verify imports failure empty stderr."""
    fail = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="")
    py = MagicMock()
    py.is_file.return_value = True
    with (
        patch.object(install, "venv_python", return_value=py),
        patch.object(install, "_import_check_result", return_value=fail),
    ):
        assert install.verify_imports() is False


def test_verify_imports_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    """Comprueba verify imports stderr."""
    fail = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="import fail")
    py = MagicMock()
    py.is_file.return_value = True
    with (
        patch.object(install, "venv_python", return_value=py),
        patch.object(install, "_import_check_result", return_value=fail),
    ):
        assert install.verify_imports() is False
    assert "import fail" in capsys.readouterr().out


def test_install_pip_deps_missing_pip(tmp_path: Path) -> None:
    """Comprueba install pip deps missing pip."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    with (
        patch.object(install, "ensure_venv", return_value=venv),
        patch.object(install, "venv_pip", return_value=venv / "bin" / "pip"),
        patch.object(
            install, "requirements_file", return_value=install.requirements_file()
        ),
    ):
        with pytest.raises(FileNotFoundError, match="pip"):
            install.install_pip_deps()


def test_import_check_result_runs_subprocess() -> None:
    """Comprueba import check result runs subprocess."""
    py = MagicMock()
    py.is_file.return_value = True
    ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with (
        patch.object(install, "venv_python", return_value=py),
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install.subprocess, "run", return_value=ok) as mock_run,
    ):
        assert install._import_check_result().returncode == 0
        mock_run.assert_called_once()


def test_verify_uinput_device_no_python() -> None:
    """Comprueba verify uinput device no python."""
    missing_python = MagicMock()
    missing_python.is_file.return_value = False
    with (
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "venv_python", return_value=missing_python),
    ):
        assert install.verify_uinput_device() is False


def test_can_access_uinput_missing_device() -> None:
    """Comprueba can access uinput missing device."""
    with (
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "Path") as mock_path,
    ):
        mock_path.return_value.exists.return_value = False
        assert install.can_access_uinput() is False


def test_ensure_venv_existing_returns_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Comprueba ensure venv existing returns path."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("include-system-site-packages = false\n", encoding="utf-8")
    with (
        patch.object(install, "venv_dir", return_value=venv),
        patch.object(install, "detect_os", return_value="linux"),
    ):
        assert install.ensure_venv() == venv
    assert "existente" in capsys.readouterr().out


def test_is_bundled() -> None:
    """Comprueba is bundled."""
    with patch.object(install.sys, "frozen", True, create=True):
        assert install.is_bundled() is True
    with patch.object(install.sys, "frozen", False, create=True):
        assert install.is_bundled() is False
    if hasattr(install.sys, "frozen"):
        delattr(install.sys, "frozen")
    assert install.is_bundled() is False


def test_project_root_bundled() -> None:
    """Comprueba project root bundled."""
    executable = Path("/opt/kps/kps")
    with (
        patch.object(install, "is_bundled", return_value=True),
        patch.object(install.sys, "executable", str(executable)),
    ):
        assert install.project_root() == executable.resolve().parent


def test_setup_environment_bundled() -> None:
    """Comprueba setup environment bundled."""
    with (
        patch.object(install, "is_bundled", return_value=True),
        patch.object(install, "verify_bundled_runtime") as mock_verify,
        patch.object(install, "ensure_venv_runtime") as mock_venv,
    ):
        install.setup_environment()
        mock_verify.assert_called_once()
        mock_venv.assert_not_called()


def test_verify_bundled_runtime_linux() -> None:
    """Comprueba verify bundled runtime linux."""
    with (
        patch.object(install, "_run_import_check", return_value=True),
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "describe_uinput_issue", return_value=""),
        patch.object(install, "verify_uinput_device", return_value=True),
    ):
        install.verify_bundled_runtime()


def test_verify_bundled_runtime_import_fail() -> None:
    """Comprueba verify bundled runtime import fail."""
    with patch.object(install, "_run_import_check", return_value=False):
        with pytest.raises(RuntimeError, match="empaquetado"):
            install.verify_bundled_runtime()


def test_run_import_check_bundled_inprocess() -> None:
    """Comprueba run import check bundled inprocess."""
    with (
        patch.object(install, "is_bundled", return_value=True),
        patch.object(install, "_import_check_inprocess", return_value=True) as mock_check,
    ):
        assert install._run_import_check() is True
        mock_check.assert_called_once()


def test_verify_uinput_device_bundled() -> None:
    """Comprueba verify uinput device bundled."""
    with (
        patch.object(install, "is_bundled", return_value=True),
        patch.object(install, "detect_os", return_value="linux"),
        patch.object(install, "_uinput_check_inprocess", return_value=True),
    ):
        assert install.verify_uinput_device(quiet=True) is True


def test_verify_runtime_delegates_to_bundled() -> None:
    """Comprueba verify runtime delegates to bundled."""
    with (
        patch.object(install, "is_bundled", return_value=True),
        patch.object(install, "verify_bundled_runtime") as mock_bundled,
    ):
        install.verify_runtime()
        mock_bundled.assert_called_once()
