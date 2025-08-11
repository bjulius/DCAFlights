import logging
import sys
import pandas as pd

# Configure pandas to show all columns and more data for debugging
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", 100)  # Show more of each column's content


class LogfmtFormatter(logging.Formatter):
    def format(self, record):
        # Start with level and message, include line number for debugging
        parts = [
            f"level={record.levelname.lower()}",
            f'msg="{record.getMessage()}"',
            f"line={record.lineno}",
        ]

        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "exc_info",
                "exc_text",
                "stack_info",
            ] and not key.startswith("_"):
                parts.append(f"{key}={value}")

        return " ".join(parts)


# Setup
logger = logging.getLogger("generated_app")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(LogfmtFormatter())
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger.propagate = False  # Prevent propagation to root logger
