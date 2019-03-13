#!/usr/bin/env python3

import os
import re
import glob

import tqdm
import boto3
s3 = boto3.resource('s3')

import terracotta as tc

# settings
DB_NAME = 'terracotta.sqlite'
RASTER_GLOB = r'/path/to/rasters/*.tif'
RASTER_NAME_PATTERN = r'(?P<sensor>\w{2})_(?P<tile>\w{5})_(?P<date>\d{8})_(?P<band>\w+).tif'
KEYS = ('sensor', 'tile', 'date', 'band')
KEY_DESCRIPTIONS = {
    'sensor': 'Sensor short name',
    'tile': 'Sentinel-2 tile ID',
    'date': 'Sensing date',
    'band': 'Band or index name'
}
S3_BUCKET = 'tc-testdata'
S3_RASTER_FOLDER = 'rasters'
S3_PATH = f's3://{S3_BUCKET}/{S3_RASTER_FOLDER}'

driver = tc.get_driver(DB_NAME)

# create an empty database if it doesn't exist
if not os.path.isfile(DB_NAME):
    driver.create(KEYS, KEY_DESCRIPTIONS)

# sanity check
assert driver.key_names == KEYS

available_datasets = driver.get_datasets()
raster_files = list(glob.glob(RASTER_GLOB))
pbar = tqdm.tqdm(raster_files)

for raster_path in pbar:
    pbar.set_postfix(file=raster_path)

    raster_filename = os.path.basename(raster_path)

    # extract keys from filename
    match = re.match(RASTER_NAME_PATTERN, raster_filename)
    if match is None:
        raise ValueError(f'Input file {raster_filename} does not match raster pattern')

    keys = match.groups()

    # skip already processed data
    if keys in available_datasets:
        continue

    with driver.connect():
        # since the rasters will be served from S3, we need to pass the correct remote path
        driver.insert(keys, raster_path, override_path=f'{S3_PATH}/{raster_filename}')
        s3.meta.client.upload_file(raster_path, S3_BUCKET,
                                   f'{S3_RASTER_FOLDER}/{raster_filename}')

# upload database to S3
s3.meta.client.upload_file(DB_NAME, S3_BUCKET, DB_NAME)
