from typing import Mapping, Sequence

from terracotta.database import requires_database, Database


@requires_database
def colorbar(db: Database, keys: Mapping[str, str], xyz: Sequence[int], *,
             color_options: Mapping[str, str] = None) -> Mapping[int, str]:
    """Returns a mapping pixel value -> color hex for given image"""
    raise NotImplementedError
