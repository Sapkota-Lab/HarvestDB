-- View the normalized records with their field and harvest context.
SELECT
	fields.name AS field_name,
	harvest_events.harvest_date,
	harvest_events.harvest_number,
	harvest_records.id AS record_id,
	harvest_records.plot_number,
	harvest_records.dynamic_data
FROM harvest_records
JOIN harvest_events ON harvest_events.id = harvest_records.harvest_event_id
JOIN fields ON fields.id = harvest_events.field_id
ORDER BY harvest_events.harvest_date DESC, harvest_records.id;

-- Print every JSON property without hard-coding column names.
SELECT
	harvest_records.id AS record_id,
	fields.name AS field_name,
	harvest_records.plot_number,
	json_property.key AS json_key,
	json_property.value AS json_value
FROM harvest_records
JOIN harvest_events ON harvest_events.id = harvest_records.harvest_event_id
JOIN fields ON fields.id = harvest_events.field_id
CROSS JOIN LATERAL jsonb_each(harvest_records.dynamic_data) AS json_property
ORDER BY harvest_records.id, json_property.key;

-- Print JSON values as text, which is convenient for reports.
SELECT
	harvest_records.id AS record_id,
	fields.name AS field_name,
	harvest_records.plot_number,
	json_property.key AS json_key,
	json_property.value AS json_value
FROM harvest_records
JOIN harvest_events ON harvest_events.id = harvest_records.harvest_event_id
JOIN fields ON fields.id = harvest_events.field_id
CROSS JOIN LATERAL jsonb_each_text(harvest_records.dynamic_data) AS json_property
ORDER BY harvest_records.id, json_property.key;

-- List every distinct JSON property currently used in the table.
SELECT DISTINCT json_property.key AS json_key
FROM harvest_records
CROSS JOIN LATERAL jsonb_object_keys(harvest_records.dynamic_data) AS json_property(key)
ORDER BY json_key;
