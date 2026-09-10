CREATE TABLE testDB (
    record_id SERIAL PRIMARY KEY,
    field_name VARCHAR(255) NOT NULL,
    year VARCHAR(4) NOT NULL,
    date TIMESTAMP NOT NULL,
    plot_number INT NOT NULL,
    dynamic_harvest_data JSONB, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);