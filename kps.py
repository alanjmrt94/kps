"""kps — evita inactividad moviendo el cursor cuando el usuario está ausente."""

import sys

from utils.cli import parse_args, print_banner, setup_logging
from utils.install import setup_environment
from utils.runner import run_loop


def main() -> None:
    """Punto de entrada: CLI, setup del entorno y bucle principal."""
    config = parse_args()
    log = setup_logging(config)
    print_banner(log)

    try:
        setup_environment()
    except RuntimeError as error:
        log.error("%s", error)
        sys.exit(1)

    try:
        run_loop(config)
    except KeyboardInterrupt:
        log.info("Detenido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
