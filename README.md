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
   [Zappa](https://github.com/Miserlou/Zappa). See [Deployment on AWS](#deployment-on-aws) 
   for more details.


## Why Terracotta?

There are many good reasons to ditch your ancient raster data workflow and switch to Terracotta.
Some of them are listed here:

- It is trivial to get going
- Usability is our first priority.
- Terracotta makes minimal assumptions about your data, so *you stay in charge*. Use the tools you
  know and love to create your data - leave the rest to Terracotta.
- Terracotta is built with extensibility in mind. Want to change your architecture? No problem!
  Even if Terracotta does not support your use case yet, extending it is as easy as implementing
  a single Python class.
- We use Python 3.6 type annotations throughout the project and aim for extensive test coverage,
  to make sure we don't leave you hanging when you need us the most.

## Architecture

In Terracotta, all heavy lifting is done by a so-called driver. The driver specifies where and how
Terracotta can find the raster data and metadata it requires to serve a dataset. Most drivers use
a database to store metadata and rely on a file system to store raster data, but neither of those
things is enforced by the API.

Already implemented drivers include:

- **SQLite + GeoTiff**: Metadata is backed in an SQLite database, along with the paths to the
  (physical) raster files. This is the simplest driver, and is used by default in most applications.

## Installation

On most systems, installation is as easy as

```bash
$ pip install terracotta
```

To install additional requirements needed to deploy to AWS, run

```bash
$ pip install terracotta[aws]
```

instead.

## Ingestion

For Terracotta to perform well, it is important that some metadata like the extent of your datasets
or the range of its values is computed and ingested into a database. There are two ways to populate
this metadata store:

### 1. Using `create-database`

A simple but limited way to build a database is through the command line interface. All you need to
do is to point Terracotta to a folder of (cloud-optimized) GeoTiffs:

```bash
$ terracotta create-database /path/to/gtiffs/{sensor}_{name}_{date}_{band}.tif -o terracotta.sqlite
```

This will create a new database with the keys `sensor`, `name`, `date`, and `band` (in this order),
and ingest all files matching the given pattern into it.

For available options, see

```bash
$ terracotta create-database --help
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

The following script populates a database with raster files located in a local directory
`RASTER_FOLDER`. During deployment, the raster files will be located in an S3 bucket, so we
override the target paths using that URL.

```python
#!/usr/bin/env python3
import os
import re

import terracotta as tc

# settings
DB_PATH = 'terracotta.sqlite'
RASTER_FOLDER = './rasters'
RASTER_NAME_PATTERN = r'(?P<name>\w+)_(?P<date>\d+T\d+)_(?P<band>\w{3}).tif'
KEYS = ('name', 'date', 'band')
S3_PATH = 's3://tc-testdata/rasters'

driver = tc.get_driver(DB_PATH)

# create an empty database if it doesn't exist
if not os.path.isfile(DB_PATH):
    driver.create(KEYS)

with driver.connect():
    # sanity check
    assert driver.available_keys == KEYS

    available_datasets = driver.get_datasets()

    for raster_path in os.listdir(RASTER_FOLDER):
        raster_filename = os.path.basename(raster_path)

        # extract keys from filename
        match = re.match(RASTER_NAME_PATTERN, raster_filename)
        if match is None:
            continue

        keys = match.groups()

        # skip already processed data
        if keys in available_datasets:
            continue

        print(f'Ingesting file {raster_path}')
        driver.insert(keys, raster_path, override_path=f'{S3_PATH}/{raster_filename}')

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
   `TC_TILE_SIZE=[128,128]`.
3. Through Terracotta's Python API, by using the command `terracotta.update_settings(**config)`,
   where `config` is a dictionary holding the new key-value pairs.

Explicit overrides (through the Python API or a configuration file) always have higher precedence
than configuration through environment variables. When changing environment variables after setup,
it might be necessary to call `terracotta.update_settings()` for the changes to take effect.

### Available settings

For all available settings, their types and default values, have a look at the file
[config.py](https://github.com/DHI-GRAS/terracotta/blob/master/terracotta/config.py) in the
Terracotta code.

## Advances recipes

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
      ...
      "extra_metadata": {
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

## Deployment on AWS λ

The easiest way to deploy Terracotta on AWS λ is by using [Zappa](https://github.com/Miserlou/Zappa).

Example `zappa_settings.json` file:

```json
{
    "dev": {
        "app_function": "terracotta.app.app",
        "aws_region": "eu-central-1",
        "profile_name": "default",
        "project_name": "my-terracotta-deployment",
        "runtime": "python3.6",
        "s3_bucket": "zappa-terracotta",
        "aws_environment_variables": {
            "TC_DRIVER_PATH": "s3://my-bucket/terracotta.sqlite",
            "TC_DRIVER_PROVIDER": "sqlite"
        },
        "callbacks": {
            "zip": "zappa_version_callback.inject_version"
        },
        "exclude": [
            "*.gz", "*.rar", "boto3*", "botocore*", "awscli*", ".mypy_cache", ".pytest_cache",
            ".eggs"
        ]
    }
}

```

## Limitations

There are some cases that Terracotta does not handle:

- The number of keys must be unique throughout a dataset.
- You can only use the last key to compose RGB images.
- Several other [open issues](https://github.com/DHI-GRAS/terracotta/issues) (PRs welcome!)
