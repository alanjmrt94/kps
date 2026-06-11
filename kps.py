"""kps — evita inactividad moviendo el cursor cuando el usuario está ausente."""

import os
import sys

from utils.cli import parse_args, print_banner, setup_logging
from utils.daemon import remove_pid_file, spawn_daemon, write_pid_file
from utils.install import setup_environment
from utils.runner import run_loop
from utils.shutdown import ShutdownController


def main() -> None:
    """Punto de entrada: CLI, setup del entorno y bucle principal."""
    config = parse_args()

    if config.daemon and not config.foreground:
        spawn_daemon()

    log = setup_logging(config)
    print_banner(log, config)

    shutdown = ShutdownController()
    shutdown.install_signal_handlers()
    shutdown.start_hotkey_listener(config.hotkey)

    if config.pid_file:
        write_pid_file(config.pid_file)
        log.debug("PID %s escrito en %s", os.getpid(), config.pid_file)

    try:
        setup_environment()
        run_loop(config, shutdown)
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
