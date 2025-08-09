"""Logger configuration for KeywordPDF Analyzer.

This module sets up logging according to the Syslog-style severity
levels and routes all existing ``print()`` calls to the logging
framework. Two log files are created:

1. ``logs/app.log`` – generic application logs (``INFO`` and above)
2. ``logs/error.log`` – detailed error logs (``ERROR`` and above)

The configuration is initialised as soon as this module is imported,
so importing it from the package ``__init__`` guarantees that any other
module that still uses ``print`` will be captured and logged with the
appropriate severity.
"""
from __future__ import annotations

import builtins
import logging
import os
import re
from typing import Any

# ---------------------------------------------------------------------------
# Optional Rich integration for beautiful console output
# ---------------------------------------------------------------------------
try:  # Rich is optional at runtime; we fall back gracefully if missing
    from rich.logging import RichHandler
    from rich.traceback import install as install_rich_traceback
    _RICH_AVAILABLE = True
except Exception:  # pragma: no cover - best-effort optional dependency
    _RICH_AVAILABLE = False

# ---------------------------------------------------------------------------
# Create *logs* directory relative to the project root
# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Configure root logger with two file handlers
# ---------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(LOG_FORMAT, "%Y-%m-%d %H:%M:%S")

logger = logging.getLogger("KeywordPDFAnalyzer")
logger.setLevel(logging.DEBUG)  # Capture everything, handlers will filter

# Generic application logs (INFO and above)
app_log_path = os.path.join(LOGS_DIR, "app.log")
app_handler = logging.FileHandler(app_log_path, encoding="utf-8")
app_handler.setLevel(logging.INFO)
app_handler.setFormatter(formatter)
logger.addHandler(app_handler)

# Detailed error logs (ERROR and above)
error_log_path = os.path.join(LOGS_DIR, "error.log")
error_handler = logging.FileHandler(error_log_path, encoding="utf-8")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)

# Optional: also log to the console for immediate feedback during CLI runs
if _RICH_AVAILABLE:
    # Install rich tracebacks for nicer error visualization in console
    try:
        install_rich_traceback(width=120, show_locals=False)
    except Exception:
        pass

    # Use RichHandler to render levels, time and nice formatting
    console_handler = RichHandler(
        markup=True,
        rich_tracebacks=True,
        show_time=True,
        show_level=True,
        show_path=False,
    )
    console_handler.setLevel(logging.INFO)
    # With RichHandler, keep formatter simple so the handler controls appearance
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)
else:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# ---------------------------------------------------------------------------
# Helper: Map symbols / keywords found in legacy "print" messages to severity
# ---------------------------------------------------------------------------
ERROR_TOKENS = {"❌", "erro", "error", "fatal"}
WARNING_TOKENS = {"⚠️", "warn", "aviso"}
DEBUG_TOKENS = {"🐞", "debug"}

_token_regex = re.compile("[\wÀ-ÿ]+", flags=re.IGNORECASE)


def _detect_level(message: str) -> int:
    """Best-effort mapping from free-text *message* to a logging level."""
    tokens = set(token.lower() for token in _token_regex.findall(message))
    if tokens & ERROR_TOKENS:
        return logging.ERROR
    if tokens & WARNING_TOKENS:
        return logging.WARNING
    if tokens & DEBUG_TOKENS:
        return logging.DEBUG
    # Default
    return logging.INFO


# ---------------------------------------------------------------------------
# Monkey-patch builtins.print so that legacy calls are redirected to logging
# ---------------------------------------------------------------------------
_builtin_print = builtins.print  # Keep reference to the original, just in case


def _print_to_log(*args: Any, **kwargs: Any) -> None:  # noqa: D401
    """Replacement for :pyfunc:`builtins.print` that logs instead of prints."""
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")  # noqa: E501 – for completeness although we ignore it

    # Build the full message as the original *print* would produce
    msg = sep.join(str(a) for a in args) + end.rstrip("\n")

    level = _detect_level(msg)
    logger.log(level, msg)


# Apply the monkey patch exactly once
if getattr(builtins.print, "__name__", "") != _print_to_log.__name__:
    builtins.print = _print_to_log  # type: ignore[assignment]

# Expose *logger* so other modules can do ``from logger_manager import logger``
__all__ = ["logger"]
