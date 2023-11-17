locals {
  sites                  = toset(var.sites)
  schema                 = "public"
  password_special_chars = "!@$"
  tables = {
    "page"           = "page"
    "article"        = "article"
    "execution"      = "execution"
    "embedding"      = "embedding"
    "recommendation" = "recommendation"
  }
}

locals {
  training_job_privileges = {
    "table" = {
      "SELECT" = keys(local.tables)
      "INSERT" = keys(local.tables)
      "UPDATE" = [local.tables.page, local.tables.article]
      "DELETE" = keys(local.tables)
    }
  }
  reader_privileges = {
    "table" = { "SELECT" = keys(local.tables) }
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

resource "postgresql_grant" "training_job_table_privileges" {
  for_each = local.training_job_privileges.table

  database    = postgresql_database.db.name
  role        = postgresql_role.training_job.name
  schema      = local.schema
  object_type = "table"
  objects     = each.value
  privileges  = [each.key]
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

resource "postgresql_grant" "reader_table_privileges" {
  for_each = local.reader_privileges.table

  database    = postgresql_database.db.name
  role        = postgresql_role.reader.name
  schema      = local.schema
  object_type = "table"
  objects     = each.value
  privileges  = [each.key]
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