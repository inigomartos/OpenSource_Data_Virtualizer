"""Structured JSON logging configuration with request correlation IDs."""

import sys
import contextvars
from loguru import logger

# Async-safe context variable for request correlation
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


def _json_formatter(record):
    """Custom JSON format for structured log output."""
    import json
    from datetime import datetime, timezone

    rid = request_id_ctx.get("")
    log_entry = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "level": record["level"].name,
        "message": record["message"],
        "logger": record["name"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }
    if rid:
        log_entry["request_id"] = rid
    if record["exception"] is not None:
        log_entry["exception"] = str(record["exception"])
    # Merge any extra data bound via logger.bind()
    extra = {k: v for k, v in record["extra"].items() if k not in ("request_id",)}
    if extra:
        log_entry["extra"] = extra

    return json.dumps(log_entry, default=str) + "\n"


def _dev_formatter(record):
    """Human-readable format for development."""
    rid = request_id_ctx.get("")
    rid_part = f" [{rid[:8]}]" if rid else ""
    return (
        "<green>{time:HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        f"<cyan>{rid_part}</cyan> "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>\n"
    )


def configure_logging(*, debug: bool = False) -> None:
    """Configure loguru for structured JSON (prod) or pretty text (dev)."""
    logger.remove()  # Remove default handler

    if debug:
        logger.add(
            sys.stderr,
            format=_dev_formatter,
            level="DEBUG",
            colorize=True,
        )
    else:
        logger.add(
            sys.stdout,
            format=_json_formatter,
            level="INFO",
            serialize=False,  # We handle serialization in _json_formatter
        )
