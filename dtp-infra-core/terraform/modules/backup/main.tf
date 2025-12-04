variable "env" { type = string }
variable "db_arn" { type = string }

# 1. The Secure Vault
resource "aws_backup_vault" "main" {
  name        = "dtp-backup-vault-${var.env}"
  kms_key_arn = var.kms_key_arn
  
  # Optimization: Verify this vault exists before applying Lock
  force_destroy = false 
}

# 2. The Plan (Daily Backups, Retain 30 Days)
resource "aws_backup_plan" "core" {
  name = "dtp-daily-backup-${var.env}"

  rule {
    rule_name         = "daily_retention"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 5 * * ? *)" # 5 AM UTC
    
    lifecycle {
      delete_after = 30
      cold_storage_after = 0 # Instant access required for DR
    }
    
    # Optimization: Separate backup from production storage
    recovery_point_tags = {
      Environment = var.env
      Role        = "backup"
    }
  }
}

# 3. Assigning Resources (RDS)
resource "aws_backup_selection" "db_backup" {
  iam_role_arn = aws_iam_role.backup_role.arn
  name         = "dtp-rds-selection"
  plan_id      = aws_backup_plan.core.id

  resources = [
    var.db_arn # Backs up the RDS instance
  ]
}

# 4. IAM Role for Backup Service
resource "aws_iam_role" "backup_role" {
  name = "dtp-backup-role-${var.env}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "backup.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "backup_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
  role       = aws_iam_role.backup_role.name
}