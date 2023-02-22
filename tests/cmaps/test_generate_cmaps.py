
def test_generate_cmaps(tmpdir):
    from terracotta.cmaps.get_cmaps import SUFFIX
    from terracotta.cmaps.generate_cmaps import generate_maps
    generate_maps(str(tmpdir))
    assert (tmpdir / f'jet{SUFFIX}').check(file=True)
