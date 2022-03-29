CREATE INDEX IF NOT EXISTS idx_rec_model_id ON recommendation (model_id);
CREATE INDEX IF NOT EXISTS idx_rec_article_id ON recommendation (recommended_article_id);