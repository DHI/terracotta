import json


def test_key_handler(read_only_database, monkeypatch):
    import terracotta
    settings = terracotta.config.parse_config({'DRIVER_PATH': str(read_only_database)})
    monkeypatch.setattr(terracotta, 'get_settings', lambda: settings)

    from terracotta.handlers import keys
    print(str(read_only_database))
    driver = terracotta.get_driver(str(read_only_database))
    assert keys.keys()
    assert keys.keys() == driver.available_keys


def test_key_handler_config(read_only_database, monkeypatch):
    import terracotta
    from terracotta.handlers import keys

    monkeypatch.setenv('TC_DRIVER_PATH', json.dumps(str(read_only_database)))
    terracotta.update_settings()
    driver = terracotta.get_driver(str(read_only_database))
    assert keys.keys()
    assert keys.keys() == driver.available_keys
