# Import the cleaned 2026 harvest workbook

Run these commands from `backend/` after installing `requirements.txt`.

Inspect the workbook without connecting to a database:

```bash
python -m app.scripts.import_cleaned_harvest "/path/to/Harvest 2026 Sapkota lab CLEANED.xlsx"
```

To write to the local testing database, start it and create the existing tables first.
`TEST_DB_SETUP.sh` resets test data, so do not rerun it on a database whose records you want to keep.
Then run:

```bash
python -m app.scripts.import_cleaned_harvest "/path/to/Harvest 2026 Sapkota lab CLEANED.xlsx" \
  --apply \
  --database-url "postgresql+psycopg://myuser:testing_password@localhost:5432/testing_db"
```

There is no default write target. `--apply` and an explicit PostgreSQL URL are required.
The importer uses one transaction. A failure rolls back all new fields, events, and records.
It does not create tables or modify the workbook.

## Mapping

- Location maps to a field: High Tunnel, South Farm, or Robinson.
- Each distinct location, row's harvest date, and harvest number maps to a harvest event.
  A sheet containing two dates creates two events. The sheet name and index date do not override row dates.
- SN maps to `plot_number`, as agreed for the testing phase. It is also retained as `serial_number`.
  SN is sequential within a sheet and is not a physical plot identifier. Repeated SNs across sheets stay separate.
- Genotypes, measurements, experiment, replicate, notes, original genotype text, and entered-by values map
  to named keys in `dynamic_data`. Explicit units remain in keys such as `total_weight_g` and `total_weight_kg`.
  The importer does not assign units to source columns that lack them.
- Empty cells remain `null`, zero stays zero, and text `N/A` is preserved. Missing genotypes are reported.
- `_source` in `dynamic_data` retains the dataset, workbook filename, worksheet, Excel row,
  original column names, formula text, and date-assignment reasoning from `_Sheet_Index`.

The supplied workbook contains 601 dated rows: 214 High Tunnel, 304 South Farm, and 83 Robinson,
grouped into 14 harvest events. One South Farm row has genotype `N/A`; its description and measurements
are retained. The 38 undated `SF_Hybrid` rows are excluded, along with metadata, cleaning history, and lab assays.
These sheets remain available in the original workbook for separate future imports.

Some dates were inferred by the earlier cleaning project. They are imported as supplied,
with the original reasoning retained rather than presented as newly verified dates.
The South Farm second-harvest sheet has 64 formula cells without cached results. Their values remain
`null` and their formulas are retained under `_source.formulas`; no values are invented or recalculated.
Its recorded weights and counts are still imported.

## Running again

Rows are identified by dataset, sheet, and Excel row, not by SN alone or by file hash.
An unchanged repeat import skips all 601 records. Renaming the file does not create duplicates.
A changed source row or a manually edited imported record stops the import for review instead of overwriting it.
Do not rearrange or rename sheets or reorder rows and treat that as an unchanged import.
Concurrent runs of this importer are serialized with a PostgreSQL transaction advisory lock.
Existing manual records without this import provenance are left untouched and are not deduplicated against the workbook.

Future collection sheets should provide a real plot identifier, location, harvest date, and harvest number.
Genotype and replicate should also be recorded so measurements can be linked to the field design.

## Tests

```bash
python -m pytest tests/test_workbook_import.py -q
```

The tests use an isolated SQLite database for parsing, transaction, and repeat-import checks.
Set `HARVEST_TEST_WORKBOOK` to the source file's path to include the full 601-row check.
PostgreSQL's advisory lock must be verified separately on a PostgreSQL target.

The supplied workbook was also imported into the local PostgreSQL `testing_db`.
All 601 stored rows were compared with the source, including measurements, dates, and provenance.
A second run created no records and skipped all 601. The existing field, three harvest events,
and three test records were retained, leaving 604 records total.
This database is local; coworkers need to run the importer against their own testing database.
