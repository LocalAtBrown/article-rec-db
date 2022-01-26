-- This table stores references to URL paths that may or may not be
-- valid articles in the newsroom system. This saves the training
-- job from hitting the newsroom API over and over again

CREATE TABLE path (
  id SERIAL PRIMARY KEY,
  path TEXT NOT NULL,
  site TEXT NOT NULL DEFAULT '',
  external_id TEXT DEFAULT '',
  exclude_reason TEXT DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX idx_path_site ON path (path, site);