import logging
import sys

import structlog
from rich.console import Console
from rich.logging import RichHandler


def console_handler() -> logging.Handler:
    console = Console(stderr=True)
    handler: logging.Handler
    renderer: structlog.typing.Processor
    if console.is_terminal:
        handler = RichHandler(console=console, show_path=False, markup=False)
        renderer = structlog.processors.KeyValueRenderer(key_order=["event"])
    else:
        handler = logging.StreamHandler(sys.stderr)
        renderer = structlog.processors.JSONRenderer()
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.ExtraAdder(allow={"port", "desktop"}),
                structlog.processors.TimeStamper(fmt="iso", utc=True),
            ],
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )
    )
    return handler
