# ZIP code universe (primary key of 3.0)

Goal: one row for **every** 5-digit ZIP code we can find, whatever its type (standard, PO box, unique,
military). This list is the primary key of the 3.0 database; statistics are attached to it later,
and a ZIP that has no statistics still keeps its row.

## Run

From the repository root (Python 3.6+, standard library only):

```
python -m data_pipeline.zipcode_universe                     # all sources, including the 2.x list
python -m data_pipeline.zipcode_universe --no-v2             # government sources only
python -m data_pipeline.zipcode_universe --irs-years 2011-2022
python -m pytest data_pipeline/tests -q                      # offline unit tests
```

The HUD step needs a free API token (account at <https://www.huduser.gov/hudapi/public/register>,
dataset "USPS Crosswalk"), read from `$HUD_API_TOKEN` or `~/.hud_token`. Everything else needs no key.
Downloads (about 57 MB) are cached in `data_pipeline/.cache/zipcode_universe/` (ignored by git); a full
run takes about 30 seconds once the files are cached.

Output:

- `data_pipeline/output/zipcode_universe.csv`: one row per ZIP (columns below)
- `data_pipeline/output/zipcode_universe_summary.json`: counts per source and coverage of the 2.x list

## Sources

USPS does not publish a free list of all ZIP codes; its complete list (City State Product) is a paid
product. The list is therefore the union of free sources that each see part of the ZIP universe:

| Source | What it is | Vintage | ZIPs | What it misses |
|---|---|---|---|---|
| `census_zcta` | Census ZIP Code Tabulation Areas, [2025 Gazetteer](https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/2025_Gaz_zcta_national.zip) | 2020 ZCTAs | 33,791 | ZIPs without an area: PO box, unique, military |
| `hud` | [HUD-USPS ZIP Code Crosswalk](https://www.huduser.gov/portal/datasets/usps_crosswalk.html), ZIP to county, built from USPS address data | 2026 Q2 | 39,484 | ZIPs that only serve PO boxes (stated by HUD), military ZIPs |
| `zbp` | Census [ZIP Code Business Patterns](https://www2.census.gov/programs-surveys/cbp/datasets/2023/zbp23totals.zip) totals | 2023 | 34,953 | ZIPs without business establishments |
| `irs` | IRS [SOI ZIP Code Data](https://www.irs.gov/pub/irs-soi/22zpallnoagi.csv) | tax year 2022 | 27,588 | ZIPs with fewer than 100 returns, APO/FPO addresses |
| `v2` | uszipcode 2.x [`simple_db.sqlite`](https://github.com/MacHu-GWU/uszipcode-project/releases/download/1.0.1.db/simple_db.sqlite) | 2.x build | 42,724 | not a government source; frozen at the 2.x build |

HUD includes many ZIPs without any residential address: 3,549 of its ZIPs have only business and/or
"other" addresses (for example 00501, the IRS ZIP in Holtsville, NY). It does not include ZIPs that
only serve PO boxes.

## Result (run of 2026-10-28)

| | ZIPs |
|---|---|
| **All sources (default)** | **42,730** |
| In at least one government source | 39,864 |
| Only in the 2.x list | 2,866 |
| In a government source but not in 2.x (new since 2.x) | 6: 18768, 77352, 84048, 85144, 90140, 90205 |

How much of the 2.x list (by its `zipcode_type`) the government sources cover:

| 2.x type | In 2.x | In a government source | Share |
|---|---|---|---|
| STANDARD | 30,001 | 29,748 | 99.2% |
| PO BOX | 9,397 | 8,709 | 92.7% |
| UNIQUE | 2,539 | 1,401 | 55.2% |
| MILITARY | 787 | 0 | 0% |

The 2,866 ZIPs found only in 2.x: 1,138 unique, 787 military, 688 PO box, 253 standard. The 253
"standard" ones are probably ZIPs retired since the 2.x build, but no free source can confirm it.

All 787 military ZIPs of 2.x fall in the APO/FPO/DPO prefixes (AE 090–099, AA 340, AP 962–966), and no
other ZIP does, so `is_military_prefix` reproduces the 2.x MILITARY type exactly.

Number of government sources per ZIP: 4 sources 27,118 · 3 sources 4,238 · 2 sources 6,122 ·
1 source 2,386 · none (2.x only) 2,866.

## Columns of `zipcode_universe.csv`

| Column | Meaning |
|---|---|
| `zipcode` | 5-digit ZIP, text with leading zeros (the primary key) |
| `city`, `state` | upper case; city from HUD, else ZBP, else 2.x; state from HUD, else ZBP, IRS, 2.x |
| `city_source` | which source gave the city (`hud` 39,484 · `v2` 2,909 · `zbp` 337) |
| `in_census_zcta`, `in_hud`, `in_zbp`, `in_irs`, `in_v2` | 1 if the source lists the ZIP |
| `n_gov_sources` | how many of the four government sources list it (0–4) |
| `is_military_prefix` | 1 for APO/FPO/DPO prefixes |
| `hud_has_residential`, `hud_has_business`, `hud_has_other` | HUD has addresses of that kind in the ZIP (empty if not in HUD) |
| `hud_county_count` | number of counties the ZIP spans in HUD |
| `irs_years` | IRS tax years that list the ZIP |
| `v2_zipcode_type` | the ZIP type stored in 2.x (empty for ZIPs new since 2.x) |

## Open questions for the maintainer

1. **Keep the 2,866 ZIPs that only 2.x knows?** They make the list complete in the 2.x sense (military,
   many unique and PO box ZIPs), but no free government source confirms them and some are probably retired.
   Default here: keep them, flagged by `n_gov_sources = 0`; `--no-v2` drops them.
2. **Verification of those ZIPs.** The only authoritative list is the USPS City State Product (paid,
   through USPS Electronic Product Fulfillment). The free USPS Addresses API can look up the city/state
   of one ZIP at a time and could confirm the 2,866 ZIPs, subject to the USPS API terms of use.
3. **ZIP type for new ZIPs.** 2.x gives a type for 42,724 ZIPs. For ZIPs added later, the HUD flags give
   a reasonable rule (residential addresses → standard; business only → unique; not in HUD and not a
   ZCTA → PO box), and the military prefixes are exact. Should the type be inferred this way?
4. **Refresh cadence.** HUD is quarterly, ZBP and IRS yearly, ZCTAs once per decade. Re-running this
   step each quarter keeps the key list current (new ZIPs such as 85144 appear in HUD first).
