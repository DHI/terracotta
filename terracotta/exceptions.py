"""exceptions.py

Custom exceptions raised internally
"""


class TileNotFoundError(Exception):
    pass


class TileOutOfBoundsError(Exception):
    pass


class DatasetNotFoundError(Exception):
    pass


class UnknownKeyError(Exception):
    pass
