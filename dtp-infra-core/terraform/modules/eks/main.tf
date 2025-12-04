module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "dtp-cluster-${var.env}"
  cluster_version = "1.27"

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnets

  # OPTIMIZATION: Enable OIDC for IAM Roles for Service Accounts (IRSA)
  enable_irsa = true

  # Base Node Group (Operational tools only)
  eks_managed_node_groups = {
    system = {
      min_size     = 2
      max_size     = 3
      desired_size = 2
      instance_types = ["t3.medium"]
      labels = { "workload" = "system" }
    }
  }
}

# OPTIMIZATION: Karpenter Controller (Installs via Helm in CI/CD usually, but IAM here)
module "karpenter" {
  source = "terraform-aws-modules/eks/aws//modules/karpenter"

  cluster_name           = module.eks.cluster_name
  irsa_oidc_provider_arn = module.eks.oidc_provider_arn
  
  # Allow Karpenter to provision instances
  policies = {
    AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  }
}