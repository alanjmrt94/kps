"""kps — evita inactividad moviendo el cursor cuando el usuario está ausente."""

import os
import sys

from utils.cli import parse_args, print_banner, setup_logging
from utils.version import App_version
from utils.daemon import remove_pid_file, spawn_daemon, write_pid_file
from utils.install import setup_environment
from utils.runner import run_loop
from utils.shutdown import ShutdownController
from utils.status import StatusHub


def _run_main(config, shutdown, status=None) -> None:
    """Setup del entorno y bucle principal."""
    setup_environment()
    run_loop(config, shutdown, status=status)


def main() -> None:
    """Punto de entrada: CLI, setup del entorno y bucle principal."""
    config = parse_args()

    if config.command == "doctor":
        from utils.doctor import run_doctor  # pylint: disable=import-outside-toplevel

        sys.exit(run_doctor())

    if config.command == "autostart":
        from utils.autostart import run_autostart  # pylint: disable=import-outside-toplevel

        sys.exit(run_autostart(config.autostart_action))

    if config.daemon and not config.foreground:
        spawn_daemon()

    log = setup_logging(config)
    print_banner(log, config)

    shutdown = ShutdownController()
    shutdown.install_signal_handlers()
    shutdown.start_hotkey_listener(config.hotkey)
    status = StatusHub()

    if config.pid_file:
        write_pid_file(config.pid_file)
        log.debug("PID %s escrito en %s", os.getpid(), config.pid_file)

    try:
        if config.tray:
            from utils.tray import run_with_tray  # pylint: disable=import-outside-toplevel

            def _worker() -> None:
                try:
                    _run_main(config, shutdown, status)
                except RuntimeError as error:
                    log.error("%s", error)

            run_with_tray(
                f"kps {App_version()}",
                lambda: shutdown.request("bandeja"),
                _worker,
                status=status,
            )
        else:
            _run_main(config, shutdown, status)
    except RuntimeError as error:
        log.error("%s", error)
        sys.exit(1)
    except KeyboardInterrupt:
        shutdown.request("Ctrl+C")
        log.info("Detenido por el usuario.")
    finally:
        remove_pid_file(config.pid_file)

    sys.exit(0)


if __name__ == "__main__":
    main()
