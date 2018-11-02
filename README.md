[![Build Status](https://travis-ci.com/DHI-GRAS/terracotta.svg?token=27HwdYKjJ1yP6smyEa25&branch=master)](https://travis-ci.com/DHI-GRAS/terracotta)
[![codecov](https://codecov.io/gh/DHI-GRAS/terracotta/branch/master/graph/badge.svg?token=u16QBwwvvn)](https://codecov.io/gh/DHI-GRAS/terracotta)

# Terracotta

A modern XYZ tile server, serving tiles from various data sources, built with Flask and Rasterio
:earth_africa:

Terracotta is meant to be deployed as a WSGI on a webserver, or as a serverless app on AWS λ,
however it can also be run as a standalone server through the CLI interface (`terracotta serve`).
It is not recommended to run Terracotta as a standalone server for other purposes than data
exploration, debugging, or development.

For best performance, it is highly recommended to use [Cloud Optimized GeoTIFFs](http://www.cogeo.org)
(COG) with Terracotta. You can convert all kinds of single-band raster files to COG through the
command `terracotta optimize-rasters`.

Terracotta is built on a modern Python 3.6 stack, powered by awesome open-source software such as
[Flask](http://flask.pocoo.org), [Zappa](https://github.com/Miserlou/Zappa), and
[Rasterio](https://github.com/mapbox/rasterio).

## Contents

- [Use cases](#use-cases)
- [Why Terracotta?](#why-terracotta)
- [Why not Terracotta?](#why-not-terracotta)
- [Architecutre](#architecture)
- [Installation](#installation)
- [Ingestion](#ingestion)
  - [1. Through the CLI](#1-through-the-cli)
  - [2. Using the Python API](#2-using-the-python-api)
- [Web API](#web-api)
- [Configuration](#configuration)
  - [Available settings](#available-settings)
- [Advanced recipes](#advanced-recipes)
  - [Serving categorical data](#serving-categorical-data)
  - [Deployment to AWS λ](#deployment-to-aws-λ)
- [Known issues](#known-issues)

## Use cases

Terracotta covers several use cases:

1. It can be used as a data exploration tool, to quickly serve up a folder containing GeoTiff files
   through `terracotta serve`.
2. It can serve as a tile server backend to an existing webserver. Refer to
   [the Flask documentation](http://flask.pocoo.org/docs/1.0/deploying/) for more information.
   Ingestion can either be done [ahead of time](#ingestion) (recommended) or on demand.
3. It can be deployed on serverless architectures such as AWS λ, serving tiles from S3 buckets.
   This allows you to build apps that scale infinitely while requiring minimal maintenance!
   To make it as easy as possible to deploy to AWS λ, we make use of the magic provided by
   [Zappa](https://github.com/Miserlou/Zappa). See [Deployment on AWS](#deployment-to-aws-λ)
   for more details.

## Why Terracotta?

There are many good reasons to ditch your ancient raster data workflow and switch to Terracotta.
Some of them are listed here:

- It is trivial to get going. Got a folder full of GeoTiffs in different projections you want to
  have a look at in your browser? Cool, `terracotta serve -p {name}.tif` and
  `terracotta connect localhost:5000` get you there!
- Usability is our first priority. We strive to make your workflow as simple as possible, while
  supporting many different use cases.
- Terracotta makes minimal assumptions about your data, so *you stay in charge*. Use the tools you
  know and love to create your data - leave the rest to Terracotta.
- Deploying Terracotta to serverless architectures is a first-priority use case, so you don't have
  to worry about maintaining or scaling your architecture.
- Running Terracotta instances are self-documenting. Everything the frontend needs to know about
  your data and architecture is exposed in only a handfull of API endpoints.
- Terracotta is built with extensibility in mind. Want to change your architecture? No problem!
  Even if Terracotta does not support your use case yet, extending it is as easy as implementing
  a single Python class.
- We use Python 3.6 type annotations throughout the project and aim for extensive test coverage,
  to make sure we don't leave you hanging when you need us the most.

## Why not Terracotta?

Terracotta is light-weight and optimized for simplicity and flexibility. To achieve this, we had
to accept some trade-offs:

- The number of keys must be unique throughout a dataset, and keys have to be strings. This means
  that it is not possible to search for datasets through any other means than setting one or more
  key values to a fixed value (i.e., not date-range lookups or similar).
- You can only use the last key to compose RGB images (i.e., the last key must be `band` or similar).
- Since the names and semantics of the keys of a Terracotta deployment are flexible, there are no
  guarantees that two different Terracotta deployments behave in the same way. However, all information
  is transparently available from the frontend, e.g. via the `/swagger.json`, `/apidoc`, and `/keys`
  API endpoints.
- Terracotta favors flexibility over raw speed. If sub-second response times are a hard requirement
  for you, Terracotta might not be the right tool for the job.

## Architecture

In Terracotta, all heavy lifting is done by a so-called driver. The driver specifies where and how
Terracotta can find the raster data and metadata it requires to serve a dataset. Most drivers use
a database to store metadata and rely on a file system to store raster data, but neither of those
things is enforced by the API.

Already implemented drivers include:

- **SQLite + GeoTiff**: Metadata is backed in an SQLite database, along with the paths to the
  (physical) raster files. This is the simplest driver, and is used by default in most applications.

## Installation

On most systems, the easiest way to install Terracotta is
[through the Conda package manager](https://conda.io/miniconda.html). After installing `conda`, the
following command creates a new environment containing all dependencies and Terracotta:

```bash
$ conda env create -f environment.yml
```

If you already have a Python 3.6 installation that you want to use, you can just run

```bash
$ pip install -e .
```

in the root of this repository instead.

## Ingestion

For Terracotta to perform well, it is important that some metadata like the extent of your datasets
or the range of its values is computed and ingested into a database. There are two ways to populate
this metadata store:

### 1. Through the CLI

A simple but limited way to build a database is to use the command line interface. All you need to
do is to point Terracotta to a folder of (cloud-optimized) GeoTiffs:

```bash
$ terracotta ingest /path/to/gtiffs/{sensor}_{name}_{date}_{band}.tif -o terracotta.sqlite
```

This will create a new database with the keys `sensor`, `name`, `date`, and `band` (in this order),
and ingest all files matching the given pattern into it.

For available options, see

```bash
$ terracotta ingest --help
```

### 2. Using the Python API

Terracotta's driver API gives you fine-grained control over ingestion and retrieval.
Metadata can be computed at three different times:

1. Automatically during a call to `driver.insert` (fine for most applications);
2. Manually using `driver.compute_metadata` (in case you want to decouple computation and IO,
   or if you want to attach additional metadata); or
3. On demand when a dataset is requested for the first time (this is what we want to avoid
   through ingestion).

#### An example ingestion script using the Python API

The following script populates a database with raster files located in a local directory.
It extracts the appropriate keys from the file name, ingests them into a database, and
pushes the rasters and the resulting database into an S3 bucket.

```python
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

```

Note that the above script is just a simple example to show you some capabilities of the Terracotta
Python API. More sophisticated solutions could e.g. attach additional metadata to database entries,
or accept parameters from the command line.

## Web API

Every Terracotta deployment exposes the API it uses as a `swagger.json` file and a visual
explorer hosted at `http://server.com/swagger.json` and `http://server.com/apidoc`, respectively.
This is the best way to find out which API *your* deployment of Terracotta uses.

## Configuration

To allow for flexible deployments, Terracotta is fully configurable in several ways:

1. Through a configuration file in TOML format, passed as an argument to `terracotta serve`, or
   to the app factory in WSGI or serverless deployments.
2. By setting environment variables with the prefix `TC_`. Lists are passed as JSON arrays:
   `TC_DEFAULT_TILE_SIZE=[128,128]`.
3. Through Terracotta's Python API, by using the command `terracotta.update_settings(**config)`,
   where `config` is a dictionary holding the new key-value pairs.

Explicit overrides (through the Python API or a configuration file) always have higher precedence
than configuration through environment variables. When changing environment variables after setup,
it might be necessary to call `terracotta.update_settings()` for the changes to take effect.

### Available settings

For all available settings, their types and default values, have a look at the file
[config.py](https://github.com/DHI-GRAS/terracotta/blob/master/terracotta/config.py) in the
Terracotta code.

## Advanced recipes

### Serving categorical data

Categorical datasets are special in that the numerical pixel values carry no direct meaning, 
but rather encode which category or label the pixel belongs to. Because labels must be preserved,
serving categorical data comes with its own set of complications:

- Dynamical stretching does not make sense
- Nearest neighbor resampling must be used
- Labels must be mapped to colors consistently

So far, Terracotta is agnostic of categories and labels, but the API is flexible enough to give
you the tools to build your own system. Categorical data can be served by following these steps:

#### During ingestion

1. Create an additional key to encode whether a dataset is categorical or not. E.g., if you are
   currently using the keys `sensor`, `date`, and `band`, ingest your data with the keys
   `[type, sensor, date, band]`, where `type` can take one of the values `categorical`, `index`,
   `reflectance`, or whatever makes sense for your given application.
2. Attach a mapping `category name -> pixel value` to the metadata of your categorical dataset.
   Using the Python API, this could e.g. be done like this:

   ```python
   import terracotta as tc

   driver = tc.get_driver('terracotta.sqlite')

   # assuming keys are [type, sensor, date, band]
   keys = ['categorical', 'S2', '20181010', 'cloudmask']
   raster_path = 'cloud_mask.tif'

   category_map = {
       'clear land': 0,
       'clear water': 1,
       'cloud': 2,
       'cloud shadow': 3
   }

   with driver.connect():
       metadata = driver.compute_metadata(raster_path, extra_metadata={'categories': category_map})
       driver.insert(keys, raster_path, metadata=metadata)

   ```

#### In the frontend

Ingesting categorical data this way allows us to access it from the frontend. Given that your
Terracotta server runs at `example.com`, you can use the following functionality:

- To get a list of all categorical data, simply send a GET request to
  `example.com/datasets?type=categorical`.
- To get the available categories of a dataset, query
  `example.com/metadata/categorical/S2/20181010/cloudmask`. The returned JSON object will contain
  a section like this:

  ```json
  {
      "metadata": {
          "categories": {
              "clear land": 0,
              "clear water": 1,
              "cloud": 2,
              "cloud shadow": 3
          }
      }
  }
  ```

- To get correctly labelled imagery, the frontend will have to pass an explicit color mapping of pixel
  values to colors by using `/singleband`'s `explicit_color_map` argument. In our case, this could look
  like this:
  `example.com/singleband/categorical/S2/20181010/cloudmask/{z}/{x}/{y}.png?colormap=explicit&explicit_color_map={"0": "99d594", "1": "2b83ba", "2": "ffffff", "3": "404040"}`.

  Supplying an explicit color map in this fashion suppresses stretching, and forces Terracotta to only use
  nearest neighbor resampling when reading the data.
  
  Colors can be passed as hex strings (as in this example) or RGB color tuples. In case you are looking 
  for a nice color scheme for your categorical datasets, [color brewer](http://colorbrewer2.org) features 
  some excellent suggestions.

### Deployment to AWS λ

The easiest way to deploy Terracotta to AWS λ is by using [Zappa](https://github.com/Miserlou/Zappa).
This repository contains a template with sensible default values for most Zappa settings.

To deploy to AWS λ, execute the following steps:

1. Create and activate a new virtual environment (here called `tc-deploy`).
2. Install all relevant dependencies via `pip install -r zappa_requirements.txt`.
3. Install the AWS command line tools via `pip install awscli`.
4. Configure access to AWS by running `aws configure`. Make sure that you have proper access
   to S3 and AWS λ before continuing.
5. If you haven't already done so, create the Terracotta database you want to use, and upload your
   raster files to S3.
6. Copy or rename `zappa_settings.toml.in` to `zappa_settings.toml` and insert the correct path to
   your Terracotta database.
7. Run `zappa deploy development` or `zappa deploy production`. Congratulations, your Terracotta instance
   should now be reachable!

Note that Zappa works best on Linux. Windows 10 users can use the
[Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10) to deploy Terracotta.

## Known Issues

The sections below outline some common issues people encounter when using Terracotta. If your problem persists,
[feel free to open an issue](https://github.com/DHI-GRAS/terracotta/issues).

### `OSError: error while reading file` while deploying to AWS λ

Rasterio Linux wheels are built on CentOS, which stores SSL certificates in `/etc/pki/tls/certs/ca-bundle.crt`.
On other Linux flavors, certificates may be stored in a different location. On Ubuntu, you can e.g. run

```bash
$ export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
```

to fix this issue. For more information, see [mapbox/rasterio#942](https://github.com/mapbox/rasterio/issues/942).