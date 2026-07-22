#!/usr/bin/env python3
"""Держит систему «активной» для Teams — только при простое и в рабочие часы.

- Дёргает мышь ТОЛЬКО если простой > 3 минут (система реально не используется)
- Активен ТОЛЬКО в окне 04:00–12:00
- Закрытие крышки / сон macOS не блокирует
"""

import time
import random
import logging
from datetime import datetime
import Quartz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler("/Users/skozar/Projects/pets/keepalive/keepalive.log"),
        logging.StreamHandler(),
    ],
)

ACTIVE_START = 4   # 04:00
ACTIVE_END = 12    # 12:00
IDLE_THRESHOLD = 180  # 3 минуты — дёргаем только при реальном простое


def idle_seconds() -> float:
    """Seconds since last user input (keyboard or mouse)."""
    return Quartz.CGEventSourceSecondsSinceLastEventType(
        Quartz.kCGEventSourceStateCombinedSessionState,
        Quartz.kCGAnyInputEventType,
    )


def in_active_window() -> bool:
    """True if current hour is within [ACTIVE_START, ACTIVE_END)."""
    hour = datetime.now().hour
    return ACTIVE_START <= hour < ACTIVE_END


def jiggle():
    """Move cursor 1 pixel right and back — imperceptible but resets idle timer."""
    pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    x, y = int(pos.x), int(pos.y)

    move = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, (x + 1, y), 0
    )
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, move)
    time.sleep(0.05)

    move = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, (x, y), 0
    )
    Quartz.CGEventPost(Quartz.kCGSessionEventTap, move)


if __name__ == "__main__":
    logging.info(
        "Started — active %02d:00–%02d:00, idle threshold %ds",
        ACTIVE_START, ACTIVE_END, IDLE_THRESHOLD,
    )

    try:
        while True:
            if in_active_window():
                idle = idle_seconds()
                if idle >= IDLE_THRESHOLD:
                    jiggle()
                    logging.info("Jiggled (idle %.0fs)", idle)
                else:
                    logging.info("Active (idle %.0fs), skipping", idle)
                time.sleep(random.randint(30, 60))
            else:
                time.sleep(300)  # Вне окна — спим 5 минут
    except KeyboardInterrupt:
        logging.info("Stopped")
