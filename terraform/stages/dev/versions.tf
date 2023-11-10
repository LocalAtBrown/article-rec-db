terraform {
  required_version = "~> 1.6.3"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.25.0"
    }
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "1.21.0"
    }
  }
}
