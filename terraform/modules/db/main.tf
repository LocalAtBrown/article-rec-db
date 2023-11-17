locals {
  sites                  = toset(var.sites)
  password_special_chars = "!@$"
  tables = {
    "page"           = {}
    "article"        = {}
    "execution"      = {}
    "embedding"      = {}
    "recommendation" = {}
  }
}

resource "postgresql_database" "db" {
  name = var.stage
}

# Enable extensions
resource "postgresql_extension" "pgvector" {
  name     = "vector"
  version  = "0.4.1"
  database = postgresql_database.db.name
}

# Training job role and site users
resource "postgresql_role" "training_job" {
  name  = "${var.stage}_training_job"
  login = false
}

resource "random_password" "training_job_site_password" {
  for_each = local.sites

  length           = 20
  special          = true
  override_special = local.password_special_chars
}

resource "postgresql_role" "training_job_site" {
  for_each = local.sites

  name     = "${var.stage}_training_job_${replace(each.key, "-", "_")}"
  login    = true
  password = random_password.training_job_site_password[each.key].result
  roles    = [postgresql_role.training_job.name]
}

resource "aws_ssm_parameter" "training_job_site_credentials" {
  for_each = local.sites

  name = "/${var.stage}/article-rec/${each.key}/training-job/database-credentials"
  type = "String"
  value = jsonencode({
    HOST     = var.host
    PORT     = var.port
    DB_NAME  = var.stage
    USERNAME = postgresql_role.training_job_site[each.key].name
    PASSWORD = random_password.training_job_site_password[each.key].result
  })
}

# Read-only role and user
resource "random_password" "reader_password" {
  length           = 20
  special          = true
  override_special = local.password_special_chars
}

resource "postgresql_role" "reader" {
  name     = "${var.stage}_reader"
  login    = true
  password = random_password.reader_password.result
}

resource "postgresql_grant" "readonly_tables" {
  database    = postgresql_database.db.name
  role        = postgresql_role.reader.name
  schema      = "public"
  object_type = "table"
  objects     = keys(local.tables)
  privileges  = ["SELECT"]
}

resource "aws_ssm_parameter" "reader_credentials" {
  name = "/${var.stage}/article-rec/reader/all/database-credentials"
  type = "String"
  value = jsonencode({
    HOST     = var.host
    PORT     = var.port
    DB_NAME  = var.stage
    USERNAME = postgresql_role.reader.name
    PASSWORD = random_password.reader_password.result
  })
}