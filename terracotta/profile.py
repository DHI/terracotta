"""profile.py

Decorators for performance tracing
"""

from typing import Iterator

import contextlib

from terracotta import get_settings


@contextlib.contextmanager
def trace(description: str = 'unknown') -> Iterator:
    settings = get_settings()
    if settings.XRAY_PROFILE:
        from aws_xray_sdk.core import xray_recorder
        try:
            subsegment = xray_recorder.begin_subsegment(description)
            yield subsegment
        finally:
            xray_recorder.end_subsegment()
    else:
        yield None
