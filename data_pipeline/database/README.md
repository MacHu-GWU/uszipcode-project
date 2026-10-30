# Database step: the crawler registry

Builds the 3.0 database from the outputs of named crawlers. Rows are PKs (ZIP codes), columns are
`zipcode` plus one column per Field, and NULL simply means "no value" (a PO box ZIP has no population).

| Concept | Where | Rule |
|---|---|---|
| **PK** | | a 5-digit ZIP as text with leading zeros |
| **PK set** | `--pk-set` | the rows of one build: `demo` (3 ZIPs), `full` (every ZIP of [`zipcode_universe`](../zipcode_universe/README.md)) or a CSV file with a `zipcode` column |
| **Field** | [`fields.py`](fields.py) | one column: name, dtype (`int`/`float`/`str`), description, unit |
| **Field catalog** | `FIELDS` in `fields.py` | the only list of Fields; its order is the column order |
| **Crawler** | [`crawlers/`](crawlers) | one data source: a name, the Fields it claims, the files it downloads and a pure `parse()` |
| **Registry** | `CRAWLERS` in [`registry.py`](registry.py) | every crawler; every Field is claimed by exactly one crawler |

`crawl` runs one crawler in four steps: fetch (the only network step, cached), parse (offline), check
the output contract, write. `build` left-joins every crawler output onto the PK set; it never
downloads anything, so switching PK sets is free.

## Run

Python 3.11 or newer (the registry reads `mise.toml` with `tomllib`), standard library only; the
tests need `pytest`. The tasks are in [`mise.toml`](../../mise.toml) at the repository root and use the
`python` on your PATH. Once per clone, trust the file (mise refuses untrusted config files):

```
mise trust
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

`census-dhc` needs a free Census API key (<https://api.census.gov/data/key_signup.html>), read from
`$CENSUS_API_KEY` or `~/.census_key`. The key is added to the request in memory only: it is never
written to the cache, the manifest, the outputs or an error message.

Files:

- `data_pipeline/.cache/crawlers/<name>/`: raw downloads and `manifest.json` (url, bytes, sha256, time); ignored by git
- `data_pipeline/output/crawlers/<name>.csv` and `.json`: one row per ZIP in the source; ignored by git
- `data_pipeline/output/db_<set>.sqlite` (table `zipcode_data`), `db_<set>.csv` and `db_<set>_coverage.json`;
  only `db_demo.csv` and `db_demo_coverage.json` are committed

## Crawlers

| Crawler | Source | Download | Fields |
|---|---|---|---|
| `census-gazetteer` | Census [2025 Gazetteer, ZCTA file](https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/2025_Gaz_zcta_national.zip) | 1 file, 0.9 MB, no key | `lat`, `lng` (ZCTA internal point), `land_area_in_sqmi` |
| `census-dhc` | 2020 Census DHC through the [Census Data API](https://api.census.gov/data/2020/dec/dhc.html) | 1 request for all ZCTAs, 0.8 MB, key | `population` (P1_001N), `housing_units` (H1_001N) |

Both are ZCTA values: a ZIP without a ZCTA (PO box, unique, military) gets NULL.

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
| F1-F5 | Field names are snake_case, `zipcode` is reserved, no duplicates, dtype is `int`/`float`/`str`, a description is given |
| C1-C8 | crawler names are kebab-case and unique; a crawler claims Fields and declares 1 to 100 downloads; filenames are safe and unique; URLs are `https://` and hold no key; a Secret is well formed; no URL is downloaded by two crawlers |
| K1-K3 | every claim names a Field of the catalog (with "did you mean"), no Field is claimed twice, **no Field is left unclaimed** |
| M0-M2 | `mise.toml` is valid, every crawler has its `crawler-<name>` task (the check prints the block to add), no task points to a missing crawler |

Before anything is written, the rows from `parse()` are checked against the output contract:

| ID | Rule |
|---|---|
| D1 | no ZIP appears twice (after normalizing, e.g. `501` -> `00501`) |
| D2 | only claimed Fields |
| D3 | values match the dtype (int is not bool, a float Field accepts an int) |
| D4 | a claimed Field is not NULL in every row (the source probably changed its header) |
| D5 | at least one usable row |
| D6 | no NaN or infinity |

Keys that are not ZIPs (`00000`, text) are skipped and counted. On any error nothing is written and
the previous output stays. `build` also checks that each crawler output exists and matches the
crawler's current claims, and says which `mise run crawler-<name>` to run if not.

## Result (run of 2026-10-30)

`mise run crawl-all` makes 2 requests the first time and 0 after that. `mise run pipeline-build`
then writes [`db_demo.csv`](../output/db_demo.csv): 3 rows x 6 columns.

```
zipcode,lat,lng,land_area_in_sqmi,population,housing_units
10001,40.750649,-73.997298,0.624,32612,18926
20013,,,,,
20037,38.892459,-77.053811,0.732,14945,9689
```

20013 is a Washington, DC PO box ZIP: it has no ZCTA, so both crawlers have no row for it and every
Field is NULL. This is expected, not an error; [`db_demo_coverage.json`](../output/db_demo_coverage.json)
lists it under `pks_without_any_value`.

With `--pk-set full` (42,730 ZIPs, 3 seconds, no downloads): 33,791 ZIPs have coordinates and land
area, 33,774 have population and housing units, and 8,939 have no value. The 17 ZCTAs in the 2025
Gazetteer but not in the 2020 DHC are in the island areas (U.S. Virgin Islands 008xx, Guam, the Northern
Mariana Islands and American Samoa), which the DHC file does not cover.

The registry is not tied to these numbers: the tests build fake registries of 1 PK / 1 Field /
1 crawler, 3 / 5 / 2, 30 / 10 / 4 and 300 / 64 / 8 and run check, crawl, build and refresh on each.

## Add a crawler

1. Add its Fields to [`fields.py`](fields.py).
2. Add a module in [`crawlers/`](crawlers) with its downloads, a pure `parse()` and `CRAWLER`
   (copy [`census_dhc.py`](crawlers/census_dhc.py)).
3. Add one line to `CRAWLERS` in [`registry.py`](registry.py).
4. Run `mise run pipeline-check` and add the task block it prints to `mise.toml`.
5. Add a parser test with a few real rows (see `tests/test_db_census_crawlers.py`).

Forgetting step 1, 3 or 4 fails the check (K1, K3 or M1).

## Open questions for the maintainer

1. **What `mise run crawler-<name>` re-runs.** Here it reuses the cached download and parses again;
   `-- --refresh` downloads again (once per 24 h). Should a plain run always download instead?
2. **Field names.** The 2.x names are kept where the meaning matches (`land_area_in_sqmi`). Keep that rule?
3. **Distributions** (e.g. population by sex and 18 age bands): one flat column per number, one JSON
   column per group as in 2.x, or a separate long table?
4. **History** (ACS 2011-2024, IRS tax years): one column per year, one database per year, or a long
   table (zipcode, field, year, value)?
5. **What goes in git.** Only `db_demo.csv` and its coverage file are committed; should the full
   database be a GitHub release asset as in 2.x?
6. **City, state and ZIP type.** Should they become Fields claimed by HUD / ZBP / 2.x crawlers (with a
   fallback rule), or be copied from the `zipcode_universe` PK set?
7. **Python version.** This step needs 3.11+ (`tomllib`); `zipcode_universe` still runs on 3.6+.
   `mise.toml` does not pin a Python, because a mise-installed Python has no pytest.
8. **CI.** Add `python -m pytest data_pipeline/tests` to the workflow? Its trigger is `master`, but the
   repository has no `master` branch.
9. **Census key.** `census-dhc` requires a key (free). Allow keyless calls instead (limited per IP per day)?
10. **Island areas.** The 17 ZCTAs of the Virgin Islands, Guam, the Northern Mariana Islands and American
    Samoa have coordinates but no 2020 DHC values (the Census publishes island areas separately). Add a
    crawler for them, or leave them NULL?
