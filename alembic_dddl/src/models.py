from dataclasses import dataclass


@dataclass
class DDL:
    """Dataclass for user defined DDL scripts"""

    name: str
    sql: str
    down_sql: str


class RevisionedScript:
    """A class representing a single autogenerated DDL file in the revisions directory"""

    def __init__(self, filepath: str, name: str, revision: str) -> None:
        self.filepath = filepath
        self.name = name
        self.revision = revision

    def read(self) -> str:
        with open(self.filepath) as f:
            contents = f.read()
        return contents

    def __eq__(self, other: object) -> bool:
        # for tests
        assert isinstance(other, RevisionedScript)

        return (
            (self.filepath == other.filepath)
            and (self.name == other.name)
            and (self.revision == other.revision)
        )
