"""Icono en bandeja del sistema (opcional, requiere kps[gui])."""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable

from utils.status import PresenceStatus, StatusHub

log = logging.getLogger("kps.tray")

_STATUS_COLORS = {
    PresenceStatus.ACTIVE: (46, 160, 67, 255),
    PresenceStatus.AWAY: (230, 162, 60, 255),
    PresenceStatus.PAUSED: (128, 128, 128, 255),
}


def tray_title(base: str, state: PresenceStatus | str) -> str:
    """Título del icono: versión + estado."""
    return f"{base} — {state}"


def tint_tray_image(image: Any, color: tuple[int, int, int, int]) -> Any:
    """Colorea un PIL.Image RGBA con el color de estado (mantiene alpha)."""
    try:
        from PIL import Image  # pylint: disable=import-outside-toplevel
    except ImportError:
        return image
    if image is None:
        return Image.new("RGBA", (64, 64), color)
    overlay = Image.new("RGBA", image.size, color)
    return Image.blend(image.convert("RGBA"), overlay, 0.45)


def apply_tray_state(icon: object, title: str, base_image: object, state: PresenceStatus) -> None:
    """Actualiza título e icono según el estado de presencia."""
    icon.title = tray_title(title, state)  # type: ignore[attr-defined]
    icon.icon = tint_tray_image(base_image, _STATUS_COLORS[state])  # type: ignore[attr-defined]


def _base_image():
    from utils.icons import load_tray_image  # pylint: disable=import-outside-toplevel

    image = load_tray_image()
    if image is None:
        from PIL import Image  # pylint: disable=import-outside-toplevel

        return Image.new("RGB", (64, 64), color=(70, 130, 180))
    return image


def run_with_tray(
    title: str,
    on_quit: Callable[[], None],
    run_main: Callable[[], None],
    status: StatusHub | None = None,
) -> None:
    """Muestra icono en bandeja y ejecuta ``run_main`` en un hilo."""
    try:
        import pystray  # pylint: disable=import-outside-toplevel
    except ImportError as error:
        raise RuntimeError(
            "Modo tray requiere dependencias GUI: pip install \"kps[gui]\""
        ) from error

    hub = status or StatusHub()
    base_image = _base_image()

    def _quit(_icon: object, _item: object) -> None:
        on_quit()
        icon.stop()

    def _status_text(_item: object) -> str:
        return f"Estado: {hub.label()}"

    icon = pystray.Icon(
        "kps",
        tint_tray_image(base_image, _STATUS_COLORS[hub.get()]),
        tray_title(title, hub.get()),
        menu=pystray.Menu(
            pystray.MenuItem(_status_text, None, enabled=False),
            pystray.MenuItem("Salir", _quit),
        ),
    )

    def _watch() -> None:
        last = object()
        while True:
            state = hub.get()
            if state != last:
                apply_tray_state(icon, title, base_image, state)
                last = state
            threading.Event().wait(0.5)

    worker = threading.Thread(target=run_main, name="kps-main", daemon=True)
    worker.start()
    watcher = threading.Thread(target=_watch, name="kps-tray-status", daemon=True)
    watcher.start()
    log.info("Bandeja del sistema activa.")
    icon.run()
