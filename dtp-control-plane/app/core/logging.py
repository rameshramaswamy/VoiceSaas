import structlog
import logging
import sys

def configure_logging():
    """
    Configures structured JSON logging for production.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if sys.stderr.isatty():
        # Pretty printing for local dev
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        # JSON for production (Splunk/Datadog)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Intercept Standard Library Logging (uvicorn, sqlalchemy)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)