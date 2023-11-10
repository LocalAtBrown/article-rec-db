# We use S3 as a backend to store the Terraform state file
# see: https://spacelift.io/blog/terraform-s3-backend
terraform {
  backend "s3" {
    bucket         = "terraform-article-rec" # bucket+key is where to store the state file
    key            = "db/dev/terraform.tfstate"
    dynamodb_table = "terraform-state-lock" # DynamoDB to lock the state file
    region         = "us-east-1"
    encrypt        = true
  }
}
