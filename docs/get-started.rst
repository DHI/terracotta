Get started
===========

Installation
------------

On most systems, the easiest way to install Terracotta is `through the
Conda package manager <https://conda.io/miniconda.html>`__. After
installing ``conda``, the following command creates a new environment
containing all dependencies and Terracotta:

.. code:: bash

   $ conda env create -f environment.yml

If you already have a Python 3.6 installation that you want to use, you
can just run

.. code:: bash

   $ pip install -e .

in the root of this repository instead.

Creating a raster database
--------------------------

For Terracotta to perform well, it is important that some metadata like
the extent of your datasets or the range of its values is computed and
ingested into a database. There are two ways to populate this metadata
store:

1. Through the CLI
~~~~~~~~~~~~~~~~~~

A simple but limited way to build a database is to use the command line
interface. All you need to do is to point Terracotta to a folder of
(cloud-optimized) GeoTiffs:

.. code:: bash

   $ terracotta ingest /path/to/gtiffs/{sensor}_{name}_{date}_{band}.tif -o terracotta.sqlite

This will create a new database with the keys ``sensor``, ``name``,
``date``, and ``band`` (in this order), and ingest all files matching
the given pattern into it.

For available options, see

.. code:: bash

   $ terracotta ingest --help

2. Using the Python API
~~~~~~~~~~~~~~~~~~~~~~~

Terracotta’s driver API gives you fine-grained control over ingestion
and retrieval. Metadata can be computed at three different times:

1. Automatically during a call to ``driver.insert`` (fine for most
   applications);
2. Manually using ``driver.compute_metadata`` (in case you want to
   decouple computation and IO, or if you want to attach additional
   metadata); or
3. On demand when a dataset is requested for the first time (this is
   what we want to avoid through ingestion).

An example ingestion script using the Python API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following script populates a database with raster files located in a
local directory. It extracts the appropriate keys from the file name,
ingests them into a database, and pushes the rasters and the resulting
database into an S3 bucket.

.. code:: python

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
           s3.meta.client.upload_file(raster_path, S3_BUCKET, f'{S3_RASTER_FOLDER}/{raster_filename}')

   # upload database to S3
   s3.meta.client.upload_file(DB_NAME, S3_BUCKET, DB_NAME)

Note that the above script is just a simple example to show you some
capabilities of the Terracotta Python API. More sophisticated solutions
could e.g. attach additional metadata to database entries, or accept
parameters from the command line.

Serving data
------------

Connecting to a running Terracotta server
-----------------------------------------