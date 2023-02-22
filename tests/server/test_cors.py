import json

import pytest


def get_client(metadata_origins=None, tile_origins=None):
    from terracotta.server import create_app
    import terracotta

    if metadata_origins is not None:
        terracotta.update_settings(ALLOWED_ORIGINS_METADATA=metadata_origins)

    if tile_origins is not None:
        terracotta.update_settings(ALLOWED_ORIGINS_TILES=tile_origins)

    flask_app = create_app()
    return flask_app.test_client()


@pytest.fixture
def valid_metadata_path():
    return '/metadata/val11/x/val12/'


@pytest.fixture
def valid_singleband_path(raster_file_xyz):
    x, y, z = raster_file_xyz
    return f'/singleband/val11/x/val12/{z}/{x}/{y}.png'


@pytest.mark.parametrize('tile_origins', (None, '["*"]', '[]', '["example.org"]'))
@pytest.mark.parametrize('metadata_origins', (None, '["*"]', '[]', '["example.org"]'))
def test_cors(use_testdb, valid_metadata_path, valid_singleband_path,
              metadata_origins, tile_origins):
    with get_client(metadata_origins, tile_origins) as client:
        # metadata
        rv = client.get(valid_metadata_path)
        assert rv.status_code == 200

        if metadata_origins == '[]':
            assert 'Access-Control-Allow-Origin' not in rv.headers
        elif metadata_origins is None:
            # default for metadata is allow all
            assert rv.headers['Access-Control-Allow-Origin'] == '*'
        else:
            expected = json.loads(metadata_origins)
            if len(expected) == 1:
                expected = expected[0]
            assert rv.headers['Access-Control-Allow-Origin'] == expected

        # tiles
        rv = client.get(valid_singleband_path)
        assert rv.status_code == 200

        if tile_origins == '[]':
            assert 'Access-Control-Allow-Origin' not in rv.headers
        elif tile_origins is None:
            # default for tiles is disallow all
            assert 'Access-Control-Allow-Origin' not in rv.headers
        else:
            expected = json.loads(tile_origins)
            if len(expected) == 1:
                expected = expected[0]
            assert rv.headers['Access-Control-Allow-Origin'] == expected
