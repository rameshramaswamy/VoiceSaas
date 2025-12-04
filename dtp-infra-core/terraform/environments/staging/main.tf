provider "aws" {
  region = "us-east-1"
}

terraform {
  backend "s3" {
    bucket = "dtp-terraform-state"
    key    = "staging/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
  }
}

module "vpc" {
  source   = "../../modules/vpc"
  env      = "staging"
  vpc_cidr = "10.0.0.0/16"
}

module "rds" {
  source          = "../../modules/rds"
  env             = "staging"
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnets
}