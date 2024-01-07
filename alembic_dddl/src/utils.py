import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_dir(dir: str) -> None:
    """Create a directory if it doesn't exist'"""
    path = Path(dir)
    if not path.is_dir():
        logger.info(f"DDL dir does not exist, creating: {path}")
        path.mkdir(parents=True)


def escape_quotes(text: str) -> str:
    """Excape single quotes in text"""
    return text.replace("'", "\\'")
