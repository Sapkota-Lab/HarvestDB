CREATE TABLE fields (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL UNIQUE,
    location VARCHAR(255),
    description VARCHAR(2048),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE harvest_events (
    id SERIAL PRIMARY KEY,
    field_id INT NOT NULL REFERENCES fields(id),
    harvest_date DATE NOT NULL,
    harvest_number INT,
    notes VARCHAR(2048),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE harvest_records (
    id SERIAL PRIMARY KEY,
    harvest_event_id INT NOT NULL REFERENCES harvest_events(id),
    plot_number VARCHAR(64) NOT NULL,
    dynamic_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);