"""exceptions.py

Custom warnings and exceptions raised internally.
"""


class TileOutOfBoundsError(Exception):
    pass


class DatasetNotFoundError(Exception):
    pass


class InvalidKeyError(Exception):
    pass


class InvalidArgumentsError(Exception):
    pass


class InvalidDatabaseError(Exception):
    pass


class PerformanceWarning(UserWarning):
    pass
