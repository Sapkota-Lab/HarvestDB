-- Seed a field, then harvest events, then records that reference them.
INSERT INTO fields (name, location, description)
VALUES ('Test Field', 'Test Location', 'Seed data for manual CRUD testing')
RETURNING id \gset field_

INSERT INTO harvest_events (field_id, harvest_date, harvest_number, notes)
VALUES (:'field_id', '2023-01-01', 1, 'First test harvest')
RETURNING id \gset event_one_

INSERT INTO harvest_events (field_id, harvest_date, harvest_number, notes)
VALUES (:'field_id', '2023-01-02', 2, 'Second test harvest')
RETURNING id \gset event_two_

INSERT INTO harvest_events (field_id, harvest_date, harvest_number, notes)
VALUES (:'field_id', '2023-01-03', 3, 'Test harvest with additional JSON properties')
RETURNING id \gset event_three_

INSERT INTO harvest_records (harvest_event_id, plot_number, dynamic_data)
VALUES
(
    :'event_one_id',
    '1',
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
    :'event_two_id',
    '2',
    '{
        "grade_1_marketable_weight": 2709,
        "grade_1_marketable_counts": 11,
        "grade_2_marketable_weight": 255,
        "grade_2_marketable_counts": 1,
        "unmarketable_weight": 0,
        "unmarketable_counts": 0
    }'
),
(
    :'event_three_id',
    '3',
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
