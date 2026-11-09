# Database step: the crawler registry

Builds the 3.0 database from the outputs of named crawlers. Rows are PKs (ZIP codes), columns are
`zipcode` plus one column per Field, and NULL simply means "no value" (a PO box ZIP has no population).

## Layout

The functionality, the crawlers and the Fields are kept apart, so that new columns only add small
files and never touch the functionality. [`test_db_structure.py`](../tests/test_db_structure.py) fails
if a module crosses these lines.

| Where | What | Rule |
|---|---|---|
| `database/*.py` | **the functionality**: [`core`](core.py), [`checks`](checks.py), [`fetch`](fetch.py), [`crawl`](crawl.py), [`build`](build.py), [`cli`](cli.py) | knows no data source and no column; only `fetch.py` opens a URL |
| [`database/crawlers/`](crawlers) | **one module per data source**; [`__init__.py`](crawlers/__init__.py) holds `CRAWLERS`, the registry | downloads and parses; claims Fields by their modules; cannot open a URL and never reads a value |
| [`database/fields/`](fields) | **one module per Field or per group of Fields**; [`__init__.py`](fields/__init__.py) holds `FIELDS`, the catalog | says what the column is and how to read it from a source row; imports only `core` |
| [`database/__main__.py`](__main__.py) | joins the three | the only place that does |

| Concept | Rule |
|---|---|
| **PK** | a 5-digit ZIP as text with leading zeros |
| **PK set** | the rows of one build: `demo` (3 ZIPs), `full` (every ZIP of [`zipcode_universe`](../zipcode_universe/README.md)) or a CSV file with a `zipcode` column |
| **Field** | one column: name, dtype (`int`/`float`/`str`), description, unit, `extract` and `examples`. The catalog's order is the column order |
| **Source row** | one row of a data source under its own column names, e.g. `{"P1_001N": "32612"}` |
| **Crawler** | a name, the Fields it claims, the files it downloads and a pure `parse()` that yields `(zipcode, source row)`. Every Field is claimed by exactly one crawler |

`crawl` runs one crawler: fetch (the only network step, cached), parse (offline), each claimed Field
reads its value from the source rows, check the output contract, write. `build` left-joins every crawler
output onto the PK set; it never downloads anything, so switching PK sets is free.

A Field module is this short ([`fields/population.py`](fields/population.py)):

```python
FIELDS = (
    Field(
        name="population",
        dtype=int,
        description="Total population of the ZCTA, 2020 Census DHC table P1 (P1_001N)",
        unit="people",
        extract=column("P1_001N", parse_int),
        examples=(({"P1_001N": "32612"}, 32612), ({"P1_001N": "0"}, 0), ({"P1_001N": None}, None)),
    ),
)
```

A distribution is one module with one column per bucket; each bucket is the sum of its source columns
([`fields/population_by_age.py`](fields/population_by_age.py)):

```python
FIELDS = field_group("population_by_age", "2020 Census DHC table P12, ZCTA", "people", (
    ("male_0_4", "Male 0-4", ("P12_003N",)),
    ("male_15_19", "Male 15-19", ("P12_006N", "P12_007N")),
    ...
))
```

A crawler claims Fields by their modules, so a typo is an import error
([`crawlers/census_gazetteer.py`](crawlers/census_gazetteer.py)):

```python
fields=field_names(lat, lng, land_area_in_sqmi, water_area_in_sqmi),
```

## Run

The tasks are in [`mise.toml`](../../mise.toml) at the repository root. It pins Python 3.12; the pipeline
needs 3.11 or newer (it reads `mise.toml` with `tomllib`) and only the standard library, plus `pytest`
for the tests. Once per clone:

```
mise trust
mise install
mise run pipeline-setup
```

| Command | What it does |
|---|---|
| `mise run pipeline-check` | checks the catalog, the claims and the tasks; prints the catalog |
| `mise run crawler-<name>` | runs one crawler, e.g. `mise run crawler-census-dhc` (cached download) |
| `mise run crawler-<name> -- --refresh` | downloads that crawler's files again (at most once per 24 h; add `--force` to override) |
| `mise run crawl-all` | runs every crawler, one after another, and stops at the first failure |
| `mise run pipeline-build` | builds the database for the demo PK set |
| `mise run pipeline-build -- --pk-set full` | builds it for all 42,730 ZIPs (or `--pk-set path/to/pks.csv`) |
| `mise run pipeline-test` | runs the offline tests (no network) |

Without mise, run the same commands with `python -m data_pipeline.database check | crawl NAME | crawl --all | build`
from the repository root. Exit codes: 0 success, 2 registry / contract / PK-set problems, 1 download
and file problems. Expected errors print one message without a traceback.

Three crawlers need a free key: `census-dhc` and `census-acs5` (<https://api.census.gov/data/key_signup.html>,
read from `$CENSUS_API_KEY` or `~/.census_key`) and `zip-basics` (<https://www.huduser.gov/hudapi/public/register>,
read from `$HUD_API_TOKEN` or `~/.hud_token`). A key is added to the request in memory only: it is never
written to the cache, the manifest, the outputs or an error message.

Files:

- `data_pipeline/.cache/crawlers/<name>/`: raw downloads and `manifest.json` (url, bytes, sha256, time); ignored by git
- `data_pipeline/output/crawlers/<name>.csv` and `.json`: one row per ZIP in the source; ignored by git
- `data_pipeline/output/db_<set>.sqlite` (table `zipcode_data`), `db_<set>.csv` and `db_<set>_coverage.json`;
  only `db_demo.csv` and `db_demo_coverage.json` are committed

## Crawlers and Fields

| Crawler | Source | Download | Fields |
|---|---|---|---|
| `zip-basics` | [HUD-USPS crosswalk](https://www.huduser.gov/portal/datasets/usps_crosswalk.html), Census Gazetteer counties, Census ZBP, uszipcode 2.x | 4 files, 20 MB, token for HUD | `zipcode_type` (2.x only), `major_city`, `state` (HUD, else ZBP, else 2.x), `county` (HUD's main county with the Gazetteer name, else 2.x), `county_fips` (HUD) |
| `census-gazetteer` | Census [2025 Gazetteer, ZCTA file](https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/2025_Gaz_zcta_national.zip) | 1 file, 0.9 MB, no key | `lat`, `lng` (ZCTA internal point), `land_area_in_sqmi`, `water_area_in_sqmi` |
| `census-dhc` | 2020 Census DHC through the [Census Data API](https://api.census.gov/data/2020/dec/dhc.html) | 4 requests (at most 50 variables each), 31 MB, key | `population`, `housing_units`, `occupied_housing_units` and 10 distributions, 128 columns: `population_by_gender_*` (2), `population_by_age_*` (36), `children_by_age_*` (42), `population_by_race_*` (7), `families_vs_singles_*` (5), `households_with_kids_*` (2), `head_of_household_by_age_*` (16), `housing_type_*` (7, group quarters), `housing_occupancy_*` (4), `vacancy_reason_*` (7) |
| `census-acs5` | [ACS 5-year](https://api.census.gov/data/2024/acs/acs5.html), latest vintage (`YEAR = 2024`: 2020-2024, dollars of 2024) | 6 requests (at most 50 variables each), 36 MB, key | `median_age`, `median_home_value`, `median_household_income`, `median_rent`, each with its `_moe` (90% margin of error), `poverty_rate`, and 11 distributions, 128 columns: `owner_occupied_home_values_*` (11), `year_housing_was_built_*` (10), `rental_properties_by_number_of_rooms_*` (4), `monthly_rent_including_utilities_*` (28), `household_income_*` (7), `annual_individual_earnings_*` (40), `employment_status_*` (3), `means_of_transportation_to_work_*` (6), `travel_time_to_work_in_minutes_*` (8), `educational_attainment_*` (8), `school_enrollment_age_3_to_17_*` (3) |

| `irs-soi` | IRS [SOI ZIP Code Data](https://www.irs.gov/statistics/soi-tax-stats-individual-income-tax-statistics-zip-code-data-soi), latest tax year (`YEAR = 2023`) | 1 file, 40 MB, no key | for 11 income sources, the share of tax returns with it and the average amount among them (22 columns): `sources_of_household_income_*` (wages, business, partnership and S corporation, unemployment), `household_investment_income_*` (interest, ordinary and qualified dividends, capital gains), `household_retirement_income_*` (IRA distributions, pensions and annuities, Social Security) |

The Census values are ZCTA values: a ZIP without a ZCTA (PO box, unique, military) gets NULL. The IRS
values are by the ZIP taxpayers write on their returns; they cover returns, not households, and only taxable
amounts; ZIPs with fewer than 100 returns are pooled by the IRS and get NULL. The ACS
writes "not available" as negative codes (for example -666666666); they are read as NULL. The
distribution buckets are those of the research (issue #88), which were checked against reference values;
the modules were generated from its bucket definitions and the values below match it exactly. Where a
2.x name plus a bucket would pass 60 characters, the module has a shorter name and says which 2.x field
it stands for (`means_of_transportation_to_work`, `educational_attainment`).

## Politeness

Enforced in [`fetch.py`](fetch.py), the only module that opens a URL; crawlers cannot change it.

- A crawler declares whole files (1 to 100 per crawler), never one request per ZIP.
- A cached file is reused: no request, and the key is not even read. A crawler downloads once.
- Downloads run one at a time, 2 s apart, with a User-Agent that names this project.
- Retries only on connection errors, timeouts, 429 and 5xx: 5 attempts, waits of 5, 15, 45 and 90 s
  (`Retry-After` is honoured up to 300 s). Any other 4xx fails at once.
- The body must start with the declared magic bytes (`PK\x03\x04` for a zip, `[[` for the Census API),
  so an HTML error page is never cached. A failed download keeps the previous file.
- `--refresh` is refused if the crawler downloaded less than 24 h ago (`--force` overrides). There is
  no loop, schedule or watch mode.

## Checks

`check`, `crawl` and `build` first run every registry check and report all problems at once, each
with how to fix it:

| IDs | Checks |
|---|---|
| F1-F7 | Field names are snake_case, `zipcode` is reserved, no duplicates, dtype is `int`/`float`/`str`, a description is given, an `extract` is given, the catalog fits SQLite's 2,000 columns |
| C1-C8 | crawler names are kebab-case and unique; a crawler claims Fields and declares 1 to 100 downloads; filenames are safe and unique; URLs are `https://` and hold no key; a Secret is well formed; no URL is downloaded by two crawlers |
| K1-K3 | every claim names a Field of the catalog (with "did you mean"), no Field is claimed twice, **no Field is left unclaimed** |
| M0-M2 | `mise.toml` is valid, every crawler has its `crawler-<name>` task (the check prints the block to add), no task points to a missing crawler |
| L1 | (`check` only) every module of `fields/` and `crawlers/` is listed in its package's `MODULES` |

Before anything is written, the values read from the source rows are checked against the output contract:

| ID | Rule |
|---|---|
| D1 | no ZIP appears twice (after normalizing, e.g. `501` -> `00501`) |
| D2 | a Field can read its value: a missing source column or a value that cannot be converted is an error |
| D3 | values match the dtype (int is not bool, a float Field accepts an int) |
| D4 | a claimed Field is not NULL in every row (the source probably changed its header) |
| D5 | at least one usable row |
| D6 | no NaN or infinity |

Keys that are not ZIPs (`00000`, text) are skipped and counted. On any error nothing is written and
the previous output stays. `build` also checks that each crawler output exists and matches the
crawler's current claims, and says which `mise run crawler-<name>` to run if not.

## Result (run of 2026-11-09)

`mise run crawl-all` makes 16 requests the first time and 0 after that. `mise run pipeline-build`
then writes [`db_demo.csv`](../output/db_demo.csv): 3 rows x 300 columns. Its first columns:

```
zipcode,zipcode_type,major_city,state,county,county_fips,lat,lng,land_area_in_sqmi,water_area_in_sqmi,population,...
10001,STANDARD,NEW YORK,NY,New York County,36061,40.750649,-73.997298,0.624,0.0,32612,...
20013,PO BOX,WASHINGTON,DC,District of Columbia,11001,,,,,,...
20037,STANDARD,WASHINGTON,DC,District of Columbia,11001,38.892459,-77.053811,0.732,0.231,14945,...
```

20013 is a Washington, DC PO box ZIP: it has a city, a state and a county, but no ZCTA and no IRS row,
so its other 294 columns are NULL. This is expected, not an error. [`db_demo_coverage.json`](../output/db_demo_coverage.json)
counts it under `not_in_source` for those Fields. For 20037 the 2020-2024 ACS gives a median age of 30.4,
a median home value of $685,300, a median household income of $111,153 and a median rent of $2,538; in tax
year 2023, 81.2% of its returns had wages, averaging $128,954.

With `--pk-set full` (42,730 ZIPs, about 12 seconds, no downloads):

| Fields | ZIPs with a value |
|---|---|
| `major_city`, `state` | 42,730 |
| `zipcode_type` | 42,724 (the 6 ZIPs newer than 2.x have none) |
| `county` | 41,866 |
| `county_fips` | 39,475 (HUD only) |
| `lat`, `lng`, `land_area_in_sqmi`, `water_area_in_sqmi` | 33,791 |
| `population`, the housing counts and the 128 DHC distribution columns | 33,774 |
| the 128 ACS distribution columns | 33,772 |
| `poverty_rate`, `median_age`, `median_household_income`, `median_home_value`, `median_rent` | 32,878, 32,820, 30,547, 30,260, 25,751 |
| the 22 IRS income-source columns | 27,689 |

Checked against earlier work:

- `major_city`, `state` and `zipcode_type` match `zipcode_universe.csv` row by row.
- The 4,323,072 DHC distribution values (33,774 ZCTAs x 128 columns), `water_area_in_sqmi` and
  `occupied_housing_units` match the research database exactly.
- `census-acs5` was also run once for the 2019-2023 vintage, the one the research used: its 4,322,816
  distribution values (33,772 ZCTAs x 128 columns) and the 9 median, margin and poverty columns match the
  research database exactly. The committed outputs use 2020-2024.
- `irs-soi` was also run on the tax year 2022 file the research used: its 303,468 shares and 303,468
  averages (27,588 ZIPs x 11 sources) match the research database exactly. The committed outputs use 2023.
- `county_fips` differs from the research database for 10 ZIPs. For 9 of them HUD gives only a 2-digit
  state code (island areas such as 96799, and 77352), which is now NULL. For 51603 two counties tie
  exactly, and the lower code is taken.

The 17 ZCTAs in the 2025 Gazetteer but not in the 2020 DHC are in the island areas (U.S. Virgin Islands
008xx, Guam, the Northern Mariana Islands and American Samoa), which the DHC file does not cover.

The registry is not tied to these numbers: the tests build fake registries of 1 PK / 1 Field /
1 crawler, 3 / 5 / 2, 30 / 10 / 4, 300 / 64 / 8 and 5 / 300 / 3 and run check, crawl, build and refresh on each.

## Add a column

**From a source that already has a crawler** (for example, another DHC variable):

1. Add `fields/<name>.py` (copy [`population.py`](fields/population.py)), with examples of the source row.
2. List the module in `MODULES` in [`fields/__init__.py`](fields/__init__.py); its place there is its column position.
3. Add the module to the crawler's `field_names(...)`, and request the source column if the download
   does not include it yet (for `census-dhc` and `census-acs5`, add the variable to `REQUESTS`; a test
   fails if a Field reads a variable that is not requested).

**A group of columns** (one distribution): the same, with one module whose `FIELDS` is built by
`field_group`, one Field per bucket (copy [`population_by_age.py`](fields/population_by_age.py)).

**From a new source:**

1. Add `crawlers/<name>.py` (copy [`census_dhc.py`](crawlers/census_dhc.py)): downloads, `parse()`, `CRAWLER`.
2. List it in `MODULES` in [`crawlers/__init__.py`](crawlers/__init__.py).
3. Run `mise run pipeline-check` and add the task block it prints to `mise.toml`.
4. Add a parser test with a few real rows (see [`test_db_crawlers.py`](../tests/test_db_crawlers.py)).

Forgetting a step fails `mise run pipeline-check` or the tests (L1, K1, K3, M1 or D2).

## Decisions

Taken as defaults while the maintainer reviews; the maintainer's branch has the final word.

| # | Question | Decision | Status |
|---|---|---|---|
| 1 | Does `crawler-<name>` download again? | No: it reuses the cache and parses again; `-- --refresh` downloads again, at most once per 24 h | done |
| 2 | How are distributions stored? | One Field per number, generated by `field_group` in one module | done: the 21 distributions of the research, 256 columns |
| 3 | How is history stored? | The main table holds the latest year; history goes to a separate long table `(zipcode, field, year, value)`. 256 numbers over 14 years would be 3,584 columns, and SQLite allows 2,000 | not built; comes with the first history crawler. F7 guards the limit |
| 4 | Where does the full database go? | A GitHub release asset, as in 2.x; git has only the demo | not published; waits for the Fields |
| 5 | Are city, state and ZIP type Fields? | Yes, claimed by `zip-basics`, which falls back HUD, ZBP, 2.x | done |
| 6 | Which Python? | 3.11+ for `data_pipeline/` only; `mise.toml` pins 3.12 and `pipeline-setup` installs pytest | done |
| 7 | CI? | A separate workflow, [`data_pipeline.yml`](../../.github/workflows/data_pipeline.yml), runs these tests on the `dev-jcw591*` branches; the existing workflow is unchanged | done |
| 8 | Island areas? | NULL for now. To add them later, `census-dhc` gets 4 more downloads (a Field has one crawler, so not a new crawler); the 4 island APIs list a ZCTA level, not tried yet | done (NULL) |

## Open questions for the maintainer

1. **"The whole code base."** Here the split is inside `data_pipeline/database/`, and `uszipcode/` is
   untouched. `zipcode_universe/` still has its own download code, because it builds the PK list rather than
   columns. Should it move onto `fetch.py`, and should the crawlers live inside the `uszipcode` package?
2. **`major_city` case.** It is upper case as HUD and ZBP write it; 2.x stored title case.
3. **`zipcode_type` source.** It comes only from 2.x, because no free government source has it, so new ZIPs have
   no type. Infer it from the HUD address flags instead?
4. **Census key.** `census-dhc` requires a key (free). Allow keyless calls instead (limited per IP per day)?
5. **One county per ZIP.** About 29% of ZIPs span more than one county; `county` keeps the one with most
   residential addresses. Should all of them be kept, in a separate ZIP-county table?
