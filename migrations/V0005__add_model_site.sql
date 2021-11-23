DROP INDEX idx_type_status;

ALTER TABLE model ADD site TEXT NOT NULL DEFAULT '';

CREATE INDEX idx_type_status_site ON model (type, status, site);
