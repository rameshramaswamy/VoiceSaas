variable "app_name" { type = string }
variable "env" { type = string }
variable "kms_key_arn" { type = string }

resource "aws_ecr_repository" "main" {
  name                 = "dtp-${var.app_name}-${var.env}"
  image_tag_mutability = "IMMUTABLE" # Optimization: Prevents tag overwriting

  image_scanning_configuration {
    scan_on_push = true # Optimization: Auto-scan for CVEs
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = var.kms_key_arn
  }

  tags = {
    Name = "dtp-${var.app_name}-${var.env}"
  }
}

# Lifecycle Policy: Clean up old untagged images to save money
resource "aws_ecr_lifecycle_policy" "cleanup" {
  repository = aws_ecr_repository.main.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Expire untagged images older than 14 days"
      selection    = {
        tagStatus   = "untagged"
        countType   = "sinceImagePushed"
        countUnit   = "days"
        countNumber = 14
      }
      action = { type = "expire" }
    }]
  })
}

output "repository_url" { value = aws_ecr_repository.main.repository_url }