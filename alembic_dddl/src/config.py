from dataclasses import dataclass, fields
from typing import Any, Dict

from alembic.config import Config
from alembic.util.langhelpers import asbool

DDDL_CONFIG_SECTION = 'dddl'


@dataclass
class DDDLConfig:
    scripts_location: str = 'migrations/versions/ddl'
    use_timestamps: bool = False
    ignore_comments: bool = False

    @classmethod
    def _process_bools(cls, alembic_config_dict: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(alembic_config_dict)
        bool_fields = (f.name for f in fields(cls) if f.type == bool)
        for bool_field in bool_fields:
            if bool_field in result:
                result[bool_field] = asbool(result[bool_field])
        return result

    @classmethod
    def from_config(cls, alembic_config: Config) -> 'DDDLConfig':
        config_fields = {f.name for f in fields(cls)}
        config_dict = alembic_config.get_section(DDDL_CONFIG_SECTION) or {}
        config_dict = {k: v for k, v in config_dict.items() if k in config_fields}
        if config_dict:
            config_dict = cls._process_bools(config_dict)
        return DDDLConfig(**config_dict)


def load_config(c: Config) -> DDDLConfig:
    return DDDLConfig.from_config(c)

