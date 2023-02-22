from io import BytesIO
import json
import urllib.parse
from collections import OrderedDict

from PIL import Image
import numpy as np

import pytest


@pytest.fixture(scope='module')
def flask_app():
    from terracotta.server import create_app
    return create_app()


@pytest.fixture(scope='module')
def client(flask_app):
    with flask_app.test_client() as client:
        yield client


def test_get_keys(client, use_testdb):
    rv = client.get('/keys')

    expected_response = [
        {'key': 'key1'},
        {'key': 'akey'},
        {'key': 'key2', 'description': 'key2'}
    ]
    assert rv.status_code == 200
    assert expected_response == json.loads(rv.data)['keys']


def test_get_metadata(client, use_testdb):
    rv = client.get('/metadata/val11/x/val12/')
    assert rv.status_code == 200
    assert ['extra_data'] == json.loads(rv.data)['metadata']


def test_get_metadata_nonexisting(client, use_testdb):
    rv = client.get('/metadata/val11/x/NONEXISTING/')
    assert rv.status_code == 404


def test_get_datasets(client, use_testdb):
    rv = client.get('/datasets')
    assert rv.status_code == 200
    datasets = json.loads(rv.data, object_pairs_hook=OrderedDict)['datasets']
    assert len(datasets) == 4
    assert OrderedDict([('key1', 'val11'), ('akey', 'x'), ('key2', 'val12')]) in datasets


def test_get_datasets_pagination(client, use_testdb):
    # no page (implicit 0)
    rv = client.get('/datasets?limit=2')
    assert rv.status_code == 200
    response = json.loads(rv.data, object_pairs_hook=OrderedDict)
    assert response['limit'] == 2
    assert response['page'] == 0

    first_datasets = response['datasets']
    assert len(first_datasets) == 2
    assert OrderedDict([('key1', 'val11'), ('akey', 'x'), ('key2', 'val12')]) in first_datasets

    # second page
    rv = client.get('/datasets?limit=2&page=1')
    assert rv.status_code == 200
    response = json.loads(rv.data, object_pairs_hook=OrderedDict)
    assert response['limit'] == 2
    assert response['page'] == 1

    last_datasets = response['datasets']
    assert len(last_datasets) == 2
    assert OrderedDict([('key1', 'val11'), ('akey', 'x'), ('key2', 'val12')]) not in last_datasets

    # page out of range
    rv = client.get('/datasets?limit=2&page=1000')
    assert rv.status_code == 200
    assert not json.loads(rv.data)['datasets']

    # invalid page
    rv = client.get('/datasets?page=-1')
    assert rv.status_code == 400

    # invalid limit
    rv = client.get('/datasets?limit=-1')
    assert rv.status_code == 400


def test_get_datasets_selective(client, use_testdb):
    rv = client.get('/datasets?key1=val21')
    assert rv.status_code == 200
    assert len(json.loads(rv.data)['datasets']) == 3

    rv = client.get('/datasets?key1=val21&key2=val23')
    assert rv.status_code == 200
    assert len(json.loads(rv.data)['datasets']) == 1

    rv = client.get('/datasets?key1=[val21]')
    assert rv.status_code == 200
    assert len(json.loads(rv.data)['datasets']) == 3

    rv = client.get('/datasets?key2=[val23,val24]&akey=x')
    assert rv.status_code == 200
    assert len(json.loads(rv.data)['datasets']) == 2


def test_get_datasets_unknown_key(client, use_testdb):
    rv = client.get('/datasets?UNKNOWN=val21')
    assert rv.status_code == 400


def test_get_singleband_greyscale(client, use_testdb, raster_file_xyz):
    import terracotta
    settings = terracotta.get_settings()

    x, y, z = raster_file_xyz
    rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png')
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == settings.DEFAULT_TILE_SIZE


def test_get_singleband_extra_args(client, use_testdb, raster_file_xyz):
    import terracotta
    settings = terracotta.get_settings()

    x, y, z = raster_file_xyz
    rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png?foo=bar&baz=quz')
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == settings.DEFAULT_TILE_SIZE


def test_get_singleband_cmap(client, use_testdb, raster_file_xyz):
    import terracotta
    settings = terracotta.get_settings()

    x, y, z = raster_file_xyz
    rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png?colormap=jet')
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == settings.DEFAULT_TILE_SIZE


def test_get_singleband_preview(client, use_testdb):
    import terracotta
    settings = terracotta.get_settings()

    rv = client.get('/singleband/val11/x/val12/preview.png?colormap=jet')
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == settings.DEFAULT_TILE_SIZE


def urlsafe_json(payload):
    payload_json = json.dumps(payload)
    return urllib.parse.quote_plus(payload_json, safe=r',.[]{}:"')


def test_get_singleband_explicit_cmap(client, use_testdb, raster_file_xyz):
    import terracotta
    settings = terracotta.get_settings()

    x, y, z = raster_file_xyz
    explicit_cmap = {1: (0, 0, 0), 2.0: (255, 255, 255, 20), 3: '#ffffff', 4: 'abcabc'}

    rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png?colormap=explicit'
                    f'&explicit_color_map={urlsafe_json(explicit_cmap)}')
    assert rv.status_code == 200, rv.data.decode('utf-8')

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == settings.DEFAULT_TILE_SIZE


def test_get_singleband_explicit_cmap_invalid(client, use_testdb, raster_file_xyz):
    x, y, z = raster_file_xyz
    explicit_cmap = {1: (0, 0, 0), 2: (255, 255, 255), 3: '#ffffff', 4: 'abcabc'}

    rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png?'
                    f'explicit_color_map={urlsafe_json(explicit_cmap)}')
    assert rv.status_code == 400

    rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png?colormap=jet'
                    f'&explicit_color_map={urlsafe_json(explicit_cmap)}')
    assert rv.status_code == 400

    rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png?colormap=explicit')
    assert rv.status_code == 400

    explicit_cmap[3] = 'omgomg'
    rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png?colormap=explicit'
                    f'&explicit_color_map={urlsafe_json(explicit_cmap)}')
    assert rv.status_code == 400

    explicit_cmap = [(255, 255, 255)]
    rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png?colormap=explicit'
                    f'&explicit_color_map={urlsafe_json(explicit_cmap)}')
    assert rv.status_code == 400

    rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png?colormap=explicit'
                    f'&explicit_color_map=foo')
    assert rv.status_code == 400


def test_get_singleband_stretch(client, use_testdb, raster_file_xyz):
    import terracotta
    settings = terracotta.get_settings()

    x, y, z = raster_file_xyz

    for stretch_range in ('[0,1]', '[0,null]', '[null, 1]', '[null,null]', 'null'):
        rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png?stretch_range={stretch_range}')
        assert rv.status_code == 200

        img = Image.open(BytesIO(rv.data))
        assert np.asarray(img).shape == settings.DEFAULT_TILE_SIZE


def test_get_singleband_out_of_bounds(client, use_testdb):
    import terracotta
    settings = terracotta.get_settings()

    x, y, z = (0, 0, 10)
    rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png')
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == settings.DEFAULT_TILE_SIZE
    assert np.all(np.asarray(img) == 0)


def test_get_singleband_unknown_cmap(client, use_testdb, raster_file_xyz):
    x, y, z = raster_file_xyz
    rv = client.get(f'/singleband/val11/x/val12/{z}/{x}/{y}.png?colormap=UNKNOWN')
    assert rv.status_code == 400


def test_get_rgb(client, use_testdb, raster_file_xyz):
    import terracotta
    settings = terracotta.get_settings()

    x, y, z = raster_file_xyz
    rv = client.get(f'/rgb/val21/x/{z}/{x}/{y}.png?r=val22&g=val23&b=val24')
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == (*settings.DEFAULT_TILE_SIZE, 3)


def test_get_rgb_preview(client, use_testdb):
    import terracotta
    settings = terracotta.get_settings()

    rv = client.get('/rgb/val21/x/preview.png?r=val22&g=val23&b=val24')
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == (*settings.DEFAULT_TILE_SIZE, 3)


def test_get_rgb_extra_args(client, use_testdb, raster_file_xyz):
    import terracotta
    settings = terracotta.get_settings()

    x, y, z = raster_file_xyz
    rv = client.get(f'/rgb/val21/x/{z}/{x}/{y}.png?r=val22&g=val23&b=val24&foo=bar&baz=quz')
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == (*settings.DEFAULT_TILE_SIZE, 3)


def test_get_rgb_stretch(client, use_testdb, raster_file_xyz):
    import terracotta
    settings = terracotta.get_settings()

    x, y, z = raster_file_xyz

    for stretch_range in ('[0,10000]', '[0,null]', '[null, 10000]', '[null,null]', 'null'):
        rv = client.get(f'/rgb/val21/x/{z}/{x}/{y}.png?r=val22&g=val23&b=val24&'
                        f'r_range={stretch_range}&b_range={stretch_range}&g_range={stretch_range}')
        assert rv.status_code == 200, rv.data

        img = Image.open(BytesIO(rv.data))
        assert np.asarray(img).shape == (*settings.DEFAULT_TILE_SIZE, 3)


def test_get_compute(client, use_testdb, raster_file_xyz):
    import terracotta
    settings = terracotta.get_settings()

    # default tile size
    x, y, z = raster_file_xyz
    rv = client.get(
        f'/compute/val21/x/{z}/{x}/{y}.png'
        '?expression=v1*v2&v1=val22&v2=val23'
        '&stretch_range=[0,10000]'
    )
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == settings.DEFAULT_TILE_SIZE

    # custom tile size
    rv = client.get(
        f'/compute/val21/x/{z}/{x}/{y}.png'
        '?expression=v1*v2&v1=val22&v2=val23'
        '&stretch_range=[0,10000]'
        '&tile_size=[128,128]'
    )
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == (128, 128)


def test_get_compute_preview(client, use_testdb):
    import terracotta
    settings = terracotta.get_settings()

    rv = client.get(
        '/compute/val21/x/preview.png'
        '?expression=v1*v2&v1=val22&v2=val23'
        '&stretch_range=[0,10000]'
    )
    assert rv.status_code == 200

    img = Image.open(BytesIO(rv.data))
    assert np.asarray(img).shape == settings.DEFAULT_TILE_SIZE


def test_get_compute_invalid(client, use_testdb, raster_file_xyz):
    x, y, z = raster_file_xyz

    # too few keys
    rv = client.get(
        f'/compute/val21/{z}/{x}/{y}.png'
        '?expression=v1*v2&v1=val22&v2=val23'
        '&stretch_range=[0,10000]'
    )
    assert rv.status_code == 400

    # invalid expression
    rv = client.get(
        '/compute/val21/x/preview.png'
        '?expression=__builtins__["dir"](v1)&v1=val22'
        '&stretch_range=[0,10000]'
    )
    assert rv.status_code == 400

    # no stretch range
    rv = client.get(
        f'/compute/val21/x/{z}/{x}/{y}.png'
        '?expression=v1*v2&v1=val22&v2=val23'
    )
    assert rv.status_code == 400

    # no expression
    rv = client.get(
        f'/compute/val21/x/{z}/{x}/{y}.png'
        '?stretch_range=[0,10000)'
    )
    assert rv.status_code == 400

    # missing operand
    rv = client.get(
        f'/compute/val21/x/{z}/{x}/{y}.png'
        '?expression=v1*v2'
        '&stretch_range=[0,10000)'
    )
    assert rv.status_code == 400

    # invalid stretch range (syntax)
    rv = client.get(
        f'/compute/val21/x/{z}/{x}/{y}.png'
        '?expression=v1*v2&v1=val22&v2=val23'
        '&stretch_range=[0,10000)'
    )
    assert rv.status_code == 400

    # invalid stretch range (value)
    rv = client.get(
        f'/compute/val21/x/{z}/{x}/{y}.png'
        '?expression=v1*v2&v1=val22&v2=val23'
        '&stretch_range=[10000,0]'
    )
    assert rv.status_code == 400


def test_get_colormap(client):
    rv = client.get('/colormap?stretch_range=[0,1]&num_values=100')
    assert rv.status_code == 200
    assert len(json.loads(rv.data)['colormap']) == 100


def test_get_colormap_invalid(client):
    rv = client.get('/colormap?stretch_range=[0,1')
    assert rv.status_code == 400


def test_get_colormap_extra_args(client):
    rv = client.get('/colormap?stretch_range=[0,1]&num_values=100&foo=bar&baz=quz')
    assert rv.status_code == 200
    assert len(json.loads(rv.data)['colormap']) == 100


def test_get_spec(client):
    from terracotta import __version__

    rv = client.get('/swagger.json')
    assert rv.status_code == 200
    assert json.loads(rv.data)
    assert __version__ in rv.data.decode('utf-8')

    rv = client.get('/apidoc')
    assert rv.status_code == 200
    assert b'Terracotta' in rv.data
