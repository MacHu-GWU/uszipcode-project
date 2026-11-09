# -*- coding: utf-8 -*-

"""
``annual_individual_earnings_*``. Claimed by ``census-acs5``.

People 16+ with earnings by sex and earnings band (native ACS bands); universe: population 16
years and over with earnings. One column per bucket, each the sum of its ACS variables. The
buckets are those of the research, checked against reference values (issue #88).
"""

from ..core import census_int, field_group

FIELDS = field_group("annual_individual_earnings", "latest ACS 5-year table B20001, ZCTA", "people", (
    ("male_1_2499", "Male, $1 to $2,499 or loss", ("B20001_003E",)),
    ("male_2500_4999", "Male, $2,500 to $4,999", ("B20001_004E",)),
    ("male_5000_7499", "Male, $5,000 to $7,499", ("B20001_005E",)),
    ("male_7500_9999", "Male, $7,500 to $9,999", ("B20001_006E",)),
    ("male_10000_12499", "Male, $10,000 to $12,499", ("B20001_007E",)),
    ("male_12500_14999", "Male, $12,500 to $14,999", ("B20001_008E",)),
    ("male_15000_17499", "Male, $15,000 to $17,499", ("B20001_009E",)),
    ("male_17500_19999", "Male, $17,500 to $19,999", ("B20001_010E",)),
    ("male_20000_22499", "Male, $20,000 to $22,499", ("B20001_011E",)),
    ("male_22500_24999", "Male, $22,500 to $24,999", ("B20001_012E",)),
    ("male_25000_29999", "Male, $25,000 to $29,999", ("B20001_013E",)),
    ("male_30000_34999", "Male, $30,000 to $34,999", ("B20001_014E",)),
    ("male_35000_39999", "Male, $35,000 to $39,999", ("B20001_015E",)),
    ("male_40000_44999", "Male, $40,000 to $44,999", ("B20001_016E",)),
    ("male_45000_49999", "Male, $45,000 to $49,999", ("B20001_017E",)),
    ("male_50000_54999", "Male, $50,000 to $54,999", ("B20001_018E",)),
    ("male_55000_64999", "Male, $55,000 to $64,999", ("B20001_019E",)),
    ("male_65000_74999", "Male, $65,000 to $74,999", ("B20001_020E",)),
    ("male_75000_99999", "Male, $75,000 to $99,999", ("B20001_021E",)),
    ("male_100000_plus", "Male, $100,000 or more", ("B20001_022E",)),
    ("female_1_2499", "Female, $1 to $2,499 or loss", ("B20001_024E",)),
    ("female_2500_4999", "Female, $2,500 to $4,999", ("B20001_025E",)),
    ("female_5000_7499", "Female, $5,000 to $7,499", ("B20001_026E",)),
    ("female_7500_9999", "Female, $7,500 to $9,999", ("B20001_027E",)),
    ("female_10000_12499", "Female, $10,000 to $12,499", ("B20001_028E",)),
    ("female_12500_14999", "Female, $12,500 to $14,999", ("B20001_029E",)),
    ("female_15000_17499", "Female, $15,000 to $17,499", ("B20001_030E",)),
    ("female_17500_19999", "Female, $17,500 to $19,999", ("B20001_031E",)),
    ("female_20000_22499", "Female, $20,000 to $22,499", ("B20001_032E",)),
    ("female_22500_24999", "Female, $22,500 to $24,999", ("B20001_033E",)),
    ("female_25000_29999", "Female, $25,000 to $29,999", ("B20001_034E",)),
    ("female_30000_34999", "Female, $30,000 to $34,999", ("B20001_035E",)),
    ("female_35000_39999", "Female, $35,000 to $39,999", ("B20001_036E",)),
    ("female_40000_44999", "Female, $40,000 to $44,999", ("B20001_037E",)),
    ("female_45000_49999", "Female, $45,000 to $49,999", ("B20001_038E",)),
    ("female_50000_54999", "Female, $50,000 to $54,999", ("B20001_039E",)),
    ("female_55000_64999", "Female, $55,000 to $64,999", ("B20001_040E",)),
    ("female_65000_74999", "Female, $65,000 to $74,999", ("B20001_041E",)),
    ("female_75000_99999", "Female, $75,000 to $99,999", ("B20001_042E",)),
    ("female_100000_plus", "Female, $100,000 or more", ("B20001_043E",)),
), convert=census_int)
