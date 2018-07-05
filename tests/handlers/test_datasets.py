
def test_datasets_handler(read_only_database, use_read_only_database):
    import terracotta
    from terracotta.handlers import datasets
    driver = terracotta.get_driver(str(read_only_database))
    assert datasets.datasets()
    assert datasets.datasets() == [list(pair) for pair in driver.get_datasets().keys()]
