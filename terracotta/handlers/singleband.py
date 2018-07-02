from typing import Mapping, Sequence
from typing.io import BinaryIO

from terracotta.database import requires_database, Database


@requires_database
def singleband(db: Database, keys: Mapping[str, str], xyz: Sequence[int], *,
               color_options: Mapping[str, str] = None) -> BinaryIO:
    """Return singleband image"""
    raise NotImplementedError
