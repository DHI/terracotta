"""handlers/colormaps.py

Handle /colormaps API endpoint.
"""

from typing import List

from terracotta.profile import trace


@trace()
def colormaps() -> List[str]:
    """Return all supported colormaps"""
    from terracotta.cmaps import AVAILABLE_CMAPS
    return list(sorted(AVAILABLE_CMAPS))
