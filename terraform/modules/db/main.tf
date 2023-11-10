locals {
  sites = toset(var.sites)
}

resource "postgresql_database" "db" {
  name = var.stage
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
  override_special = "!#$%*()-_=+[]{}<>:?"
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

# Enable extensions
resource "postgresql_extension" "pgvector" {
  name     = "vector"
  version  = "0.4.1"
  database = postgresql_database.db.name
}
