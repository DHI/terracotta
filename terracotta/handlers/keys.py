from typing import List

from terracotta.database import requires_database, Database


@requires_database
def keys(db: Database) -> List[str]:
    """List available keys, in order"""
    raise NotImplementedError
