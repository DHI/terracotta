from typing import List


def colormaps() -> List[str]:
    """Return all supported colormaps"""
    from terracotta.cmaps import AVAILABLE_CMAPS
    return list(sorted(AVAILABLE_CMAPS))
