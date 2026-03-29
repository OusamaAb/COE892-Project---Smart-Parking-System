"""
In-memory global lot clock for the current process only (not persisted).

- Starts at 9:00 AM on a fixed fictional calendar date.
- Every REAL_SECONDS_PER_TICK wall-clock seconds, SIM_MINUTES_PER_TICK
  simulated minutes are added.
"""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timedelta

# Tunables
SIM_START = datetime(2020, 1, 1, 9, 0, 0)
REAL_SECONDS_PER_TICK = 30
SIM_MINUTES_PER_TICK = 15

_lock = threading.Lock()
_sim_now: datetime = SIM_START


def get_sim_now() -> datetime:
    with _lock:
        return _sim_now


def reset_sim_clock() -> None:
    """Reset to 9:00 AM (e.g. on service startup)."""
    global _sim_now
    with _lock:
        _sim_now = SIM_START


def advance_sim_clock() -> datetime:
    global _sim_now
    with _lock:
        _sim_now += timedelta(minutes=SIM_MINUTES_PER_TICK)
        return _sim_now


def format_lot_time(dt: datetime) -> str:
    """e.g. '9:00 AM' / '2:45 PM'"""
    h24 = dt.hour
    h = h24 % 12
    if h == 0:
        h = 12
    ampm = "AM" if h24 < 12 else "PM"
    return f"{h}:{dt.minute:02d} {ampm}"


async def clock_tick_loop(on_tick) -> None:
    """Sleep REAL_SECONDS_PER_TICK, advance clock, call async on_tick()."""
    while True:
        await asyncio.sleep(REAL_SECONDS_PER_TICK)
        advance_sim_clock()
        await on_tick()
