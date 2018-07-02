from typing import Mapping, Any

from terracotta.database import requires_database, Database


@requires_database
def metadata(db: Database, keys: Mapping[str, str]) -> Mapping[str, Any]:
    """Returns all metadata for a single dataset"""
    raise NotImplementedError
