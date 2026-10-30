import logging
import logging.handlers
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT

_configured: set = set()

def get_logger(name: str = "tg_extractor") -> logging.Logger:
    logger = logging.getLogger(name)
    if name not in _configured:
        logger.setLevel(logging.DEBUG)
        fmt = logging.Formatter("[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s",
                                datefmt="%Y-%m-%d %H:%M:%S")
        fh = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.WARNING)
        ch.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(ch)
        _configured.add(name)
    return logger
