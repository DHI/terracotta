import os
from typing import Dict, List

import terracotta

# Define the location of the SQLite database
# (this will be created if it doesn't already exist)
DB_NAME = "./terracotta.sqlite"

# Define the list of keys that will be used to identify datasets.
# (these must match the keys of the "key_values" dicts defined in
# RASTER_FILES)
KEYS = ["type", "rp", "rcp", "epoch", "gcm"]

# Define a list of raster files to import
# (this is a list of dictionaries, each with a file path and the
# values for each key - make sure the order matches the order of
# KEYS defined above)
#
# This part of the script could be replaced with something that
# makes sense for your data - it could use a glob expression to
# find all TIFFs and a regular expression pattern to extract the
# key values, or it could read from a CSV, or use some other
# reference or metadata generating process.
RASTER_FILES = [
    {
        "key_values": {
            "type": "river",
            "rp": 250,
            "rcp": 4.5,
            "epoch": 2030,
            "gcm": "NorESM1-M",
        },
        "path": "./data/river__rp_250__rcp_4x5__epoch_2030__gcm_NorESM1-M.tif",
    },
    {
        "key_values": {
            "type": "river",
            "rp": 500,
            "rcp": 8.5,
            "epoch": 2080,
            "gcm": "NorESM1-M",
        },
        "path": "./data/river__rp_500__rcp_8x5__epoch_2080__gcm_NorESM1-M.tif",
    },
]


def load(db_name: str, keys: List[str], raster_files: List[Dict]):
    # get a TerracottaDriver that we can use to interact with
    # the database
    driver = terracotta.get_driver(db_name)

    # create the database file if it doesn't exist already
    if not os.path.isfile(db_name):
        driver.create(keys)

    # check that the database has the same keys that we want
    # to load
    assert list(driver.key_names) == keys, (driver.key_names, keys)

    # connect to the database
    with driver.connect():
        # insert metadata for each raster into the database
        for raster in raster_files:
            driver.insert(raster["key_values"], raster["path"])


if __name__ == "__main__":
    load(DB_NAME, KEYS, RASTER_FILES)
