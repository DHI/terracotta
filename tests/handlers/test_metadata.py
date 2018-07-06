
def test_metadata_handler(use_read_only_database):
    from terracotta.handlers import metadata, datasets
    ds = datasets.datasets()[0]
    md = metadata.metadata(ds)
    assert md
    assert md['metadata'] == ['extra_data']
