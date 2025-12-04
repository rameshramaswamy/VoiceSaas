resource "aws_iam_role" "rds_proxy_role" {
  name = "dtp-rds-proxy-role-${var.env}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "rds.amazonaws.com" }
    }]
  })
}

# Allow Proxy to read Secrets Manager to auth against DB
resource "aws_iam_role_policy" "rds_proxy_policy" {
  role = aws_iam_role.rds_proxy_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "secretsmanager:GetSecretValue"
      Resource = aws_secretsmanager_secret.db_creds.arn
    }, {
      Effect = "Allow"
      Action = "kms:Decrypt"
      Resource = aws_kms_key.db_key.arn
    }]
  })
}

resource "aws_db_proxy" "main" {
  name                   = "dtp-rds-proxy-${var.env}"
  debug_logging          = false
  engine_family          = "POSTGRESQL"
  idle_client_timeout    = 1800
  require_tls            = true
  role_arn               = aws_iam_role.rds_proxy_role.arn
  vpc_subnet_ids         = var.private_subnets
  vpc_security_group_ids = [var.db_security_group_id]

  auth {
    auth_scheme = "SECRETS"
    description = "AWS Secrets Manager Auth"
    iam_auth    = "DISABLED"
    secret_arn  = aws_secretsmanager_secret.db_creds.arn
  }

  tags = {
    Environment = var.env
  }
}

resource "aws_db_proxy_default_target_group" "main" {
  db_proxy_name = aws_db_proxy.main.name
  connection_pool_config {
    connection_borrow_timeout = 120
    max_connections_percent   = 100
    session_pinning_filters   = ["EXCLUDE_VARIABLE_SETS"]
  }
}

resource "aws_db_proxy_target" "main" {
  db_instance_identifier = aws_db_instance.enterprise.id
  db_proxy_name          = aws_db_proxy.main.name
  target_group_name      = aws_db_proxy_default_target_group.main.name
}

# Output the PROXY endpoint, not the DB endpoint
output "proxy_endpoint" {
  value = aws_db_proxy.main.endpoint
}