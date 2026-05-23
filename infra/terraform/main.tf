terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state — configure for your account
  backend "s3" {
    bucket = "nyayrithm-tf-state"
    key    = "nyayrithm/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# ── VPC ──────────────────────────────────────────────────────────────────────
module "vpc" {
  source = "../modules/vpc"
  env    = var.env
}

# ── RDS (PostgreSQL) — enabled if db_backend = "postgres" ─────────────────
module "rds" {
  count  = var.db_backend == "postgres" ? 1 : 0
  source = "../modules/rds"
  env    = var.env
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}

# ── ElastiCache (Redis) ───────────────────────────────────────────────────
module "elasticache" {
  source     = "../modules/elasticache"
  env        = var.env
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}

# ── S3 (Evidence Storage) ────────────────────────────────────────────────
module "s3" {
  count  = var.storage_backend == "s3" ? 1 : 0
  source = "../modules/s3"
  env    = var.env
}

# ── ECS (Backend + Celery) ───────────────────────────────────────────────
module "ecs" {
  source         = "../modules/ecs"
  env            = var.env
  vpc_id         = module.vpc.vpc_id
  subnet_ids     = module.vpc.private_subnet_ids
  backend_image  = var.backend_image
  db_url         = var.db_backend == "postgres" ? module.rds[0].connection_url : ""
  redis_url      = module.elasticache.connection_url
}

# ── Qdrant (Vector Store) — enabled if vector_db_backend = "qdrant" ───────
module "qdrant" {
  count  = var.vector_db_backend == "qdrant" ? 1 : 0
  source = "../modules/qdrant"
  env    = var.env
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}

# ── CloudFront (Frontend CDN) ────────────────────────────────────────────
module "cloudfront" {
  count  = var.deploy_frontend ? 1 : 0
  source = "../modules/cloudfront"
  env    = var.env
}
