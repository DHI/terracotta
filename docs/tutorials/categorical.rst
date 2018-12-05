How to serve categorical data with Terracotta
=============================================

Categorical datasets are special , because the numerical pixel values
carry no direct meaning, but rather encode which category or label the
pixel belongs to. Because labels must be preserved, serving categorical
data comes with its own set of complications:

-  Dynamical stretching does not make sense
-  Nearest neighbor resampling must be used
-  Labels must be mapped to colors consistently

Terracotta does not know categories and labels, but the API is flexible
enough to give you the tools to build your own system and do the
interpretation in the frontend. You can serve categorical data by
following these steps:

During ingestion
----------------

1. Create an additional key to encode whether a dataset is categorical
   or not. E.g., if you are currently using the keys ``sensor``,
   ``date``, and ``band``, ingest your data with the keys
   ``[type, sensor, date, band]``, where ``type`` can take one of the
   values ``categorical``, ``index``, ``reflectance``, or whatever makes
   sense for your given application.

2. Attach a mapping ``category name -> pixel value`` to the metadata of
   your categorical dataset. Using the :doc:`Python API <../api>`, you
   could do it like this:

   .. code-block:: python

      import terracotta as tc

      driver = tc.get_driver('terracotta.sqlite')

      # assuming key names are [type, sensor, date, band]
      key_values = ['categorical', 'S2', '20181010', 'cloudmask']
      raster_path = 'cloud_mask.tif'

      category_map = {
          'clear land': 0,
          'clear water': 1,
          'cloud': 2,
          'cloud shadow': 3
      }

      with driver.connect():
          metadata = driver.compute_metadata(
              raster_path,
              extra_metadata={'categories': category_map}
          )
          driver.insert(key_values, raster_path, metadata=metadata)


In the frontend
---------------

Ingesting categorical data this way allows us to access it from the
frontend. Given that your Terracotta server runs at ``example.com``, you
can use the following functionality:

-  To get a list of all categorical data, simply send a GET request to
   ``example.com/datasets?type=categorical``.
-  To get the available categories of a dataset, query
   ``example.com/metadata/categorical/S2/20181010/cloudmask``. The
   returned JSON object will contain a section like this:

   .. code-block:: json

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

-  To get correctly labelled imagery, the frontend will have to pass an
   explicit color mapping of pixel values to colors by using
   ``/singleband``'s ``explicit_color_map`` argument. In our case,
   this could look like this::

      example.com/singleband/categorical/S2/20181010/cloudmask/
      {z}/{x}/{y}.png?colormap=explicit&explicit_color_map=
      {"0": "99d594", "1": "2b83ba", "2": "ffffff", "3": "404040"}

   .. note::

      Depending on your architecture, it might be required to encode all
      special characters in the query, such as ``{``, ``}``, and ``:``.
      This is e.g. the case when using AWS API Gateway / AWS Lambda.

   Supplying an explicit color map in this fashion suppresses
   stretching, and forces Terracotta to only use nearest neighbor
   resampling when reading the data.

   Colors can be passed as hex strings (as in this example) or RGBA color
   tuples. In case you are looking for a nice color scheme for your
   categorical datasets, `color brewer <http://colorbrewer2.org>`__
   features some excellent suggestions.
