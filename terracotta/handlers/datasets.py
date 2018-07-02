from typing import List, Mapping

from terracotta.database import requires_database, Database


@requires_database
def datasets(db: Database, some_keys: Mapping[str, str] = None) -> List[Mapping[str, str]]:
    """List all available key combinations"""
    raise NotImplementedError
