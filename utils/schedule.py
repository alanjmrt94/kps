"""Horarios de activación de perfiles (HH:MM, incluye tramos nocturnos)."""

from __future__ import annotations

import datetime as dt
from typing import Optional


def parse_hhmm(value: str | None) -> Optional[dt.time]:
    """Parsea ``HH:MM``; None si falta o es inválido."""
    if not value:
        return None
    text = value.strip()
    try:
        parsed = dt.datetime.strptime(text, "%H:%M")
    except ValueError:
        return None
    return parsed.time()


def is_within_window(
    now: dt.time,
    start: dt.time | None,
    end: dt.time | None,
) -> bool:
    """
    True si ``now`` está en [start, end).

    Si start > end, el tramo cruza medianoche (p. ej. 22:00–07:00).
    Sin start y end, siempre activo.
    """
    if start is None and end is None:
        return True
    if start is None or end is None:
        return True
    if start == end:
        return True
    if start < end:
        return start <= now < end
    return now >= start or now < end


def schedule_allows(start_raw: str | None, end_raw: str | None, now: dt.time | None = None) -> bool:
    """True si el horario del perfil admite pulsos ahora."""
    current = now if now is not None else dt.datetime.now().time().replace(microsecond=0)
    return is_within_window(current, parse_hhmm(start_raw), parse_hhmm(end_raw))
