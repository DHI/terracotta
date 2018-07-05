
def test_metadata_handler(read_only_database, monkeypatch):
    import terracotta
    settings = terracotta.config.parse_config({'DRIVER_PATH': str(read_only_database)})
    monkeypatch.setattr(terracotta, 'get_settings', lambda: settings)

    from terracotta.handlers import metadata, datasets
    ds = datasets.datasets()[0]
    md = metadata.metadata(ds)
    assert md
    assert md['metadata'] == ['extra_data']
