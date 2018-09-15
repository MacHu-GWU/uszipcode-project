#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from uszipcode.pkg.haversine import great_circle


def test():
    lyon = (45.7597, 4.8422)  # 里昂
    paris = (48.8567, 2.3508)  # 巴黎

    delta = 0.01  # 1% error
    assert abs(great_circle(lyon, paris, miles=False) /
               392.001248 - 1.0) <= delta
    assert abs(great_circle(lyon, paris, miles=True) /
               243.589575 - 1.0) <= delta


if __name__ == "__main__":
    import os

    basename = os.path.basename(__file__)
    pytest.main([basename, "-s", "--tb=native"])
