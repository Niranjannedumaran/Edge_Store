import logging
import json
import sys
from datetime import datetime, timezone
from backend.app.config import settings


class StructuredJsonFormatter(logging.Formatter):
    """
    Format logs as structured JSON strings for clean ingestion and enterprise log hygiene.
    Sanitizes known sensitive keys (password, token, secret, key_material).
    """
    SENSITIVE_KEYS = {"password", "token", "jwt", "secret", "authorization", "luks_key", "key_material"}

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "environment_mode": settings.ENVIRONMENT_MODE.value,
        }

        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            clean_extra = {}
            for k, v in record.extra_data.items():
                if any(sens in k.lower() for sens in self.SENSITIVE_KEYS):
                    clean_extra[k] = "[REDACTED]"
                else:
                    clean_extra[k] = v
            log_obj["data"] = clean_extra

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logger(name: str = "edgestore") -> logging.Logger:
    logger = logging.getLogger(name)
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = StructuredJsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = setup_logger()
