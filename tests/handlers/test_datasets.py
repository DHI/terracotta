
def test_datasets_handler(testdb, use_testdb):
    import terracotta
    from terracotta.handlers import datasets
    driver = terracotta.get_driver(str(testdb))
    keys = driver.key_names
    assert datasets.datasets()
    assert datasets.datasets() == [dict(zip(keys, pair)) for pair in driver.get_datasets().keys()]

    # check key order
    assert all(tuple(ds.keys()) == keys for ds in datasets.datasets())
