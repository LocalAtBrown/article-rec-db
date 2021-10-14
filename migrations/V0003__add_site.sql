-- external ids are no longer unique in multitenant setup
DROP INDEX uq_external_id;

ALTER TABLE article
    ADD site text,
    ADD CONSTRAINT uq_site_external_id UNIQUE (site, external_id);

