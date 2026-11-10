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

CREATE TABLE record_images (
    id SERIAL PRIMARY KEY,
    harvest_record_id INT NOT NULL REFERENCES harvest_records(id) ON DELETE CASCADE,
    data BYTEA NOT NULL,
    original_filename VARCHAR(255),
    content_type VARCHAR(64) NOT NULL,
    size_bytes BIGINT NOT NULL,
    category VARCHAR(32) NOT NULL DEFAULT 'Other',
    caption VARCHAR(512),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE seed_inventory (
    id SERIAL PRIMARY KEY,
    crop_type VARCHAR(100) NOT NULL,
    variety_name VARCHAR(150),
    breeding_line VARCHAR(150),
    seed_weight_g NUMERIC(12, 4),
    seed_count INTEGER,
    date_recorded TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,

    CONSTRAINT check_seed_weight CHECK (seed_weight_g >= 0),

    CONSTRAINT check_seed_count CHECK (seed_count >= 0)
);
CREATE INDEX ix_record_images_harvest_record_id ON record_images(harvest_record_id);
CREATE INDEX ix_seed_inventory_crop_type ON seed_inventory(crop_type);