__all__ = ["log_traceback", "logger"]

import sys
import time
import traceback
from typing import Any

from loguru import logger

from ash.config import config
from ash.utils import indent, json_dumps


def _write_stderr(message: str) -> None:
    print(message, file=sys.stderr, flush=True)  # noqa: T201


def _serializer(message) -> None:  # type: ignore[no-untyped-def]  #noqa: ANN001
    record = message.record
    level = record["level"].name
    message = record["message"]
    module = record["name"]

    if config.log_mode == "json":
        #
        # JSON mode logging
        #

        payload = {
            "timestamp": time.time(),
            "level": level.lower(),
            "message": message,
            "module": module,
            **record["extra"],
        }
        serialized = json_dumps(payload)
        _write_stderr(serialized)

    else:
        #
        # Text mode logging
        #

        module = module.replace("ayon_server.", "")
        formatted = f"{level:<7} {module:<26} | {message}"
        _write_stderr(formatted)

        # Format the message according to the log context setting
        if config.log_context:
            # Put the module name and extra context info in a separate block
            contextual_info = ""
            for k, v in record["extra"].items():
                contextual_info += f"{k}: {v}\n"
            if contextual_info:
                _write_stderr(indent(contextual_info))

        # Print traceback if available
        if tb := record.get("traceback"):
            _write_stderr(indent(str(tb)))


logger.remove(0)
logger.add(_serializer, level=config.log_level)


def log_traceback(message: str = "Exception!", **kwargs: Any) -> None:
    """Log the current exception traceback."""
    tb = traceback.format_exc()
    logger.error(message, traceback=tb, **kwargs)
    _write_stderr(indent(tb))
