import logging

import colorlog

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s %(name)s [%(levelname)s] %(message)s"
# )
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create color formatter
color_formatter = colorlog.ColoredFormatter(
    "%(green)s%(asctime)s%(reset)s %(bold_blue)s%(name)s%(reset)s %(log_color)s[%(levelname)s]%(reset)s %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(color_formatter)

logger.addHandler(console_handler)
logger.propagate = False 