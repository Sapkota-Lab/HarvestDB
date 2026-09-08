-- View all records.
SELECT *
FROM testDB
ORDER BY date DESC;

-- Print every JSON property without hard-coding column names.
SELECT
	record_id,
	field_name,
	plot_number,
	json_property.key AS json_key,
	json_property.value AS json_value
FROM testDB
CROSS JOIN LATERAL jsonb_each(dynamic_harvest_data) AS json_property
ORDER BY record_id, json_property.key;

-- Print JSON values as text, which is convenient for reports.
SELECT
	record_id,
	field_name,
	plot_number,
	json_property.key AS json_key,
	json_property.value AS json_value
FROM testDB
CROSS JOIN LATERAL jsonb_each_text(dynamic_harvest_data) AS json_property
ORDER BY record_id, json_property.key;

-- List every distinct JSON property currently used in the table.
SELECT DISTINCT json_property.key AS json_key
FROM testDB
CROSS JOIN LATERAL jsonb_object_keys(dynamic_harvest_data) AS json_property(key)
ORDER BY json_key;
