"""keepalive — stay green in messaging apps."""

# Required Notice: Copyright 2026 Sviatoslav Kozar (https://github.com/skozar/keepalive)
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

__version__ = "0.7.0"

# Re-export constants for convenience
from keepalive.config import (
    KEY_CODES,
    DEFAULT_SCHEDULE,
    DEFAULT_IDLE,
    DEFAULT_METHOD,
    DEFAULT_KEY,
    load_settings,
    save_settings,
)
