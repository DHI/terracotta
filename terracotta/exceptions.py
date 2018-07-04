"""exceptions.py

Custom exceptions raised internally
"""


class TileOutOfBoundsError(Exception):
    pass


class DatasetNotFoundError(Exception):
    pass


class UnknownKeyError(Exception):
    pass


class InvalidArgumentsError(Exception):
    pass
