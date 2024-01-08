-- Create a new sequence
CREATE SEQUENCE recommendation_id_seq_bigint;

-- Change the data type of the id column to BIGINT
ALTER TABLE recommendation ALTER COLUMN id TYPE BIGINT;

-- Set the default value of the id column to the next value from the new sequence
ALTER TABLE recommendation ALTER COLUMN id SET DEFAULT nextval('recommendation_id_seq_bigint');

-- Set the new sequence to the max value of id
SELECT setval('recommendation_id_seq_bigint', COALESCE((SELECT MAX(id)+1 FROM recommendation), 1), false);

-- Drop the old sequence
DROP SEQUENCE recommendation_id_seq;
