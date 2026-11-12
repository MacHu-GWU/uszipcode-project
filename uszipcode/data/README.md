# uszipcode 3.0 data pipeline: the crawler registry

Builds the 3.0 database from the outputs of named crawlers. Rows are PKs (ZIP codes), columns are
`zipcode` plus one column per Field, and NULL simply means "no value" (a PO box ZIP has no population).

This package, `uszipcode/data/`, holds all the crawler and data-cleaning code. It is on its own: it imports
nothing from the rest of `uszipcode`, and the rest of `uszipcode` imports nothing from it. Its tests are in
[`tests/data/`](../../tests/data). What it downloads and writes goes to
[`data_pipeline/`](../../data_pipeline/README.md) at the repository root, so none of that is installed
with the package.

## Layout

The functionality, the crawlers and the Fields are kept apart, so that new columns only add small
files and never touch the functionality. [`test_db_structure.py`](../../tests/data/test_db_structure.py) fails
if a module crosses these lines.

| Where | What | Rule |
|---|---|---|
| `uszipcode/data/*.py` | **the functionality**: [`core`](core.py), [`checks`](checks.py), [`fetch`](fetch.py), [`crawl`](crawl.py), [`build`](build.py), [`cli`](cli.py) | knows no data source and no column; only `fetch.py` opens a URL |
| [`crawlers/`](crawlers) | **one module per data source**; [`__init__.py`](crawlers/__init__.py) holds `CRAWLERS`, the registry | downloads and parses; claims Fields by their modules; cannot open a URL and never reads a value |
| [`fields/`](fields) | **one module per Field or per group of Fields**; [`__init__.py`](fields/__init__.py) holds `FIELDS`, the catalog | says what the column is and how to read it from a source row; imports only `core` |
| [`fields/history/`](fields/history) | the same for the history Fields; [`__init__.py`](fields/history/__init__.py) holds `HISTORY_FIELDS` | the same rules |
| [`__main__.py`](__main__.py) | joins the three | the only place that does |
| [`keys.py`](keys.py), [`zipcodes.py`](zipcodes.py) | the two API keys, each defined once, and the form of a ZIP | what the crawlers and `zipcode_universe` share |
| [`zipcode_universe/`](zipcode_universe/README.md) | builds the list of PKs; its files are downloaded by `fetch.py` too | the functionality does not import it |

| Concept | Rule |
|---|---|
| **PK** | a 5-digit ZIP as text with leading zeros |
| **PK set** | the rows of one build: `demo` (3 ZIPs), `full` (every ZIP of [`zipcode_universe`](zipcode_universe/README.md)) or a CSV file with a `zipcode` column |
| **Field** | one column: name, dtype (`int`/`float`/`str`), description, unit, `extract` and `examples`. The catalog's order is the column order |
| **Source row** | one row of a data source under its own column names, e.g. `{"P1_001N": "32612"}` |
| **Crawler** | a name, the Fields it claims, the files it downloads and a pure `parse()` that yields `(zipcode, source row)`. Every Field is claimed by exactly one crawler |
| **Derived Field** | a Field with `inputs`: other Fields earlier in the catalog. No crawler claims it; `build` computes it after the join (e.g. `population_density`) |
| **History Field** | a Field of the second catalog, `HISTORY_FIELDS`, claimed by a history crawler (`history=True`). A history crawler has one row per ZIP and year, and adds a `year` column to its source rows. In the database a history Field `x` is one column, `x_by_year`: the values of the ZIP by year, as JSON |
| **Compressed Field** | a `str` Field with `compressed=True` (the boundary): text in the crawler output, a zlib BLOB in the database |
| **Simple Field** | a Field with `simple=True`: also a column of the simple release, the small database with a part of the columns |

`crawl` runs one crawler: fetch (the only network step, cached), parse (offline), each claimed Field
reads its value from the source rows, check the output contract, write. `build` left-joins every crawler
output onto the PK set, computes the derived Fields, and folds the rows of the history crawlers into one
JSON value per ZIP and history Field. From the same rows it also writes the simple release. It never
downloads anything, so switching PK sets is free.

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
([`crawlers/zcta_geometry.py`](crawlers/zcta_geometry.py)):

```python
fields=field_names(bounds, polygon),
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
| `mise run pipeline-build -- --pk-set full` | builds it for all 42,730 ZIPs (or `--pk-set path/to/pks.csv`; the file may not be named `demo.csv` or `full.csv`) |
| `mise run pipeline-test` | runs the offline tests (no network) |

Without mise, run the same commands with `python -m uszipcode.data check | crawl NAME | crawl --all | build`
from the repository root. Exit codes: 0 success, 2 registry / contract / PK-set problems, 1 download
and file problems. Expected errors print one message without a traceback.

Five crawlers need a free key, so `crawl-all` needs both keys:

- the four Census API crawlers (`census-dhc`, `census-acs5`, `census-acs5-history`, `census-decennial`) share
  one key (<https://api.census.gov/data/key_signup.html>), read from `$CENSUS_API_KEY` or `~/.census_key`;
- `zip-basics` needs a HUD token (<https://www.huduser.gov/hudapi/public/register>), read from
  `$HUD_API_TOKEN` or `~/.hud_token`.

A key is added to the request in memory only: it is never written to the cache, the manifest, the outputs
or an error message.

When the requirements of the library itself are not installed, every command first prints a line such as
`No module named 'sqlalchemy'`. It comes from `uszipcode/__init__.py`, which reports that the search engine
cannot be imported. The pipeline does not need the search engine and runs as usual.

Files (all in `data_pipeline/` at the repository root, outside the package):

- `data_pipeline/.cache/crawlers/<name>/`: raw downloads and `manifest.json` (url, bytes, sha256, time); ignored by git
- `data_pipeline/output/crawlers/<name>.csv` and `.json`: one row per ZIP (or ZIP and year) in the source; ignored by git
- `data_pipeline/output/db_<set>.sqlite`: the database; ignored by git
- `data_pipeline/output/db_<set>_simple.sqlite`: the simple release, a part of its columns; ignored by git
- `data_pipeline/output/db_<set>_coverage.json`: what each Field and crawler covers; the demo one is committed
- `data_pipeline/output/db_<set>.csv`: the same table as text, for reading and reviewing. It is written only
  for a PK set of at most 1,000 rows, so not for `full`; the demo one is committed

## The database

`db_<set>.sqlite` has one table, `zipcode_data`, with one row per ZIP:

| Columns | Stored as |
|---|---|
| `zipcode` | TEXT, the primary key |
| one per Field, in catalog order | INTEGER, REAL or TEXT; NULL means "no value" |
| `polygon` (a compressed Field) | BLOB: `zlib.compress` of the UTF-8 GeoJSON text. This is what `CompressedJSONType` of `sqlalchemy_mate` reads, the type of `polygon` in 2.x |
| one per history Field, `<field>_by_year` | TEXT: a JSON object of the values by year, `{"2011":13642,"2012":14304}`, years ascending. A year without a value is left out; a ZIP without any value has NULL |

```python
import json, sqlite3, zlib

con = sqlite3.connect("data_pipeline/output/db_demo.sqlite")
by_year, polygon = con.execute(
    "SELECT acs_population_by_year, polygon FROM zipcode_data WHERE zipcode = '20037'").fetchone()
json.loads(by_year)["2024"]                   # 13156
json.loads(zlib.decompress(polygon))["type"]  # 'MultiPolygon'
```

The history columns are plain JSON text, so SQLite can read them too:
`SELECT json_extract(acs_population_by_year, '$.2024') FROM zipcode_data`.

### The simple release

`db_<set>_simple.sqlite` is the small database: the same table `zipcode_data` with the same rows and a
part of the columns, `zipcode` and the Fields marked `simple=True`. `build` writes it from the rows it
has just written to `db_<set>.sqlite`, so the two files cannot differ, and a column is added to it by
adding `simple=True` to its Field. It has no history columns.

The 20 simple Fields are the columns of the 2.x `simple_zipcode` table that are Fields today (a test
compares the two lists):

`zipcode_type`, `major_city`, `state`, `county`, `lat`, `lng`, `timezone`, `land_area_in_sqmi`,
`water_area_in_sqmi`, `bounds_west`, `bounds_east`, `bounds_north`, `bounds_south`, `radius_in_miles`,
`population`, `population_density`, `housing_units`, `occupied_housing_units`, `median_home_value`,
`median_household_income`.

The 2.x table had three more columns, which are not Fields: `post_office_city`, `common_city_list` and
`area_code_list`.

## Crawlers and Fields

| Crawler | Source | Download | Fields |
|---|---|---|---|
| `zip-basics` | [HUD-USPS crosswalk](https://www.huduser.gov/portal/datasets/usps_crosswalk.html), Census [2025 Gazetteer](https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/) (ZCTA file and counties file), Census ZBP, uszipcode 2.x, BTS [NTAD Time Zones](https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/NTAD_Time_Zones/FeatureServer/0) | 6 files, 30 MB, token for HUD | `zipcode_type` (2.x only), `major_city`, `state` (HUD, else ZBP, else 2.x), `county` (HUD's main county with the Gazetteer name, else 2.x), `county_fips` (HUD), `county_list` (every county of the ZIP, as JSON), `lat`, `lng` (ZCTA internal point), `land_area_in_sqmi`, `water_area_in_sqmi`, `timezone` (the BTS zone at the ZCTA internal point, else at the internal point of the main county, else the zone of the state) |
| `zcta-geometry` | Census [TIGER/Line 2025 ZCTA](https://www2.census.gov/geo/tiger/TIGER2025/ZCTA520/) (full-resolution boundaries), Census [cartographic boundary file 2020 ZCTA, 1:500,000](https://www2.census.gov/geo/tiger/GENZ2020/shp/) | 2 files, 596 MB, no key | `bounds_west`, `bounds_east`, `bounds_north`, `bounds_south` (the box of each TIGER/Line record), `polygon` (GeoJSON of the generalized boundary; the last column) |
| `census-dhc` | 2020 Census DHC through the [Census Data API](https://api.census.gov/data/2020/dec/dhc.html) | 4 requests (at most 50 variables each), 31 MB, key | `population`, `housing_units`, `occupied_housing_units` and 10 distributions, 128 columns: `population_by_gender_*` (2), `population_by_age_*` (36), `children_by_age_*` (42), `population_by_race_*` (7), `families_vs_singles_*` (5), `households_with_kids_*` (2), `head_of_household_by_age_*` (16), `housing_type_*` (7, group quarters), `housing_occupancy_*` (4), `vacancy_reason_*` (7) |
| `census-acs5` | [ACS 5-year](https://api.census.gov/data/2024/acs/acs5.html), latest vintage (`YEAR = 2024`: 2020-2024, dollars of 2024) | 6 requests (at most 50 variables each), 36 MB, key | `median_age`, `median_home_value`, `median_household_income`, `median_rent`, each with its `_moe` (90% margin of error), `poverty_rate`, and 11 distributions, 128 columns: `owner_occupied_home_values_*` (11), `year_housing_was_built_*` (10), `rental_properties_by_number_of_rooms_*` (4), `monthly_rent_including_utilities_*` (28), `household_income_*` (7), `annual_individual_earnings_*` (40), `employment_status_*` (3), `means_of_transportation_to_work_*` (6), `travel_time_to_work_in_minutes_*` (8), `educational_attainment_*` (8), `school_enrollment_age_3_to_17_*` (3) |
| `irs-soi` | IRS [SOI ZIP Code Data](https://www.irs.gov/statistics/soi-tax-stats-individual-income-tax-statistics-zip-code-data-soi), latest tax year (`YEAR = 2023`) | 1 file, 40 MB, no key | for 11 income sources, the share of tax returns with it and the average amount among them (22 columns): `sources_of_household_income_*` (wages, business, partnership and S corporation, unemployment), `household_investment_income_*` (interest, ordinary and qualified dividends, capital gains), `household_retirement_income_*` (IRA distributions, pensions and annuities, Social Security) |
| derived | computed by `build` | none | `population_density` = `population` / `land_area_in_sqmi` (NULL where the land area is 0); `radius_in_miles` = half the diagonal of the `bounds_*` box |

History Fields (the columns `<field>_by_year`):

| Crawler | Source | Download | History Fields |
|---|---|---|---|
| `census-acs5-history` | ACS 5-year, every vintage 2011-2024 (the API has no ZCTA data in earlier 5-year files) | 14 requests, 33 MB, key | `acs_population`, `median_household_income`, `median_home_value`, `median_rent`, each with its `_moe` |
| `census-decennial` | Census 2000 and 2010 (Summary File 1, `P001001`) and 2020 (DHC, `P1_001N`) | 3 requests, 2 MB, key | `census_population` |
| `irs-soi-history` | IRS SOI ZIP Code Data, every tax year 2011-2023 (the IRS has no file of this form before 2011); the latest file is also the download of `irs-soi` | 13 files, 379 MB, no key | `tax_returns` (`N1`), `people_on_tax_returns` (`N2`), `average_income_per_return` (`A00100` x 1,000 / `N1`) |

Comparing years needs care. The year of an ACS value is the last year of its 5-year window, so
neighbouring years share four years of data, and dollars are of that year (not adjusted for inflation).
ZCTA boundaries change: ACS years up to 2020 use the 2010 ZCTAs, later years the 2020 ZCTAs, and each census
uses its own. A code can therefore stand for a different area in different years.

The year of an IRS value is the tax year. `tax_returns` counts returns: a couple filing jointly is one.
`people_on_tax_returns` is the number of taxpayers and dependents on them, which the IRS calls exemptions up
to 2017 and individuals from 2018; it is lower than the population, because not everybody files a return.
`average_income_per_return` is the adjusted gross income of all returns divided by their number, in dollars
of that year: an average, which a few very large incomes move far more than a median (20037 has $170,357
for 2022 and $290,902 for 2023). uszipcode 2.x had the second and the third under the names
`population_by_year` and `average_household_income_over_time`.

The Census values are ZCTA values: a ZIP without a ZCTA (PO box, unique, military) gets NULL. The IRS
values are by the ZIP taxpayers write on their returns; they cover returns, not households, and only taxable
amounts; ZIPs with fewer than 100 returns are pooled by the IRS and get NULL. The ACS
writes "not available" as negative codes (for example -666666666); they are read as NULL. The
distribution buckets are those of the research (issue #88), which were checked against reference values;
the modules were generated from its bucket definitions and the values below match it exactly. Where a
2.x name plus a bucket would pass 60 characters, the module has a shorter name and says which 2.x field
it stands for (`means_of_transportation_to_work`, `educational_attainment`).

The geometry is that of the 2020 ZCTAs, so a ZIP without a ZCTA has none.
`bounds_*` is the box of the full-resolution boundary, water included. `radius_in_miles` is half the
diagonal of that box (half the great-circle distance between its south-west and north-east corners): the
radius of the circle around the middle of the box that reaches its corners, so the whole ZCTA lies inside
that circle. A ZCTA with far-apart parts has a large one: 99503 in Anchorage has 141 miles, because its box
reaches 8 degrees to the west. `polygon` is GeoJSON text (longitude
first, 6 decimals) of the boundary as the Census Bureau generalized it for 1:500,000 maps; nothing is
simplified here. It is the last column, because it is by far the longest (up to 177,237 characters, for
99615). `timezone` is the standard-time zone of BTS (`Eastern`, `Central`, `Mountain`, `Pacific`, `Alaska`,
`Hawaii-Aleutian`, `Atlantic`, `Chamorro`, `Samoa`): it does not say whether a place observes daylight
saving time (Arizona is `Mountain`), and the research found 493 ZCTAs whose boundary touches a second zone.

About 29% of the ZIPs that HUD lists span more than one county. `county` and `county_fips` are the main
county: the one with the largest share of the ZIP's residential addresses, then of all its addresses, then
the lowest code. `county_list` has all of them, the main county first, as a JSON array:

```json
[{"county_fips":"47125","county":"Montgomery County","state":"TN","res_ratio":0.9108674928503336,"bus_ratio":0.5823353293413174,"oth_ratio":0.6936026936026936,"tot_ratio":0.8935663224781573},
 {"county_fips":"21047","county":"Christian County","state":"KY","res_ratio":0.08913250714966635,"bus_ratio":0.4176646706586826,"oth_ratio":0.3063973063973064,"tot_ratio":0.10643367752184273}]
```

This is 42223 (Fort Campbell), one of 4 ZIPs whose counties are in two states. `county` and `state` are the
name and state of the county in the Census Gazetteer; they are `null` for the 20 entries in Guam, the U.S.
Virgin Islands and the Northern Mariana Islands, which that file does not list. The four ratios are HUD's
shares of the ZIP's residential, business, other and all addresses in the county, untouched. A record with an
incomplete county code (9 of 54,570) is left out, as in `county_fips`. SQLite reads the column with
`json_each`: `SELECT z.zipcode FROM zipcode_data z, json_each(z.county_list) c WHERE json_extract(c.value, '$.county_fips') = '21047'`.

A zone needs a point, and the best point a ZIP has decides its `timezone`:

1. the internal point of its ZCTA (`lat`, `lng`);
2. without a ZCTA (PO box, unique and other ZIPs): the internal point of its main county, which is the HUD
   county, else the county that 2.x names;
3. without a county: its state, when the internal points of all counties of the state lie in one zone.

Steps 2 and 3 can be wrong where a county spans two zones. The ZCTA point, the county point and the county
of a ZIP are in three files, and one file belongs to one crawler (C8). This is why `zip-basics` reads the
Gazetteer ZCTA file and the time zones too, and why there is no crawler for the Gazetteer alone.
The shapefiles are read by a small reader in [`crawlers/zcta_geometry.py`](crawlers/zcta_geometry.py), with
the standard library only.

## Politeness

Enforced in [`fetch.py`](fetch.py), the only module that opens a URL; crawlers cannot change it, and
`zipcode_universe` downloads through it as well.

- A crawler declares whole files (1 to 100 per crawler), never one request per ZIP.
- A cached file is reused: no request, and the key is not even read. A crawler downloads once.
- Downloads run one at a time, 2 s apart (also from one crawler to the next in `crawl-all`), with a
  User-Agent that names this project.
- Retries only on connection errors, timeouts, 429 and 5xx: 5 attempts, waits of 5, 15, 45 and 90 s
  (`Retry-After` is honoured up to 300 s). Any other 4xx fails at once.
- A connection that drops in the middle of a file is resumed: the next request asks only for the missing
  bytes (HTTP `Range`, with `If-Range`, so a file that changed meanwhile comes whole again). An attempt that
  brought new bytes does not count as a failure; at most 30 requests per file.
- A body shorter than its `Content-Length` is treated as a dropped connection and resumed, so a file
  cut short by a connection that closed without an error is never cached.
- A bearer token (HUD) is sent only to the host of the declared URL: when the server redirects to
  another host, the request goes on without it.
- The body must start with the declared magic bytes (`PK\x03\x04` for a zip, `[[` for the Census API),
  so an HTML error page is never cached. A failed download keeps the previous file.
- `--refresh` is refused if the crawler downloaded less than 24 h ago (`--force` overrides). There is
  no loop, schedule or watch mode.

## Checks

`check`, `crawl` and `build` first run every registry check and report all problems at once, each
with how to fix it:

| IDs | Checks |
|---|---|
| F1-F10 | Field names are snake_case, `zipcode` (and `year` for a history Field) is reserved, no duplicates, dtype is `int`/`float`/`str`, a description is given, an `extract` is given, the database fits SQLite's 2,000 columns (F7); only a `str` Field of `FIELDS` is compressed (F8); no history column `<field>_by_year` has the name of a Field (F9); no history Field is marked `simple` (F10) |
| C1-C8 | crawler names are kebab-case and unique; a crawler claims Fields and declares 1 to 100 downloads; filenames are safe and unique; URLs are `https://` and hold no key; a Secret is well formed; no URL is downloaded by two crawlers, except that a history crawler may download a file of one other crawler too (it cannot claim Fields of the main table, so `irs-soi` and `irs-soi-history` both read the latest IRS file) |
| K1-K5 | every claim names a Field of the catalog (with "did you mean"; history crawlers claim from `HISTORY_FIELDS`), no Field is claimed twice, **no Field is left unclaimed** unless it is derived; a derived Field is claimed by no crawler (K4) and derives only from Fields before it in `FIELDS` (K5) |
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
| D7 | a history source row has a `year` (and a ZIP appears once per year) |

Keys that are not ZIPs (`00000`, text, the `HH`/`XX` codes of the 2000 census) are skipped and counted.
On any error nothing is written and the previous output stays. `build` also checks that each crawler
output exists (B1), matches the crawler's current claims and was made from the downloads the crawler
declares now (B2; a new `YEAR` in a crawler changes its URLs) and holds valid rows (B3), and says
which `mise run crawler-<name>` to run if not. Every derived value passes the same type rules (B4).

## Result (run of 2026-11-09)

`mise run crawl-all` makes 49 requests the first time (about 1.15 GB; the TIGER/Line file alone is 529 MB
and took 10 minutes here, the 13 IRS history files 8 minutes) and 0 after that. A run from a fresh clone on
2026-11-10, before the IRS history (36 requests then), took 44 minutes in all and made 39 requests, because `zcta-geometry` needed 6 requests for the 3 files it had then (connections that
failed and were retried); every crawler output and the
demo and full databases came out byte-identical to the earlier run. The Census API does not always
return its rows in the same order, so the `sha256` of a few cached files (and with it
`db_demo_coverage.json`) changes from one download to the next, while the outputs do not.
`mise run pipeline-build` then writes
[`db_demo.csv`](../../data_pipeline/output/db_demo.csv): 3 rows x 321 columns (`zipcode`, 308 Fields, 12 history columns). Its first columns (the `county_list` cell is cut short here):

```
zipcode,zipcode_type,major_city,state,county,county_fips,county_list,lat,lng,timezone,land_area_in_sqmi,water_area_in_sqmi,bounds_west,bounds_east,bounds_north,bounds_south,radius_in_miles,population,...
10001,STANDARD,NEW YORK,NY,New York County,36061,"[{...}]",40.750649,-73.997298,Eastern,0.624,0.0,-74.010148,-73.984076,40.759686,40.743451,0.8832534157578589,32612,...
20013,PO BOX,WASHINGTON,DC,District of Columbia,11001,"[{...}]",,,Eastern,,,,,,,,,...
20037,STANDARD,WASHINGTON,DC,District of Columbia,11001,"[{...}]",38.892459,-77.053811,Eastern,0.732,0.231,-77.064696,-77.04624,38.910414,38.87131,1.4391841683262467,14945,...
```

20013 is a Washington, DC PO box ZIP: it has a type, a city, a state, a county (name, code and list) and the
time zone of that county, but no ZCTA and no IRS row, so its other 313 columns are NULL, the 12 history columns included. This is
expected, not an error. [`db_demo_coverage.json`](../../data_pipeline/output/db_demo_coverage.json)
counts it under `not_in_source` for the Fields of a crawler that does not list it, and under `empty_in_source`
for `lat`, `lng` and the two areas, because `zip-basics` lists it without a point. For 20037 the 2020-2024 ACS gives a median age of 30.4,
a median home value of $685,300, a median household income of $111,153 and a median rent of $2,538; in tax
year 2023, 81.2% of its returns had wages, averaging $128,954. Its population density is 20,417 people per
square mile, and its radius 1.44 miles (its box is 2.70 miles from north to south and 0.99 from east to west). The history columns of 10001 and 20037 hold 16 years (2000, 2010, 2011-2024): for 20037,
`census_population_by_year` is `{"2000":12642,"2010":14642,"2020":14945}`, and `tax_returns_by_year` starts
`{"2011":5316,"2012":4970,` and ends `"2023":5540}`.

With `--pk-set full` (42,730 ZIPs, no downloads; about 12 seconds; `db_full.sqlite` is 167 MB, of which
45 MB are the compressed boundaries, 138 MB as text, and 8 MB the county lists; `db_full_simple.sqlite` is 6.9 MB, 42,730 rows x 21
columns, each identical to the same column of `db_full.sqlite`):

| Fields | ZIPs with a value |
|---|---|
| `major_city`, `state` | 42,730 |
| `zipcode_type` | 42,724 (the 6 ZIPs newer than 2.x have none) |
| `county` | 41,866 |
| `county_fips`, `county_list` | 39,475 (HUD only); the lists hold 54,561 counties: 28,096 ZIPs have one, 8,298 two, 2,520 three, 561 four to seven |
| `timezone` | 41,905: 33,791 from the ZCTA point, 5,752 from the HUD county, 592 from the county 2.x names, 1,770 from the state |
| `lat`, `lng`, `land_area_in_sqmi`, `water_area_in_sqmi`, the 4 `bounds_*`, `radius_in_miles`, `polygon` | 33,791 |
| `population`, `population_density`, the housing counts and the 128 DHC distribution columns | 33,774 |
| the 128 ACS distribution columns | 33,772 |
| `poverty_rate`, `median_age`, `median_household_income`, `median_home_value`, `median_rent` | 32,878, 32,820, 30,547, 30,260, 25,751 |
| the 22 IRS income-source columns | 27,689 |

The 12 history columns hold 4,607,813 values for 34,241 PKs: `acs_population_by_year` has 466,292
(2011-2024, 33,971 PKs), `median_rent_by_year` 379,157, and `census_population_by_year` 98,748 (2000, 2010,
2020; 184 ZCTAs of the old censuses are not in the PK list). Each of the three IRS columns has 361,760
(2011-2023, 30,197 PKs, of which 27,330 have all 13 years and 2,251 only one; 2,205 are PO box ZIPs, which
have no Census values).

When the history moved into the main table and `polygon` was compressed, the new full database was compared
with the one before (tables `zipcode_data` and `zipcode_history`, `polygon` as text): the 306 other columns
of all 42,730 rows are identical, every boundary decompresses to the same text, and the JSON columns hold
exactly the 3,522,533 values of the 532,117 rows of the old history table.

Checked against earlier work:

- `major_city`, `state` and `zipcode_type` match `zipcode_universe.csv` row by row.
- The 4,323,072 DHC distribution values (33,774 ZCTAs x 128 columns), `water_area_in_sqmi` and
  `occupied_housing_units` match the research database exactly.
- `census-acs5` was also run once for the 2019-2023 vintage, the one the research used: its 4,322,816
  distribution values (33,772 ZCTAs x 128 columns) and the 9 median, margin and poverty columns match the
  research database exactly. The committed outputs use 2020-2024.
- `irs-soi` was also run on the tax year 2022 file the research used: its 303,468 shares and 303,468
  averages (27,588 ZIPs x 11 sources) match the research database exactly. The committed outputs use 2023.
- `population_density` matches the research database for all 39,558 of its ZIPs, NULLs included.
- `radius_in_miles` against 2.x, which did not document its column and stored whole miles (below one mile,
  multiples of 300 feet): 32,907 ZIPs have a value in both, and for 26,281 of them (80%) the new value is
  within one mile or 25% of the 2.x value; the middle 80% of the ratios 2.x / new lie between 0.70 and 1.40
  (median 1.02). The radius of a circle with the area of the ZCTA, the other definition tried, is that
  close for 19%. 2.x values such as 13 miles for 23884 (a box of 1.5 miles) cannot be reproduced.
- The history crawlers match the research history tables: 466,292 ACS rows (3,730,336 values) exactly, and
  98,932 census rows exactly; the research also kept 1,140 census rows whose codes are not ZIPs (`006HH`,
  `006XX`: water and unassigned areas of the 2000 census), which the crawler skips.
- The 4 `bounds_*` and `timezone` match the research database exactly for all 33,791 ZCTAs
  (the research read the same TIGER/Line and BTS files with shapely). The TIGER/Line internal point equals
  `lat`/`lng` of the Gazetteer to its 6 decimals for every ZCTA, and `timezone` is the zone at `lat`/`lng`. Every
  internal point lies inside its box. The research simplified the full boundaries itself (about 30 m);
  `polygon` uses the Census generalized file instead: 5,954,485 points (the research had 6,097,831), every
  ring oriented as RFC 7946 asks, and an area (in degrees, converted at the ZCTA's latitude) within 0.973 to
  1.005 of the Gazetteer land + water area for 90% of ZCTAs (median 1.001). For 47 ZCTAs on coasts and islands
  (for example 02668 and 04108) the internal point falls just outside the generalized shape.
- `timezone` of the ZIPs without a ZCTA, against 2.x, which had IANA names (`America/Chicago` is `Central`
  here): when the county and state steps were added, the 33,791 zones from a ZCTA point and the 316 other
  columns stayed identical, and 8,114 ZIPs got a zone. 8,100 of them have a zone in 2.x, and 8,098 have the
  same one (the two others are in Texas and Idaho, in counties with two zones). For comparison, the zones
  from a ZCTA point agree with 2.x for 33,775 of 33,788. The 825 ZIPs still without a zone are the 787
  military ZIPs (`AE`, `AP`, `AA`), which are not in a U.S. zone, and 38 others, mostly in the island areas.
- The IRS history against the 2.x comprehensive database, which has the tax years 2005-2018: for the
  221,288 pairs of ZIP and year that both have (2011-2018), `people_on_tax_returns` equals the 2.x
  `population_by_year` in every one, and `average_income_per_return` equals the 2.x
  `average_household_income_over_time` to the dollar in every one. The 2.x name was misleading: its
  "population" is the IRS count of people on tax returns (6,320 for 20037 in 2018, where the 2020 census
  counts 14,945 people). When the three columns were added, the 318 other columns stayed identical.
- `county_list`: when it was added, the 317 other columns stayed identical. It holds every HUD record with a
  5-digit county code (54,561 of 54,570), its first element is `county_fips` and `county` for all 39,475 ZIPs,
  and `tot_ratio` adds up to 1 in every list.
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

**Computed from other columns:** a Field module with `inputs` (copy
[`population_density.py`](fields/population_density.py) or [`radius_in_miles.py`](fields/radius_in_miles.py)),
listed after its inputs in `fields/__init__.py`; no crawler claims it.

**Also in the simple release:** add `simple=True` to the Field.

**A history column:** the same steps in [`fields/history/`](fields/history), claimed by a
history crawler, whose `parse()` puts the `year` in each source row (copy
[`census_acs5_history.py`](crawlers/census_acs5_history.py)).

**From a new source:**

1. Add `crawlers/<name>.py` (copy [`census_dhc.py`](crawlers/census_dhc.py)): downloads, `parse()`, `CRAWLER`.
2. List it in `MODULES` in [`crawlers/__init__.py`](crawlers/__init__.py).
3. Run `mise run pipeline-check` and add the task block it prints to `mise.toml`.
4. Add a parser test with a few real rows (see [`test_db_crawlers.py`](../../tests/data/test_db_crawlers.py)).

Forgetting a step fails `mise run pipeline-check` or the tests (L1, K1, K3, K5, M1 or D2).

## Decisions

Taken as defaults while the maintainer reviews; the maintainer's branch has the final word.

| # | Question | Decision | Status |
|---|---|---|---|
| 1 | Does `crawler-<name>` download again? | No: it reuses the cache and parses again; `-- --refresh` downloads again, at most once per 24 h | done |
| 2 | How are distributions stored? | One Field per number, generated by `field_group` in one module | done: the 21 distributions of the research, 256 columns |
| 3 | How is history stored? | The main table holds the latest year; history goes to a separate table. 256 numbers over 14 years would be 3,584 columns, and SQLite allows 2,000 | replaced by the maintainer's decision below: the crawler outputs keep one row per (zipcode, year), and `build` folds them into one JSON column per history Field of the main table. ACS 2011-2024, the censuses 2000-2020 and the IRS tax years 2011-2023 are in it |
| 4 | Where does the full database go? | A GitHub release asset, as in 2.x; git has only the demo | not published; waits for the Fields |
| 5 | Are city, state and ZIP type Fields? | Yes, claimed by `zip-basics`, which falls back HUD, ZBP, 2.x | done |
| 6 | Which Python? | 3.11+ for `uszipcode/data/` only; `mise.toml` pins 3.12 and `pipeline-setup` installs pytest | done |
| 7 | CI? | A separate workflow, [`data_pipeline.yml`](../../.github/workflows/data_pipeline.yml), runs these tests on the `dev-jcw591*` branches; the existing workflow is unchanged | done |
| 8 | Island areas? | NULL for now. To add them later, `census-dhc` gets 4 more downloads (a Field has one crawler, so not a new crawler); the 4 island APIs list a ZCTA level, not tried yet | done (NULL) |
| 9 | `major_city` case? | Upper case, as HUD and ZBP write it (2.x stored title case). Title case is a matter of display, and is easy to get wrong (McKinney, St. Louis) | done |
| 10 | `zipcode_type` source? | The 2.x values: no free government source has the type. The 6 ZIPs newer than 2.x have none | done |
| 11 | Is a Census key required? | Yes (it is free). Keyless calls are limited per IP per day, so a crawl may not finish | done |
| 12 | Does the JSON say which ZCTA set a history value uses? | No: the set follows from the source and the year (see [Crawlers and Fields](#crawlers-and-fields)) | done |
| 13 | How detailed is `polygon`? | The Census generalization for 1:500,000 maps; nothing is simplified here | done |
| 14 | 529 MB for the four `bounds_*`? | Yes: the TIGER/Line file is downloaded once, and its box is exact (it matches the research for all 33,791 ZCTAs) | done |
| 15 | What is `radius_in_miles`? | Half the diagonal of the `bounds_*` box, a derived Field. It is the definition that comes closest to the 2.x values (see [Result](#result-run-of-2026-11-09)) | done |
| 16 | Which columns has the simple release? | The 2.x simple columns that are Fields. `county_fips` is new in 3.0 and is not in it. The table is `zipcode_data`, as in the full database (`simple_zipcode` in 2.x) | done |
| 17 | The other 2.x fields? | `common_city_list`, `area_code_list`, `source_of_earnings` and `neighborhood` have no free government source and are not Fields. `post_office_city` is not stored: in 2.x it was `major_city`, a comma and `state` in one text (for 33,013 of its 33,104 values). `nearby_zipcodes` can be computed at query time from `lat` and `lng`. `schools` is left for later | not Fields |
| 18 | Time zone of a ZIP without a ZCTA? | The zone at the internal point of its main county (HUD, else the county 2.x names), else the zone of its state when the whole state is in one zone. It is one Field of one crawler: `zip-basics` took over the Gazetteer ZCTA file and the time zones (see [Crawlers and Fields](#crawlers-and-fields)) | done: 41,905 ZIPs have a zone, 33,791 before |
| 19 | One county per ZIP? | `county` and `county_fips` keep the main county, and `county_list` has all of them as a JSON array in the same row, with HUD's address shares. It is a column and not a second table, because the product is one wide table (see [Crawlers and Fields](#crawlers-and-fields)) | done: 39,475 ZIPs, 54,561 counties |
| 20 | IRS history? | Three history Fields from the 13 yearly files, 2011-2023: `tax_returns`, `people_on_tax_returns` and `average_income_per_return`. The income sources by year are not added: they would be 22 more JSON columns | done: 361,760 values each; the last two equal 2.x in all 221,288 common values |
| 21 | Does `zipcode_universe` download by itself? | No: its five files go through `fetch.py`, like those of the crawlers (cached with a manifest, resumed, checked by their first bytes), and the HUD token is the one of `keys.py` | done: the list it builds is byte-identical to the committed one |

## Decisions of the maintainer (2026-11-10)

| Decision | Status |
|---|---|
| All crawler and data-cleaning code lives in `uszipcode/data/`. It does not depend on the rest of `uszipcode`, and its product is the SQLite database | done: the code moved here from `data_pipeline/`, and the demo and full databases came out byte-identical |
| The product is one wide table with one row per ZIP. The values of a Field over time are one JSON structure in that row. The crawler stage may keep any shape | done: `db_<set>.sqlite` has the one table `zipcode_data`; a history Field `x` is the column `x_by_year`, a JSON object `{year: value}` (see [The database](#the-database)) |
| `polygon` stays in the main table, compressed | done: a zlib BLOB, 45 MB instead of 138 MB; the full database was 150 MB instead of 227 MB |
| The `simple` release has only a part of the columns | done: a Field with `simple=True` is also a column of `db_<set>_simple.sqlite`, which `build` writes from the same rows (see [The simple release](#the-simple-release)); 20 Fields, 6.9 MB for all ZIPs |
| The pipeline gets its own group of optional dependencies, `data`, in `pyproject.toml` | not added: the repository has no `pyproject.toml` yet, and the pipeline needs only the standard library (and pytest for its tests) |

## Open questions for the maintainer

1. **The `data` dependency group.** The repository has `setup.py` and no `pyproject.toml`, and the pipeline
   needs only the standard library (and pytest for its tests). Should a `pyproject.toml` be added now, or the
   group wait for it?
2. **Two files of the library.** `--cov=uszipcode` in the library's CI now counts `uszipcode/data/`, whose
   tests are skipped on Python 3.10: 25% with it, 97% with `uszipcode/data/*` omitted in `.coveragerc`. And in
   a new environment with only `requirements.txt` installed, `import uszipcode` fails with
   `No module named 'botocore'`: `sqlalchemy_mate` 2.0.0.3 imports it and `requirements.txt` does not list
   it. This branch changes neither file. May it?
3. **The JSON structure of a history column.** It is `{year: value}`, chosen here. Another structure changes
   one function (`history_json` in `build.py`). Is this the structure you had in mind?
