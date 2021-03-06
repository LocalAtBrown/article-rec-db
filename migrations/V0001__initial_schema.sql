CREATE TABLE article(
  id SERIAL PRIMARY KEY,
  -- reference id for article in external newsroom system
  external_id INTEGER NOT NULL,
  title TEXT NOT NULL DEFAULT '',
  path TEXT NOT NULL DEFAULT '',
  published_at TIMESTAMPTZ DEFAULT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_external_id ON article (external_id);

CREATE TABLE model (
  id SERIAL PRIMARY KEY,
  -- type of entity a model is recommending articles for - "article", "user," etc
  type TEXT NOT NULL,
  -- status of the model - "pending," "current," etc
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE recommendation (
  id SERIAL PRIMARY KEY,
  model_id INTEGER NOT NULL REFERENCES model (id) ON DELETE CASCADE,
  -- represents the entity being recommended for. could be an article, user, etc
  source_entity_id TEXT NOT NULL,
  -- represents the article recommended for the source entity
  recommended_article_id INTEGER NOT NULL REFERENCES article (id) ON DELETE CASCADE,
  -- how relevant the article is for the entity
  score DECIMAL (7, 6) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (
    model_id,
    source_entity_id,
    recommended_article_id
  )
);

CREATE INDEX idx_source_entity_id_model_id ON recommendation (source_entity_id, model_id);
