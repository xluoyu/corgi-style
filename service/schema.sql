-- PostgreSQL Schema for Outfit Agent
-- Database: outfit_agent

CREATE DATABASE outfit_agent;

\c outfit_agent;

CREATE TYPE gender_type AS ENUM ('male', 'female', 'other');
CREATE TYPE clothes_category AS ENUM ('top', 'pants', 'outer', 'inner', 'accessory');
CREATE TYPE temperature_range AS ENUM ('summer', 'spring_autumn', 'winter', 'all_season');
CREATE TYPE scene_type AS ENUM ('daily', 'work', 'sport', 'date', 'party');
CREATE TYPE wear_method AS ENUM ('inner_wear', 'outer_wear', 'single_wear', 'layering');

CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL UNIQUE,
    nickname VARCHAR(64) DEFAULT '匿名用户',
    gender gender_type DEFAULT 'other',
    height FLOAT,
    weight FLOAT,
    style_preference TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_id ON "user"(user_id);

CREATE TABLE IF NOT EXISTS user_preference (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    liked_colors TEXT,
    liked_styles TEXT,
    liked_categories TEXT,
    disliked_colors TEXT,
    temperature_min FLOAT,
    temperature_max FLOAT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pref_user FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_pref_user_id ON user_preference(user_id);

CREATE TABLE IF NOT EXISTS user_clothes (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    image_url VARCHAR(512) NOT NULL,
    category clothes_category NOT NULL,
    color VARCHAR(32) NOT NULL,
    temperature_range temperature_range NOT NULL,
    scene scene_type,
    wear_method wear_method,
    brand VARCHAR(128),
    description TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_clothes_user FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_clothes_user_id ON user_clothes(user_id);
CREATE INDEX idx_clothes_category ON user_clothes(category);

CREATE TABLE IF NOT EXISTS outfit_record (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    scheme_id VARCHAR(32) NOT NULL,
    weather_temp FLOAT,
    weather_city VARCHAR(64),
    top_clothes_id INTEGER,
    pants_clothes_id INTEGER,
    outer_clothes_id INTEGER,
    inner_clothes_id INTEGER,
    accessory_clothes_id INTEGER,
    scheme_description TEXT,
    match_score FLOAT DEFAULT 0.0,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_outfit_user FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_top_clothes FOREIGN KEY (top_clothes_id) REFERENCES user_clothes(id) ON DELETE SET NULL,
    CONSTRAINT fk_pants_clothes FOREIGN KEY (pants_clothes_id) REFERENCES user_clothes(id) ON DELETE SET NULL,
    CONSTRAINT fk_outer_clothes FOREIGN KEY (outer_clothes_id) REFERENCES user_clothes(id) ON DELETE SET NULL,
    CONSTRAINT fk_inner_clothes FOREIGN KEY (inner_clothes_id) REFERENCES user_clothes(id) ON DELETE SET NULL,
    CONSTRAINT fk_accessory_clothes FOREIGN KEY (accessory_clothes_id) REFERENCES user_clothes(id) ON DELETE SET NULL
);

CREATE INDEX idx_outfit_user_id ON outfit_record(user_id);
CREATE INDEX idx_outfit_scheme_id ON outfit_record(scheme_id);

CREATE TABLE IF NOT EXISTS outfit_feedback (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    outfit_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_feedback_user FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_feedback_outfit FOREIGN KEY (outfit_id) REFERENCES outfit_record(id) ON DELETE CASCADE
);

CREATE INDEX idx_feedback_user_id ON outfit_feedback(user_id);
CREATE INDEX idx_feedback_outfit_id ON outfit_feedback(outfit_id);

-- Function to auto-update update_time timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.update_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for auto-updating update_time
CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON "user"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preference_updated_at BEFORE UPDATE ON user_preference
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_clothes_updated_at BEFORE UPDATE ON user_clothes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
