# Terracotta
An XYZ tile server, that serves tiles from GeoTIFFs. built with Flask and Rasterio :earth_africa:

Terracotta is meant to be deployed as a WSGI app on a webserver, however it can also be run as a standalone server through the CLI interface available by running `terracotta`, after installing the package.

It is not recommended to run Terracotta as a standalone server for other purposes than debugging and development.

See [this](http://flask.pocoo.org/docs/0.12/deploying/) for more information on deployment.

It is recommended to use [Cloud Optimized GeoTIFFs](http://www.cogeo.org) with Terracotta, for best performance.

## The API
Terracotta currently implements the following http API (curly braces denote request parameters):

- http://server.com/tile/{dataset}/{z}/{x}/{y}.png
Serves mercator tile (`x`, `y`) at zoom level `z`, from `dataset`.

- http://server.com/tile/{dataset}/{timestep}/{z}/{x}/{y}.png
Same as previous but for timestepped datasets.
The format of `timestep` is dependent on the dataset.

- http://server.com/datasets
Returns a JSON {'datasets': list of dataset names} response

- http://server.com/meta/{dataset}
Returns a JSON of useful metadata for `dataset`, such as whether or not `dataset` is timestepped,
min/max values of the dataset, WGS84 bounds, datatype and more.

- http://server.com/timesteps/{dataset}
Returns a JSON {'timesteps': list of timesteps for `dataset`} response
or empty list if `dataset` is not timestepped.

- http://server.com/legend/{dataset}
Returns a JSON of `class_names` and associated colormap hex values if `dataset` is categorical.
If `dataset` is not categorical, it returns the colors associated with the `min` and `max` values in `dataset`.

```json
{
  "legend": {
    "land": "#00FF00",
    "water": "#0000FF",
  }
}
```

## Configuration
Datasets and other options are defined in Terracotta's config file.
By default Terracotta looks for `config.cfg` in the current directory.
If you are running Terracotta through its CLI, you can point to a config file by using `--cfg-file`.

### Example configuration
```
[options]
tile_cache_size = 128000000

[yangon]
path = /data/terracotta/yangon
regex = yangon\.tif
categorical = yes
class_names = urban, forest, cropland, grassland, soil, water
class_values = 1, 2, 3, 4, 5, 6

[lake-titicaca]
path = /data/terracotta/lake-titicaca
timestepped = yes
regex = titicaca_(?P<timestep>[0-9]{8})\.tif
```

The config above would give us a server with 2 datasets called `yangon` and `lake-titicaca`.

`yangon` is not timestepped and consists of the single GeoTIFF file `yangon.tif`, which is located in
`/data/terracotta/yangon`.

`yangon` is a categorical dataset, and a call to `http://server.com/legend/yangon` would return a JSON
of the `class_names` and the associated colors given the `class_values` and current colormap.

`lake-titicaca` is timestepped and consists of one or more files, all located in `/data/terracotta/lake-titicaca`.
These files follow the naming scheme `titicaca_yyyymmdd.tif` where `yyyymmdd` are the timesteps associated with the files.
For example: `titicaca_20170101.tif` contains the data for first of January 2017. Tiles from this timestep can be requested through:

`http://server.com/tile/lake-titicaca/20170101/{z}/{x}/{y}.png`.
