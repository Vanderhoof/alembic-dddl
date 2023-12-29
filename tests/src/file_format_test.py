import re
from datetime import datetime
from unittest.mock import patch

import pytest

from alembic_dddl import RevisionedScript
from alembic_dddl.src.file_format import TimestampedFileFormat, DateTimeFileFormat


def test_get_script_if_matches_not_matches() -> None:
    filepath = f"wrong_filename.sql"

    result = TimestampedFileFormat.get_script_if_matches(filepath=filepath)

    assert result is None


def test_get_script_if_matches_wrong_pattern() -> None:
    with patch.object(TimestampedFileFormat, "pattern", re.compile("Wrong_pattern")):
        with pytest.raises(AssertionError):
            TimestampedFileFormat.get_script_if_matches(filepath="filepath")


class TestTimestampedFileFormat:
    @staticmethod
    def test_get_script_if_matches_matches() -> None:
        time = 1703860266
        name = "sample_script_name"
        revision = "c7526352"
        filepath = f"{time}_{name}_{revision}.sql"

        result = TimestampedFileFormat.get_script_if_matches(filepath=filepath)

        assert isinstance(result, RevisionedScript)
        assert result.name == name
        assert result.revision == revision

    @staticmethod
    def test_generate_filename() -> None:
        time = datetime.fromtimestamp(1703860266)
        name = "sample_script_name"
        revision = "c7526352"

        expected = "1703860266_sample_script_name_c7526352.sql"

        result = TimestampedFileFormat.generate_filename(
            name=name, revision=revision, time=time
        )
        assert result == expected


class TestDateTimeFileFormat:
    @staticmethod
    def test_get_script_if_matches_matches() -> None:
        time = "2023_01_01_0915"
        name = "sample_script_name"
        revision = "c7526352"
        filepath = f"{time}_{name}_{revision}.sql"

        result = DateTimeFileFormat.get_script_if_matches(filepath=filepath)

        assert isinstance(result, RevisionedScript)
        assert result.name == name
        assert result.revision == revision

    @staticmethod
    def test_generate_filename() -> None:
        time = datetime(2023, 1, 1, 9, 15)
        name = "sample_script_name"
        revision = "c7526352"

        expected = "2023_01_01_0915_sample_script_name_c7526352.sql"

        result = DateTimeFileFormat.generate_filename(
            name=name, revision=revision, time=time
        )
        assert result == expected
