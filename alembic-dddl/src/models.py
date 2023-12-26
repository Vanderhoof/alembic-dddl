import os
from dataclasses import dataclass


@dataclass
class DDL:
    name: str
    sql: str
    down_sql: str


class RevisionedScript:
    def __init__(self, filepath: str, name: str, revision: str) -> None:
        self.filepath = filepath
        self.name = name
        self.revision = revision

        self.script_name = os.path.split(filepath)[-1]

    def read(self) -> str:
        with open(self.filepath) as f:
            contents = f.read()
        return contents

    def __repr__(self) -> str:
        return f'< Script {self.filepath!r}'
