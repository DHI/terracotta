
def test_datasets_handler(read_only_database, use_read_only_database):
    import terracotta
    from terracotta.handlers import datasets
    driver = terracotta.get_driver(str(read_only_database))
    keys = driver.available_keys
    assert datasets.datasets()
    assert datasets.datasets() == [dict(zip(keys, pair)) for pair in driver.get_datasets().keys()]
