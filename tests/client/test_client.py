import pytest


@pytest.fixture(scope='module')
def client_app(test_server):
    from terracotta.client.flask_api import create_app
    yield create_app(test_server)


@pytest.fixture()
def client(client_app, test_server):
    with client_app.test_client() as client:
        yield client


def test_get_app(client, test_server):
    rv = client.get('/')
    assert rv.status_code == 200
    assert 'Terracotta Preview' in rv.data.decode('utf-8')
