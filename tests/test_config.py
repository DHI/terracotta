import json

import pytest


def test_env_config(monkeypatch):
    from terracotta import config

    with monkeypatch.context() as m:
        m.setenv('TC_DRIVER_PATH', '"test"')
        assert config.parse_config().DRIVER_PATH == 'test'

    with monkeypatch.context() as m:
        m.setenv('TC_DRIVER_PATH', '"test2"')
        assert config.parse_config().DRIVER_PATH == 'test2'

    with monkeypatch.context() as m:
        m.setenv('TC_DRIVER_PATH', 'test3')
        assert config.parse_config().DRIVER_PATH == 'test3'

    with monkeypatch.context() as m:
        m.setenv('TC_TILE_SIZE', json.dumps([1, 2]))
        assert config.parse_config().TILE_SIZE == (1, 2)


def test_env_config_invalid(monkeypatch):
    from terracotta import config

    with monkeypatch.context() as m:
        m.setenv('TC_TILE_SIZE', '[1')  # unbalanced bracket
        with pytest.raises(ValueError):
            config.parse_config()

    with monkeypatch.context() as m:
        m.setenv('TC_DRIVER_PATH', '{{test: 1}}')  # unquoted key
        with pytest.raises(ValueError):
            config.parse_config()
    assert True


def test_dict_config():
    from terracotta import config

    settings = config.parse_config({'DRIVER_PATH': 'test3'})
    assert settings.DRIVER_PATH == 'test3'

    settings = config.parse_config({'TILE_SIZE': [100, 100]})
    assert settings.TILE_SIZE == (100, 100)


def test_terracotta_settings():
    from terracotta import config
    settings = config.parse_config()

    assert settings.TILE_SIZE

    with pytest.raises(TypeError):
        settings.TILE_SIZE = (10, 10)


def test_settings_repr():
    from terracotta import config
    settings = config.parse_config()
    assert repr(settings)
