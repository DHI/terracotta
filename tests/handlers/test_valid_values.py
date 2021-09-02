
def test_valid_values_handler(testdb, use_testdb):
    import terracotta
    from terracotta.handlers import valid_values

    driver = terracotta.get_driver(str(testdb))

    handler_response = valid_values.valid_values({})
    assert handler_response
    assert set(handler_response.keys()) == set(driver.key_names)
