def test_metadata_handler(use_testdb):
    from terracotta.handlers import metadata, datasets

    ds = datasets.datasets()[0]
    md = metadata.metadata(None, ds)
    assert md
    assert md["metadata"] == ["extra_data"]

    md = metadata.metadata(["metadata", "bounds"], ds)
    assert md
    assert len(md.keys()) == 3
    assert all(k in md.keys() for k in ("metadata", "bounds", "keys"))


def test_multiple_metadata_handler(use_testdb):
    from terracotta.handlers import metadata, datasets

    ds = datasets.datasets()
    ds1 = list(ds[0].values())
    ds2 = list(ds[1].values())

    md = metadata.multiple_metadata(None, [ds1, ds2])

    assert md
    assert md[0]["metadata"] == ["extra_data"]
    assert len(md) == 2

    md = metadata.multiple_metadata(["metadata", "bounds"], [ds1, ds2])
    assert md
    assert len(md[0].keys()) == 3
    assert all(k in md[0].keys() for k in ("metadata", "bounds", "keys"))
