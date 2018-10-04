"""exceptions.py

Custom warnings and exceptions raised internally
"""


class TileOutOfBoundsError(Exception):
    pass


class DatasetNotFoundError(Exception):
    pass


class UnknownKeyError(Exception):
    pass


class InvalidArgumentsError(Exception):
    pass


class InvalidDatabaseError(Exception):
    pass


class PerformanceWarning(UserWarning):
    pass
