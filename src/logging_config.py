"""Kedro-style Rich logging configuration.

Provides centralized logging setup with Rich handler for beautiful console output.

Usage:
    from src.logging_config import setup_logging

    # In main() or entry point:
    setup_logging()

    # Then use standard logging:
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Processing file: %s", filename)

Output style:
    [03/19/26 14:30:00] INFO     Processing file: input.xml       my_module.py:42
"""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path

from rich.console import Console

# Module-level Console for use in logging.yml via ext:// protocol
stderr_console = Console(stderr=True)


def setup_logging(
    config_path: Path | str | None = None,
    level: int = logging.INFO,
) -> None:
    """Configure Kedro-style Rich logging.

    Args:
        config_path: Path to logging.yml config file.
                     If None, uses default conf/logging.yml or fallback.
        level: Default log level (used in fallback mode).
    """
    if config_path is None:
        project_root = Path(__file__).parent.parent
        config_path = project_root / "conf" / "logging.yml"

    config_path = Path(config_path) if isinstance(config_path, str) else config_path

    if config_path and config_path.exists():
        _setup_from_yaml(config_path)
    else:
        _setup_fallback(level)


def _setup_from_yaml(config_path: Path) -> None:
    """Load logging config from YAML file."""
    import yaml

    with open(config_path) as f:
        config = yaml.safe_load(f)

    for handler_config in config.get("handlers", {}).values():
        if "filename" in handler_config:
            log_file = Path(handler_config["filename"])
            log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(config)


def _setup_fallback(level: int) -> None:
    """Fallback Rich logging setup without config file."""
    from rich.logging import RichHandler

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%m/%d/%y %H:%M:%S]",
        handlers=[
            RichHandler(
                console=stderr_console,
                rich_tracebacks=True,
                tracebacks_show_locals=False,
                show_path=True,
                markup=True,
            )
        ],
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
