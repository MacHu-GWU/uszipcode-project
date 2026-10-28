# uszipcode 3.0 data pipeline

Builds the 3.0 database from official U.S. sources (discussion:
[issue #88](https://github.com/MacHu-GWU/uszipcode-project/issues/88)). This folder is separate from the
installed `uszipcode` package and does not change it.

Steps (in order; each one is a sub-package run with `python -m data_pipeline.<step>` from the repository root):

| Step | Status | What it does |
|---|---|---|
| [`zipcode_universe`](zipcode_universe/README.md) | done (draft) | the primary-key list: every 5-digit ZIP from free sources, with source flags |
| statistics | to do | attach Census / ACS / IRS statistics, coordinates, boundaries and time zones to the keys |

Tests: `python -m pytest data_pipeline/tests -q` (offline, standard library only).
