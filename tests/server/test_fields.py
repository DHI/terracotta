from marshmallow import ValidationError
import pytest
from terracotta.server.singleband import SinglebandOptionSchema


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
