USE konkan_railway;

-- Performance indexes for faster queries on the delays table.

CREATE INDEX idx_delays_date ON delays(record_date);
CREATE INDEX idx_delays_train_date ON delays(train_no, record_date);
CREATE INDEX idx_delays_station_date ON delays(station_code, record_date);