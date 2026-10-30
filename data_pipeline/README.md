# uszipcode 3.0 data pipeline

Builds the 3.0 database from official U.S. sources (discussion:
[issue #88](https://github.com/MacHu-GWU/uszipcode-project/issues/88)). This folder is separate from the
installed `uszipcode` package and does not change it.

Steps (in order; each one is a sub-package run with `python -m data_pipeline.<step>` from the repository root):

| Step | Status | What it does |
|---|---|---|
| [`zipcode_universe`](zipcode_universe/README.md) | done (draft) | the primary-key list: every 5-digit ZIP from free sources, with source flags |
| [`database`](database/README.md) | in progress | the crawler registry: one Field catalog, named crawlers that each claim Fields, and the join onto a PK set (2 crawlers, 5 Fields so far) |
| more crawlers | to do | ACS, IRS, HUD, boundaries and time zones, each as a crawler of the `database` step |

The tasks of both steps are in [`mise.toml`](../mise.toml) (`mise run pipeline-check`, `mise run crawler-<name>`,
`mise run pipeline-build`; see [`database/README.md`](database/README.md)).

Tests: `python -m pytest data_pipeline/tests -q` or `mise run pipeline-test` (offline; needs pytest).
