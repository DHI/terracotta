import pytest


def test_colorbar_handler(read_only_database, monkeypatch):
    import terracotta
    settings = terracotta.config.parse_config({'DRIVER_PATH': str(read_only_database)})
    monkeypatch.setattr(terracotta, 'get_settings', lambda: settings)

    from terracotta.handlers import datasets, colorbar
    keys = datasets.datasets()[0]
    cbar = colorbar.colorbar(keys, num_values=50)
    assert cbar
    assert len(cbar) == 50


def test_colorbar_error(read_only_database, monkeypatch):
    import terracotta
    settings = terracotta.config.parse_config({'DRIVER_PATH': str(read_only_database)})
    monkeypatch.setattr(terracotta, 'get_settings', lambda: settings)

    from terracotta.handlers import colorbar
    keys = ('too', 'many', 'keys')
    with pytest.raises(terracotta.exceptions.UnknownKeyError):
        colorbar.colorbar(keys)

    keys = ('made-up', 'keys')
    with pytest.raises(terracotta.exceptions.DatasetNotFoundError):
        colorbar.colorbar(keys)
