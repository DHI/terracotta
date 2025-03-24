from marshmallow import ValidationError
import pytest

from terracotta.server.singleband import SinglebandOptionSchema
from terracotta.server.rgb import RGBOptionSchema


@pytest.mark.parametrize(
    "args, expected",
    [("[0, 1]", [0, 1]), ('["p2", "p28"]', ["p2", "p28"]), (None, None)],
)
def test_serde(args, expected):
    args = {"stretch_range": args}
    option_schema = SinglebandOptionSchema()
    loaded = option_schema.load(args)
    assert loaded["stretch_range"] == expected
    dumped = option_schema.dump(loaded)
    assert dumped["stretch_range"] == expected


def test_serde_validation():
    option_schema = SinglebandOptionSchema()
    with pytest.raises(ValidationError) as exc_info:
        args = {"stretch_range": '["t2", "p28"]'}
        option_schema.load(args)
    assert "Percentile format is `p<digits>`" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        args = {"stretch_range": '[{}, "p28"]'}
        option_schema.load(args)
    assert "Must be a string or a number" in str(exc_info.value)


def test_serde_bad_type():
    option_schema = SinglebandOptionSchema()
    with pytest.raises(ValidationError) as exc_info:
        dump_args = {"stretch_range": [0, {"bad": "type"}]}
        option_schema.dump(dump_args)
    assert "Must be a string or a number" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        load_args = {"stretch_range": '[0, {"bad": "type"}]'}
        option_schema.load(load_args)
    assert "Must be a string or a number" in str(exc_info.value)


@pytest.mark.parametrize(
    "args",
    ["gamma 1 1.5", "sigmoidal r 6 0.5", "gamma r 1.5 sigmoidal 1 8 0.2"],
)
def test_color_transform_singleband_validation(args):
    args = {"color_transform": args}
    option_schema = SinglebandOptionSchema()
    loaded = option_schema.load(args)

    assert loaded["color_transform"] == args["color_transform"]


@pytest.mark.parametrize(
    "args",
    [
        "gamma g 1.5",
        "sigmoidal rg 6 0.5",
        "gamma r 1.5 sigmoidal rgb 8 0.2",
        "sigmoidal 1 5",
        "hue 5",
    ],
)
def test_color_transform_singleband_validation_fail(args):
    args = {"color_transform": args}
    option_schema = SinglebandOptionSchema()
    with pytest.raises(ValidationError):
        option_schema.load(args)


@pytest.mark.parametrize(
    "args",
    [
        "gamma 1 1.5",
        "saturation 0.5",
        "gamma r 1.5 sigmoidal 1 8 0.2",
        "gamma rgb 1.5",
        "sigmoidal rgb 6 0.5",
        "gamma gb 1.5 sigmoidal rg 8 0.2",
    ],
)
def test_color_transform_rgb_validation(args):
    args = {"color_transform": args, "r": "R", "g": "G", "b": "B"}
    option_schema = RGBOptionSchema()
    loaded = option_schema.load(args)

    assert loaded["color_transform"] == args["color_transform"]


@pytest.mark.parametrize(
    "args",
    ["gamma r -1.5", "gamma 1", "gaama rgb 1.5", "sigmoidal 1 5", "hue 5", "gamma 0"],
)
def test_color_transform_rgb_validation_fail(args):
    args = {"color_transform": args, "r": "R", "g": "G", "b": "B"}
    option_schema = RGBOptionSchema()
    with pytest.raises(ValidationError):
        option_schema.load(args)
