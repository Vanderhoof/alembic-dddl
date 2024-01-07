from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from alembic_dddl.src.config import DDDLConfig, load_config


@pytest.fixture
def sample_config_dict() -> Dict[str, Any]:
    return {
        'scripts_location': 'migrations/versions/ddl_revisions',
        'ignore_comments': 'True',
        'wrong_option': 42
    }


@pytest.fixture
def mock_alembic_config(sample_config_dict: Dict[str, Any]) -> Mock:
    return Mock(get_section=Mock(return_value=sample_config_dict))


@pytest.fixture
def mock_empty_alembic_config() -> Mock:
    return Mock(get_section=Mock(return_value=None))


def test_process_bools(sample_config_dict: Dict[str, Any]) -> None:
    expected = {
        'scripts_location': 'migrations/versions/ddl_revisions',
        'ignore_comments': True,
        'wrong_option': 42
    }
    result = DDDLConfig._process_bools(sample_config_dict)
    assert result == expected


def test_from_config(mock_alembic_config: Mock) -> None:
    expected = DDDLConfig(
        scripts_location='migrations/versions/ddl_revisions',
        use_timestamps=False,
        ignore_comments=True
    )
    result = DDDLConfig.from_config(alembic_config=mock_alembic_config)
    assert result == expected


def test_from_config_no_section(mock_empty_alembic_config: Mock) -> None:
    expected = DDDLConfig(
        scripts_location='migrations/versions/ddl',
        use_timestamps=False,
        ignore_comments=False
    )
    result = DDDLConfig.from_config(alembic_config=mock_empty_alembic_config)
    assert result == expected


def test_load_config(mock_alembic_config: Mock) -> None:
    # mostly for coverage :)
    with patch('alembic_dddl.src.config.DDDLConfig') as mock_config:
        load_config(mock_alembic_config)
        assert mock_config.from_config.called is True

