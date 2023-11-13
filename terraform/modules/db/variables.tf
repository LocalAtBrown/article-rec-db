variable "stage" {
  type = string
}

variable "sites" {
  type        = list(string)
  description = "Partner sites"
}

variable "host" {
  type        = string
  description = "The host of the database"
}

variable "port" {
  type        = number
  description = "The port of the database"
}
