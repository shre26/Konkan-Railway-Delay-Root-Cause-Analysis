CREATE DATABASE IF NOT EXISTS konkan_railway;
USE konkan_railway;

-- trains table: one row per train no.
CREATE TABLE trains (
    train_no INT PRIMARY KEY,
    train_name VARCHAR(50) NOT NULL,
    type_code VARCHAR(20),
    coverage_tier VARCHAR(10) -- High / Medium / Low
);

-- stations table: one row per station code
CREATE TABLE stations (
    station_code VARCHAR(10) PRIMARY KEY,
    station_full_name VARCHAR(100),
    station_zone VARCHAR(5)
);

-- schedule table: one row per (train, stop) - the scheduled route
CREATE TABLE schedule (
    train_no INT NOT NULL,
    station_no INT NOT NULL,
    station_code VARCHAR(10) NOT NULL,
    distance_from_origin DECIMAL(6.1),
    arrival_day TINYINT,
    arrival_time TIME,
    departure_day TINYINT,
    departure_time TIME,
    PRIMARY KEY (train_no, station_no),
    FOREIGN KEY (train_no) REFERENCES trains(train_no),
    FOREIGN KEY (station_code) REFERENCES stations(station_code)
);

-- delays table: one row per (train, station, date) -- actual delay observed
CREATE TABLE delays (
    delay_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    train_no INT NOT NULL,
    station_code VARCHAR(10) NOT NULL,
    record_date DATE NOT NULL,
    station_no INT NOT NULL,
    delay_minutes DECIMAL(7,1),
    day_of_week VARCHAR(10),
    month TINYINT,
    is_monsoon BOOLEAN,
    is_extreme_delay BOOLEAN,
    UNIQUE KEY uq_train_station_date (train_no, station_code, record_date),
    FOREIGN KEY (train_no) REFERENCES trains(train_no),
    FOREIGN KEY (station_code) REFERENCES stations(station_code)
);