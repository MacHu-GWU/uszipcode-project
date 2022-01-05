# -*- coding: utf-8 -*-

import pytest
import enum
from uszipcode.tests import SearchEngineBaseTest
from uszipcode.search import validate_enum_arg


def test_validate_enum_arg():
    class Color(enum.Enum):
        red = enum.auto()
        blue = enum.auto()

    with pytest.raises(TypeError):
        validate_enum_arg(Color, "color", "not-a-valid-color")

    validate_enum_arg(Color, "color", Color.red)


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
