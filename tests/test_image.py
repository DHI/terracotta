import pytest

from PIL import Image
import numpy as np


def test_array_to_png_singleband():
    from terracotta import image
    testdata = np.random.randint(0, 256, size=(256, 512), dtype='uint8')
    out_img = Image.open(image.array_to_png(testdata)).convert('RGBA')
    out_data = np.asarray(out_img)

    assert out_data.shape[:-1] == testdata.shape
    assert np.all(out_data[testdata == 0, -1] == 0)
    assert np.all(out_data[testdata != 0, -1] == 255)
    np.testing.assert_array_equal(testdata, out_data[..., 0])


def test_array_to_png_singleband_invalid():
    from terracotta import image, exceptions

    with pytest.raises(exceptions.InvalidArgumentsError) as exc:
        image.array_to_png(np.zeros((20, 20)), colormap='unknown')
    assert 'invalid color map' in str(exc.value)

    with pytest.raises(exceptions.InvalidArgumentsError) as exc:
        image.array_to_png(np.zeros((20, 20)), colormap=[(0, 0, 0, 0)] * 1000)
    assert 'must contain less' in str(exc.value)

    with pytest.raises(ValueError) as exc:
        image.array_to_png(np.zeros((20, 20)), colormap=[(0, 0, 0)] * 10)
    assert 'must have shape' in str(exc.value)


def test_array_to_png_rgb():
    from terracotta import image
    testdata = np.random.randint(0, 256, size=(256, 512, 3), dtype='uint8')
    out_img = Image.open(image.array_to_png(testdata)).convert('RGBA')
    out_data = np.asarray(out_img)

    assert out_data.shape[:-1] == testdata.shape[:-1]
    assert np.all(out_data[np.all(testdata == 0, axis=-1), -1] == 0)
    assert np.all(out_data[~np.all(testdata == 0, axis=-1), -1] == 255)
    np.testing.assert_array_equal(testdata, out_data[..., :-1])


def test_array_to_png_rgb_invalid():
    from terracotta import image

    too_many_bands = np.random.randint(0, 256, size=(256, 512, 4), dtype='uint8')
    with pytest.raises(ValueError) as exc:
        image.array_to_png(too_many_bands)
    assert 'must have three bands' in str(exc.value)

    with pytest.raises(ValueError) as exc:
        image.array_to_png(np.zeros((20, 20, 3)), colormap='viridis')
    assert 'Colormap argument cannot be given' in str(exc.value)

    with pytest.raises(ValueError) as exc:
        image.array_to_png(np.array([]))
    assert '2 or 3 dimensions' in str(exc.value)


def test_contrast_stretch():
    from terracotta import image
    data = np.arange(0, 10)

    np.testing.assert_array_equal(
        image.contrast_stretch(data, (0, 10), (10, 20)),
        np.arange(10, 20)
    )

    np.testing.assert_array_equal(
        image.contrast_stretch(data, (5, 6), (10, 20), clip=True),
        np.array([10, 10, 10, 10, 10, 10, 20, 20, 20, 20])
    )

    np.testing.assert_array_equal(
        image.contrast_stretch(data, (5, 6), (10, 20), clip=False),
        np.array([-40, -30, -20, -10, 0, 10, 20, 30, 40, 50])
    )


def test_to_uint8():
    from terracotta import image

    data = np.array([-50, 0, 10, 255, 256, 1000])
    np.testing.assert_array_equal(
        image.to_uint8(data, -50, 1000),
        [1, 13, 15, 74, 75, 255]
    )


def test_label():
    from terracotta import image

    data = np.array([15, 16, 17])
    np.testing.assert_array_equal(image.label(data, [17, 15]), np.array([2, 0, 1]))


def test_label_invalid():
    from terracotta import image

    data = np.array([15, 16, 17])
    with pytest.raises(ValueError) as exc:
        image.label(data, list(range(1000)))
    assert 'more than 255 labels' in str(exc.value)
