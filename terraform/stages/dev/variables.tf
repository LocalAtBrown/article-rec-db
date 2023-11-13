variable "stage" {
  type    = string
  default = "dev"
}

variable "credentials_admin_ssm_param" {
  type        = string
  description = "The name of the SSM parameter containing the credentials for the Postgres admin user"
}

variable "sites" {
  type        = list(string) # use kebab case, e.g., "dallas-free-press"
  default     = ["afro-la", "dallas-free-press"]
  description = "Partner sites"
}
