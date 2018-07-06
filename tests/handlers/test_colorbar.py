import pytest


def test_colorbar_handler(use_read_only_database):
    from terracotta.handlers import datasets, colorbar
    keys = datasets.datasets()[0]
    cbar = colorbar.colorbar(keys, num_values=50)
    assert cbar
    assert len(cbar) == 50


def test_colorbar_error(use_read_only_database):
    import terracotta
    from terracotta.handlers import colorbar

    keys = ('too', 'many', 'keys')
    with pytest.raises(terracotta.exceptions.UnknownKeyError):
        colorbar.colorbar(keys)

    keys = ('made-up', 'keys')
    with pytest.raises(terracotta.exceptions.DatasetNotFoundError):
        colorbar.colorbar(keys)
