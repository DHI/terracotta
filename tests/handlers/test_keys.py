
def test_key_handler(read_only_database, use_read_only_database):
    import terracotta
    from terracotta.handlers import keys

    driver = terracotta.get_driver(str(read_only_database))

    handler_response = keys.keys()
    assert handler_response
    assert tuple(row['key'] for row in handler_response) == driver.key_names


def test_key_handler_env_config(read_only_database, monkeypatch):
    import terracotta
    from terracotta.handlers import keys

    monkeypatch.setenv('TC_DRIVER_PATH', str(read_only_database))
    terracotta.update_settings()
    driver = terracotta.get_driver(str(read_only_database))

    handler_response = keys.keys()
    assert handler_response
    assert tuple(row['key'] for row in handler_response) == driver.key_names
