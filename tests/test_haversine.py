#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uszipcode.packages.haversine import great_circle


def test_all():
    lyon = (45.7597, 4.8422)
    paris = (48.8567, 2.3508)

    delta = 0.01
    assert abs(great_circle(lyon, paris, miles=False)/392.001248 - 1.0) <= delta
    assert abs(great_circle(lyon, paris, miles=True)/243.589575 - 1.0) <= delta


if __name__ == "__main__":
    import py
    py.test.cmdline.main("--tb=native -s")