import pytest

import numpy as np


@pytest.fixture(autouse=True)
def reload_cmap():
    import importlib
    import terracotta.cmaps.get_cmaps

    try:
        yield
    finally:
        importlib.reload(terracotta.cmaps.get_cmaps)


def test_get_cmap():
    from terracotta.cmaps.get_cmaps import get_cmap, AVAILABLE_CMAPS

    for name in AVAILABLE_CMAPS:
        cmap = get_cmap(name)
        assert cmap.shape == (255, 4)
        assert cmap.dtype == np.uint8


def test_get_cmap_filesystem(monkeypatch):
    import importlib
    import importlib.resources

    import terracotta.cmaps.get_cmaps

    def throw_error(*args, **kwargs):
        raise ModuleNotFoundError("monkeypatched")

    with monkeypatch.context() as m:
        m.setattr(importlib.resources, "files", throw_error)

        with pytest.raises(ModuleNotFoundError) as exc_info:
            importlib.resources.files("terracotta")

        (msg,) = exc_info.value.args
        assert msg == "monkeypatched"

        importlib.reload(terracotta.cmaps.get_cmaps)

        cmap = terracotta.cmaps.get_cmaps.get_cmap("jet")
        assert cmap.shape == (255, 4)
        assert cmap.dtype == np.uint8


def test_extra_cmap(monkeypatch, tmpdir):
    import importlib

    import terracotta.cmaps.get_cmaps

    custom_cmap_data = np.tile(np.arange(255, dtype="uint8"), (4, 1)).T
    np.save(str(tmpdir / f"foo{terracotta.cmaps.get_cmaps.SUFFIX}"), custom_cmap_data)
    np.save(str(tmpdir / "bar.npy"), custom_cmap_data)

    with monkeypatch.context() as m:
        m.setenv("TC_EXTRA_CMAP_FOLDER", str(tmpdir))
        importlib.reload(terracotta.cmaps.get_cmaps)

        assert "foo" in terracotta.cmaps.get_cmaps.AVAILABLE_CMAPS
        assert "bar" not in terracotta.cmaps.get_cmaps.AVAILABLE_CMAPS

        np.testing.assert_equal(
            custom_cmap_data, terracotta.cmaps.get_cmaps.get_cmap("foo")
        )


def test_extra_cmap_invalid_shape(monkeypatch, tmpdir):
    import importlib
    import terracotta.cmaps.get_cmaps

    broken_cmap_data = np.tile(np.arange(666, dtype="uint8"), (4, 1)).T
    np.save(str(tmpdir / f"foo{terracotta.cmaps.get_cmaps.SUFFIX}"), broken_cmap_data)

    with monkeypatch.context() as m:
        m.setenv("TC_EXTRA_CMAP_FOLDER", str(tmpdir))

        with pytest.raises(ValueError) as raised_exc:
            importlib.reload(terracotta.cmaps.get_cmaps)

        assert "foo" in str(raised_exc.value)
        assert "666" in str(raised_exc.value)


def test_extra_cmap_invalid_folder(monkeypatch):
    import importlib
    import terracotta.cmaps.get_cmaps

    with monkeypatch.context() as m:
        m.setenv("TC_EXTRA_CMAP_FOLDER", "bar")

        with pytest.raises(IOError) as raised_exc:
            importlib.reload(terracotta.cmaps.get_cmaps)

        assert "bar" in str(raised_exc.value)


def test_extra_cmap_invalid_dtype(monkeypatch, tmpdir):
    import importlib
    import terracotta.cmaps.get_cmaps

    broken_cmap_data = np.tile(np.arange(255, dtype="float"), (4, 1)).T
    np.save(str(tmpdir / f"foo{terracotta.cmaps.get_cmaps.SUFFIX}"), broken_cmap_data)

    with monkeypatch.context() as m:
        m.setenv("TC_EXTRA_CMAP_FOLDER", str(tmpdir))

        with pytest.raises(ValueError) as raised_exc:
            importlib.reload(terracotta.cmaps.get_cmaps)

        assert "foo" in str(raised_exc.value)
        assert "float" in str(raised_exc.value)
