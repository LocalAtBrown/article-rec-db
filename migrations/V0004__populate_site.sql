-- Run this migration only once after we ship the 
-- article training job change that populates
-- the site parameter properly. After this change,
-- make the site parameter required not null

UPDATE article SET site = 'washington-city-paper' where site is null;

ALTER TABLE article ALTER COLUMN site SET NOT NULL; 
