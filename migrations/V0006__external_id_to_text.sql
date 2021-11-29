ALTER TABLE article
    ALTER COLUMN external_id TYPE TEXT,
    ALTER COLUMN external_id SET DEFAULT '',
    ALTER COLUMN external_id SET NOT NULL;
