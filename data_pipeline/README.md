# uszipcode 3.0 data pipeline: working folder

The code of the pipeline is in [`uszipcode/data/`](../uszipcode/data/README.md) and its tests are in
[`tests/data/`](../tests/data) (discussion: [issue #88](https://github.com/MacHu-GWU/uszipcode-project/issues/88)).
This folder holds only what the pipeline downloads and writes, so that none of it is installed with the
`uszipcode` package.

| Folder | What is in it | In git |
|---|---|---|
| `.cache/` | the raw downloads, one folder per crawler, and the downloads of `zipcode_universe` | no |
| `output/crawlers/` | one CSV and one JSON file per crawler | no |
| `output/` | `zipcode_universe.csv` (the list of PKs) and the databases `db_<set>.*` | only `zipcode_universe.*` and the demo CSV and coverage files |

The tasks are in [`mise.toml`](../mise.toml): `mise run pipeline-check`, `mise run crawler-<name>`,
`mise run pipeline-build` and `mise run pipeline-test` (see the
[README of the pipeline](../uszipcode/data/README.md)).
