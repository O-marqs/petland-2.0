import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Allowlist only: never include arbitrary exceptions, URLs or payloads.
        result = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": record.msg,
        }
        for name in ("request_id", "route", "method", "status", "duration_ms", "error_type"):
            if hasattr(record, name):
                result[name] = getattr(record, name)
        return json.dumps(result, ensure_ascii=False)


def configure_logging(level: str) -> logging.Logger:
    logger = logging.getLogger("petland")
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger
