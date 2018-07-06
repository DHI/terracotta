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
[Flask](http://flask.pocoo.org) and [Rasterio](https://github.com/mapbox/rasterio).

## Use cases

Terracotta covers several use cases:

1. It can be used as a data exploration tool, to quickly serve up a folder containing GeoTiff files
   through `terracotta serve`.
2. It can serve as a tile server backend to an existing webserver. Refer to
   [the Flask documentation](http://flask.pocoo.org/docs/1.0/deploying/) for more information.
   Ingestion can either be done [ahead of time](#ingestion) (recommended) or on demand.
3. It can be deployed on serverless architectures such as AWS λ, serving tiles from S3 buckets.


## Why Terracotta?

There are many good reasons to ditch your ancient raster data workflow and switch to Terracotta.
Some of them are listed here:

- It is trivial to get going.
- Usability is our first priority.
- Terracotta makes minimal assumptions about your data, so *you stay in charge*.
- Terracotta is built with extensibility in mind. Want to change your architecture? No problem!
  Even if Terracotta does not support your use case yet, extending it is as easy as implementing
  a single class.
- It uses Python 3.6 type annotations throughout and is well tested, to make sure it won't leave you
  hanging when you need it the most.

## Architecture

In Terracotta, all heavy lifting is done by a so-called driver. The driver specifies where and how
Terracotta can find the raster data and metadata it requires to serve a dataset. Most drivers use
a database to store metadata and rely on a file system to store raster data, but neither of those
statements is enforced by the API.

Already implemented drivers include:

- **SQLite + GeoTiff**: Metadata is backed in an SQLite database, along with the paths to the
  (physical) raster files. This is the simplest driver, and is used by default in most applications.

## Installation

On most systems, installation is as easy as

```bash
pip install terracotta
```

## Ingestion

### Using `create-database`

### An example ingestion script using the Python API

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

## The API

Terracotta implements the following API (curly braces denote request parameters):

- `http://server.com/singleband/{key1}/{key2}/.../{z}/{x}/{y}.png`

   Serves [Mercator tile](http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/)
   (`x`, `y`) at zoom level `z`, from `dataset`.

- `http://server.com/rgb/{key1}/{key2}/.../{z}/{x}/{y}.png?r={key_n_1}&g={key_n_2}&b={key_n_3}`

   Returns RGB where red, green, and blue channels correspond to the given values of the last key
   `key_n`. All keys except the last one must be specified in the route.

- `http://server.com/keys`

   Lists the names of all available keys in the current deployment.

- `http://server.com/datasets?{some_key}={some_value}&{other_key}={other_value}&...`

   List all available key combinations. Examples:

   - `/datasets?name=foo&timestep=bar` returns `[{name: foo, timestep: bar, band: baz}, {name: foo, timestep: bar, band: boo}, ...]`
   - `/datasets?name=foo` returns `[{name: foo, timestep: bar, band: baz}, {name: foo, timestep: baa, band: boo}, ...]`


- `http://server.com/metadata/{key1}/{key2}/...`

   Returns a JSON object containing useful metadata for `dataset`, such as whether or not `dataset` is timestepped,
min/max values of the dataset, WGS84 bounds, datatype and more.

   Metadata contains:

   - `bounds`:

- `http://server.com/colorbar/{key1}/{key2}/...`

   Returns a JSON mapping numerical values to RGB codes.

- `http://server.com/colormaps`

   Return a JSON list of all available colormaps for the `colormap` query parameter.

## Configuration

To allow for flexible deployments, Terracotta is fully configurable in several ways:

1. Through a configuration file in TOML format, passed as an argument to `terracotta serve`, or
   to the app factory in WSGI or serverless deployments.
2. By setting environment variables with the prefix `TC_`, containing the JSON-encoded value to
   be used for the corresponding option.
3. Through Terracotta's Python API, by using the command `terracotta.update_settings(config)`,
   where `config` is a dictionary holding the new key-value pairs.

### Available settings

`terracotta-config.toml`:
```toml
DRIVER_PATH = 'path_or_url'
DRIVER_PROVIDER = ''  # default: auto-detect
CACHE_SIZE = 1024 * 1024 * 500  # 500MB
TILE_SIZE = (256, 256)
DB_CACHEDIR = '/tmp/terracotta'  # used to cache remote databases
```

## Limitations

There are some cases that Terracotta does not handle:

- The number of keys must be unique throughout a dataset.
- You can only use the last key to compose RGB images.
