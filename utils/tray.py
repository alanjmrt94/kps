"""Icono en bandeja del sistema (opcional, requiere kps[gui])."""

from __future__ import annotations

import logging
import threading
from typing import Callable

log = logging.getLogger("kps.tray")


def run_with_tray(title: str, on_quit: Callable[[], None], run_main: Callable[[], None]) -> None:
    """Muestra icono en bandeja y ejecuta ``run_main`` en un hilo."""
    try:
        import pystray  # pylint: disable=import-outside-toplevel
    except ImportError as error:
        raise RuntimeError(
            "Modo tray requiere dependencias GUI: pip install \"kps[gui]\""
        ) from error

    from utils.icons import load_tray_image  # pylint: disable=import-outside-toplevel

    image = load_tray_image()
    if image is None:
        from PIL import Image  # pylint: disable=import-outside-toplevel

        image = Image.new("RGB", (64, 64), color=(70, 130, 180))

    def _quit(_icon: object, _item: object) -> None:
        on_quit()
        icon.stop()

    icon = pystray.Icon(
        "kps",
        image,
        title,
        menu=pystray.Menu(pystray.MenuItem("Salir", _quit)),
    )

    worker = threading.Thread(target=run_main, name="kps-main", daemon=True)
    worker.start()
    log.info("Bandeja del sistema activa.")
    icon.run()
