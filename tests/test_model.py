# -*- coding: utf-8 -*-

import pytest
from pytest import raises
from uszipcode.model import SimpleZipcode as Zipcode, MAPPER_STATE_ABBR_SHORT_TO_LONG


class TestZipcode(object):
    def test_city(self):
        z = Zipcode(major_city="New York")
        assert z.major_city == z.city

    def test_bool(self):
        assert bool(Zipcode()) is False
        assert bool(Zipcode(zipcode="10001")) is True
        assert bool(Zipcode(zipcode="")) is True

    def test_comparison(self):
        assert Zipcode(zipcode="10001") < Zipcode(zipcode="10002")
        assert Zipcode(zipcode="10002") <= Zipcode(zipcode="10002")
        assert Zipcode(zipcode="10002") > Zipcode(zipcode="10001")
        assert Zipcode(zipcode="10002") >= Zipcode(zipcode="10002")
        assert Zipcode(zipcode="10001") == Zipcode(zipcode="10001")
        assert Zipcode(zipcode="10001") != Zipcode(zipcode="10002")

        with raises(ValueError):
            _ = Zipcode(zipcode="10001") < Zipcode()

        with raises(ValueError):
            _ = Zipcode() < Zipcode(zipcode="10001")

    def test_hash(self):
        z_set_1 = {
            Zipcode(zipcode="10001"),
            Zipcode(zipcode="10002"),
        }
        z_set_2 = {
            Zipcode(zipcode="10002"),
            Zipcode(zipcode="10003"),
        }
        assert len(z_set_1.union(z_set_2)) == 3
        assert len(z_set_1.intersection(z_set_2)) == 1
        assert z_set_1.difference(z_set_2).pop().zipcode == "10001"

        assert hash(Zipcode()) != hash(Zipcode(zipcode="10001"))

    def test_state_attr(self):
        z = Zipcode(state="ca")
        assert z.state_abbr == "CA"
        assert z.state_long == MAPPER_STATE_ABBR_SHORT_TO_LONG["CA"]

    def test_glance(self):
        z = Zipcode(zipcode="10001")
        z.glance()


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
