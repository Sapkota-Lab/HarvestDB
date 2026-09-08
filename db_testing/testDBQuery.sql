-- Add sample harvest data.
INSERT INTO testDB (
	field_name,
	year,
	date,
	plot_number,
	dynamic_harvest_data
)
VALUES
(
	'Test Field',
	'2023',
	'2023-01-01 09:00:00',
	1,
	'{
		"grade_1_marketable_weight": 2864,
		"grade_1_marketable_counts": 11,
		"grade_2_marketable_weight": 790,
		"grade_2_marketable_counts": 3,
		"unmarketable_weight": 0,
		"unmarketable_counts": 0
	}'
),
(
	'Test Field',
	'2023',
	'2023-01-02 09:00:00',
	2,
	'{
		"grade_1_marketable_weight": 2709,
		"grade_1_marketable_counts": 11,
		"grade_2_marketable_weight": 255,
		"grade_2_marketable_counts": 1,
		"unmarketable_weight": 0,
		"unmarketable_counts": 0
	}'
);


-- Add another sample harvest data with different JSON properties.
INSERT INTO testDB (
	field_name,
	year,
	date,
	plot_number,
	dynamic_harvest_data
)
VALUES
(
	'Test Field',
	'2023',
	'2023-01-03 09:00:00',
	3,
	'{
		"grade_1_marketable_weight": 3000,
		"grade_1_marketable_counts": 12,
		"grade_2_marketable_weight": 500,
		"grade_2_marketable_counts": 2,
		"unmarketable_weight": 100,
		"unmarketable_counts": 1,
		"extra_property": "example",
		"another_extra_property": 42
	}'
);
