# -*- coding: utf-8 -*-

"""
``housing_type_*``. Claimed by ``census-dhc``.

Group quarters population by facility type (all ages, both sexes); universe: group quarters population. One column per bucket, each
the sum of its DHC variables. The buckets are those of the research, checked
against reference values (issue #88).
"""

from ..core import field_group

FIELDS = field_group("housing_type", "2020 Census DHC table PCT19, ZCTA", "people", (
    ("correctional_adult", "Correctional facilities for adults", ("PCT19_005N", "PCT19_037N", "PCT19_069N", "PCT19_102N", "PCT19_134N", "PCT19_166N")),
    ("juvenile", "Juvenile facilities", ("PCT19_012N", "PCT19_044N", "PCT19_076N", "PCT19_109N", "PCT19_141N", "PCT19_173N")),
    ("nursing", "Nursing facilities", ("PCT19_016N", "PCT19_048N", "PCT19_080N", "PCT19_113N", "PCT19_145N", "PCT19_177N")),
    ("other_institutional", "Other institutional facilities", ("PCT19_017N", "PCT19_049N", "PCT19_081N", "PCT19_114N", "PCT19_146N", "PCT19_178N")),
    ("college", "College/University student housing", ("PCT19_024N", "PCT19_056N", "PCT19_088N", "PCT19_121N", "PCT19_153N", "PCT19_185N")),
    ("military", "Military quarters", ("PCT19_025N", "PCT19_057N", "PCT19_089N", "PCT19_122N", "PCT19_154N", "PCT19_186N")),
    ("other_noninstitutional", "Other noninstitutional facilities", ("PCT19_028N", "PCT19_060N", "PCT19_092N", "PCT19_125N", "PCT19_157N", "PCT19_189N")),
))
