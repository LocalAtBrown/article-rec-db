provider "aws" {
  region                   = "us-east-1"
  shared_credentials_files = ["~/.aws/credentials"]
}

data "aws_ssm_parameter" "credentials_admin" {
  name = var.credentials_admin_ssm_param
}

locals {
  credentials_admin = jsondecode(data.aws_ssm_parameter.credentials_admin.value)
}

provider "postgresql" {
  host      = local.credentials_admin.host
  port      = local.credentials_admin.port
  username  = local.credentials_admin.username
  password  = local.credentials_admin.password
  sslmode   = "require"
  superuser = false
}

module "db" {
  source = "../../modules/db"

  stage = var.stage
  sites = var.sites
  host  = local.credentials_admin.host
  port  = local.credentials_admin.port
}

