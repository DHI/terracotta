import pytest


@pytest.fixture(scope='module')
def client_defaults():
    from terracotta.server import create_app
    flask_app = create_app()
    with flask_app.test_client() as client:
        yield client


@pytest.fixture(scope='module')
def client_metadata_disallowed():
    from terracotta.server import create_app
    import terracotta
    terracotta.update_settings(
        ALLOWED_ORIGINS_METADATA=''
    )
    flask_app = create_app()
    with flask_app.test_client() as client:
        yield client


@pytest.fixture(scope='module')
def client_all_allowed():
    from terracotta.server import create_app
    import terracotta
    terracotta.update_settings(
        ALLOWED_ORIGINS_METADATA='*',
        ALLOWED_ORIGINS_TILES='*'
    )
    flask_app = create_app()
    with flask_app.test_client() as client:
        yield client


@pytest.fixture(scope='module')
def valid_metadata_path():
    return '/metadata/val11/x/val12/'


@pytest.fixture(scope='module')
def valid_singleband_path(raster_file_xyz):
    x, y, z = raster_file_xyz
    return f'/singleband/val11/x/val12/{z}/{x}/{y}.png'


def test_cors_defaults(
    client_defaults, use_testdb, valid_metadata_path, valid_singleband_path
):
    rv = client_defaults.get(valid_metadata_path)
    assert rv.status_code == 200
    assert 'Access-Control-Allow-Origin' in rv.headers

    rv = client_defaults.get(valid_singleband_path)
    assert rv.status_code == 200
    assert 'Access-Control-Allow-Origin' not in rv.headers


def test_cors_all_allowed(
        client_all_allowed, use_testdb, valid_metadata_path, valid_singleband_path
):
    rv = client_all_allowed.get(valid_metadata_path)
    assert rv.status_code == 200
    assert 'Access-Control-Allow-Origin' in rv.headers

    rv = client_all_allowed.get(valid_singleband_path)
    assert rv.status_code == 200
    assert 'Access-Control-Allow-Origin' in rv.headers


def test_cors_metadata_disallowed(client_metadata_disallowed, use_testdb, valid_metadata_path):
    rv = client_metadata_disallowed.get(valid_metadata_path)
    assert rv.status_code == 200
    assert 'Access-Control-Allow-Origin' not in rv.headers
