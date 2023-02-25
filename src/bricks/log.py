"""
Log

Log helper and wrapper around `structlog and `jsonlogger`. Idea to use as follows:
> from basics.log import logger
> logger(__name__).debug('Or onr of the others.', **kwargs_with_extra_details)

Alternatively:
> try:
>     1/0
> except Exception:
>     logger(__name__).exception('Something did not go as planned')

## To a File or Other Targets

Pipe the `stdout` to the required target. See https://12factor.net/logs for background.

## Typing

The groupped type `LoggerType` consists of the `logger` types in the standard library
with `logging.Logger` and structlog's `BoundLogger`.

# Sources and Links

1. https://www.structlog.org/en/stable/standard-library.html
2. https://codywilbourn.com/2018/08/23/playing-with-python-structured-logs/

# TODO:

1. Add `structlog`; currently only `jsonlogger` and `logging` included.

"""
import logging
import sys
import typing as t

import structlog

LoggerType = t.Union[logging.Logger]


def init(debug: bool = False) -> None:
    """
    Initialise the stdlib and structlog loggers.

    `debug` sets the log level, see `level()`.
    """

    if logging.getLogger().hasHandlers():
        return

    log_level = level(debug)

    # Processors used by both `structlog` and `logging`
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=False),
        structlog.processors.UnicodeDecoder(),
        # structlog.stdlib.render_to_log_kwargs,
    ]

    # Configure the `structlog` logger, the message is eventually dumped into the
    # `logging` logger by the `wrap_for_formatter`
    structlog.configure(
        cache_logger_on_first_use=True,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
    )

    # Depending if the environment is a tty terminal or not, select the renderer.
    if sys.stdout.isatty():
        renderer = [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        renderer = [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    # Configure the `logging` logger, which also gets the `structlog` calls
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *renderer,
        ],
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Boil it all down and set the minimum level
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)


def logger(name: str = None) -> LoggerType:
    """
    Get a logger object, optionally with the given name.

    If `name` is not given `__package__` is used.
    """

    if not logging.getLogger().hasHandlers():
        init()

    if name is None:
        name = __package__

    return logging.getLogger(name)


def level(debug: bool = False) -> int:
    """
    Determine the level at and above which messages are logged.

    Lower ranked messages are ignored.
    """
    return logging.DEBUG if debug else logging.INFO
