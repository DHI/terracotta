import json
from io import BytesIO

from PIL import Image
import numpy as np

import pytest


@pytest.fixture(scope='module')
def flask_app():
    from terracotta.flask_api import create_app
    return create_app()


@pytest.fixture(scope='module')
def client(flask_app):
    with flask_app.test_client() as client:
        yield client


def test_get_colormaps(client):
    rv = client.get('/colormaps')
    assert rv.status_code == 200
    assert 'jet' in json.loads(rv.data)


def test_get_keys(client, use_read_only_database):
    rv = client.get('/keys')
    assert rv.status_code == 200
    assert ['key1', 'key2'] == json.loads(rv.data)


def test_get_metadata(client, use_read_only_database):
    rv = client.get('/metadata/val11/val12/')
    assert rv.status_code == 200
    assert ['extra_data'] == json.loads(rv.data)['metadata']


def test_get_metadata_nonexisting(client, use_read_only_database):
    rv = client.get('/metadata/val11/NONEXISTING/')
    assert rv.status_code == 404


def test_get_datasets(client, use_read_only_database):
    rv = client.get('/datasets')
    assert rv.status_code == 200
    assert ['val11', 'val12'] in json.loads(rv.data)


def test_get_datasets_selective(client, use_read_only_database):
    rv = client.get('/datasets?key1=val21')
    assert rv.status_code == 200
    assert len(json.loads(rv.data)) == 3

    rv = client.get('/datasets?key1=val21&key2=val23')
    assert rv.status_code == 200
    assert len(json.loads(rv.data)) == 1


def test_get_datasets_unknown_key(client, use_read_only_database):
    rv = client.get('/datasets?UNKNOWN=val21')
    assert rv.status_code == 404


def test_get_singleband(client, use_read_only_database, raster_file_xyz):
    import terracotta
    settings = terracotta.get_settings()

    x, y, z = raster_file_xyz
    rv = client.get(f'/singleband/val11/val12/{z}/{x}/{y}.png')
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == (*settings.TILE_SIZE, 4)


def test_get_singleband_out_of_bounds(client, use_read_only_database):
    import terracotta
    settings = terracotta.get_settings()

    x, y, z = (0, 0, 10)
    rv = client.get(f'/singleband/val11/val12/{z}/{x}/{y}.png')
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == (*settings.TILE_SIZE, 2)
    assert np.all(np.asarray(img)[..., -1] == 0)


def test_get_singleband_unknown_cmap(client, use_read_only_database, raster_file_xyz):
    x, y, z = raster_file_xyz
    rv = client.get(f'/singleband/val11/val12/{z}/{x}/{y}.png?colormap=UNKNOWN')
    assert rv.status_code == 400


def test_get_rgb(client, use_read_only_database, raster_file_xyz):
    import terracotta
    settings = terracotta.get_settings()

    x, y, z = raster_file_xyz
    rv = client.get(f'/rgb/val21/{z}/{x}/{y}.png?r=val22&g=val23&b=val24')
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == (*settings.TILE_SIZE, 4)
