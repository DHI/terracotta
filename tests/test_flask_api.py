import json

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
