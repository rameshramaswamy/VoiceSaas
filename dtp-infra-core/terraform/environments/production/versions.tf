terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket         = "dtp-terraform-state-prod"
    key            = "platform/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "dtp-terraform-lock-prod" # OPTIMIZATION: Locking
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}