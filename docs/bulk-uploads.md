# Bulk uploads

The upload form accepts `.csv` and `.xlsx` files. Both formats use a required `plot_number` column and an optional `dynamic_data` column containing a JSON object, such as `{"weight": 12.5, "count": 3}`. Leave `dynamic_data` blank for no measurements.

Uploads use `POST /api/v1/harvest-records/upload?harvest_event_id={harvest_event_id}`. The harvest event must already exist.

For XLSX uploads:

- Put column names in the first row of the first worksheet. Only that worksheet is imported.
- Empty rows are skipped.
- Numeric plot numbers are converted to text. To preserve leading zeros, store those cells as text in Excel.
- Replace formulas with values and fix Excel cell errors before uploading.

After uploading, the app shows the total record count, the imported tab's name and count, and the names of any tabs that were not imported. CSV uploads show the total record count.

The upload response contains `records`, `imported_sheets` (each with `name` and `record_count`), and `skipped_sheets`. Both sheet lists are empty for CSV uploads.

All rows are validated before records are saved. If a row is invalid, the upload reports its row number and saves no records from that file.
