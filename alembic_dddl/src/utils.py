import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def ensure_dir(dir: str) -> None:
    path = Path(dir)
    if not path.is_dir():
        logger.info(f'DDL dir does not exist, creating: {path}')
        path.mkdir(parents=True)
