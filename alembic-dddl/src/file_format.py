import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from re import Pattern
from typing import Union

from dddl.src.models import RevisionedScript


class FileFormatBase(ABC):
    pattern: Pattern

    @staticmethod
    @abstractmethod
    def generate_filename(name: str, revision: str, time: datetime) -> str:
        ...

    @classmethod
    def get_script_if_matches(cls, filepath: str) -> Union[RevisionedScript, None]:
        filename = os.path.split(filepath)[-1]
        match = cls.pattern.match(filename)
        if not match:
            return None
        return RevisionedScript(filepath=filepath, name=match['name'], revision=match['revision'])


class TimestampedFileFormat(FileFormatBase):
    """
    Example: 1703585962_report_uptime_8ffde7d40185.sql
    """
    pattern = re.compile(r'(?P<timestamp>\d{9,})_(?P<name>.+?)_(?P<revision>[^_]+).sql')

    @staticmethod
    def generate_filename(name: str, revision: str, time: datetime) -> str:
        return f"{int(time.timestamp())}_{name}_{revision}.sql"


class DateTimeFileFormat(FileFormatBase):
    """
    Example: '2023_06_05_1820_report_uptime_4b550063ade3.sql'
    """
    pattern = re.compile(
        r'(?P<year>\d{4})_(?P<month>\d{2})_(?P<day>\d{2})_(?P<hours>\d{2})(?P<minutes>\d{2})'
        r'_(?P<name>.+?)_(?P<revision>[^_]+).sql'
    )

    @staticmethod
    def generate_filename(name: str, revision: str, time: datetime) -> str:
        return f"{time.strftime('%Y_%m_%d_%H%M')}_{name}_{revision}.sql"


