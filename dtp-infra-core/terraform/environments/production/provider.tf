provider "aws" {
  region = "us-east-1"

  # OPTIMIZATION: Default Tags
  # These are applied to VPCs, Subnets, EC2s, RDS, everything.
  default_tags {
    tags = {
      Project     = "DTP-Voice-Agent"
      Environment = "Production"
      ManagedBy   = "Terraform"
      CostCenter  = "Core-Platform"
      Owner       = "DevOps-Team"
    }
  }
}