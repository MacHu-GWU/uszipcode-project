# -*- coding: utf-8 -*-

import pytest
from pytest import raises
from uszipcode.model import Zipcode, STATE_ABBR_SHORT_TO_LONG


class TestZipcode(object):
    def test_city(self):
        z = Zipcode(major_city="New York")
        assert z.major_city == z.city

    def test_bool(self):
        assert bool(Zipcode()) is False
        assert bool(Zipcode(zipcode="10001")) is True

    def test_comparison(self):
        assert Zipcode(zipcode="10001") < Zipcode(zipcode="10002")
        assert Zipcode(zipcode="10002") <= Zipcode(zipcode="10002")
        assert Zipcode(zipcode="10002") > Zipcode(zipcode="10001")
        assert Zipcode(zipcode="10002") >= Zipcode(zipcode="10002")
        assert Zipcode(zipcode="10001") == Zipcode(zipcode="10001")
        assert Zipcode(zipcode="10001") != Zipcode(zipcode="10002")

        with raises(ValueError):
            Zipcode(zipcode="10001") < Zipcode()
        with raises(ValueError):
            Zipcode() < Zipcode(zipcode="10001")

    def test_hash(self):
        assert hash(Zipcode()) != hash(Zipcode(zipcode="10001"))

    def test_state_attr(self):
        z = Zipcode(state="ca")
        assert z.state_abbr == "CA"
        assert z.state_long == STATE_ABBR_SHORT_TO_LONG["CA"]

    def test_glance(self):
        z = Zipcode(zipcode="10001")
        z.glance()


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
