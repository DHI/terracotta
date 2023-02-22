import json

import pytest


def test_schema_integrity():
    from terracotta import config
    settings_fields = config.TerracottaSettings._fields
    schema_fields = config.SettingSchema._declared_fields
    assert set(settings_fields) == set(schema_fields)


def test_env_config(monkeypatch):
    from terracotta import config

    with monkeypatch.context() as m:
        m.setenv('TC_DRIVER_PATH', 'test')
        assert config.parse_config().DRIVER_PATH == 'test'

    with monkeypatch.context() as m:
        m.setenv('TC_DRIVER_PATH', 'test2')
        assert config.parse_config().DRIVER_PATH == 'test2'

    with monkeypatch.context() as m:
        m.setenv('TC_DEFAULT_TILE_SIZE', json.dumps([1, 2]))
        assert config.parse_config().DEFAULT_TILE_SIZE == (1, 2)


def test_env_config_invalid(monkeypatch):
    from terracotta import config

    with monkeypatch.context() as m:
        m.setenv('TC_DEFAULT_TILE_SIZE', '[1')  # unbalanced bracket
        with pytest.raises(ValueError):
            config.parse_config()

    with monkeypatch.context() as m:
        m.setenv('TC_DEBUG', 'foo')  # not a boolean
        with pytest.raises(ValueError):
            config.parse_config()

    with monkeypatch.context() as m:
        m.setenv('TC_REMOTE_DB_CACHE_DIR', '/foo/test.sqlite')  # non-existing folder
        with pytest.raises(ValueError):
            config.parse_config()

    assert True


def test_dict_config():
    from terracotta import config

    settings = config.parse_config({'DRIVER_PATH': 'test3'})
    assert settings.DRIVER_PATH == 'test3'

    settings = config.parse_config({'DEFAULT_TILE_SIZE': [100, 100]})
    assert settings.DEFAULT_TILE_SIZE == (100, 100)


def test_terracotta_settings():
    from terracotta import config
    settings = config.parse_config()

    assert settings.DEFAULT_TILE_SIZE

    with pytest.raises(AttributeError):
        settings.DEFAULT_TILE_SIZE = (10, 10)


def test_update_config():
    from terracotta import get_settings, update_settings
    update_settings(DRIVER_PATH='test')
    new_settings = get_settings()
    assert new_settings.DRIVER_PATH == 'test'

    update_settings(DEFAULT_TILE_SIZE=[50, 50])
    new_settings = get_settings()
    assert new_settings.DRIVER_PATH == 'test' and new_settings.DEFAULT_TILE_SIZE == (50, 50)
