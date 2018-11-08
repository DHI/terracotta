
def test_key_handler(testdb, use_testdb):
    import terracotta
    from terracotta.handlers import keys

    driver = terracotta.get_driver(str(testdb))

    handler_response = keys.keys()
    assert handler_response
    assert tuple(row['key'] for row in handler_response) == driver.key_names


def test_key_handler_env_config(testdb, monkeypatch):
    import terracotta
    from terracotta.handlers import keys

    monkeypatch.setenv('TC_DRIVER_PATH', str(testdb))
    terracotta.update_settings()
    driver = terracotta.get_driver(str(testdb))

    handler_response = keys.keys()
    assert handler_response
    assert tuple(row['key'] for row in handler_response) == driver.key_names
