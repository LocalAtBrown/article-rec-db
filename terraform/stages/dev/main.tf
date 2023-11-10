terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.25.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.5.1"
    }
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "1.21.0"
    }
  }
}

provider "aws" {
  region                   = "us-east-1"
  shared_credentials_files = ["~/.aws/credentials"]
}

data "aws_ssm_parameter" "credentials_admin" {
  name = var.credentials_admin_ssm_param
}

locals {
  credentials_admin = jsondecode(data.aws_ssm_parameter.credentials_admin.value)
  sites             = toset(var.sites)
}

provider "postgresql" {
  host      = local.credentials_admin.host
  port      = local.credentials_admin.port
  username  = local.credentials_admin.username
  password  = local.credentials_admin.password
  sslmode   = "require"
  superuser = false
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

  length  = 20
  special = true
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
    HOST     = local.credentials_admin.host
    PORT     = local.credentials_admin.port
    DB_NAME  = var.stage
    USERNAME = postgresql_role.training_job_site[each.key].name
    PASSWORD = random_password.training_job_site_password[each.key].result
  })
}

# Enable extensions
resource "postgresql_extension" "pgvector" {
  name     = "vector"
  version  = "0.4.1"
  database = var.stage
}
