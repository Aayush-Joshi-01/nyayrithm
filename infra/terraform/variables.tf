variable "env" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "backend_image" {
  description = "ECR image URI for the backend"
  type        = string
  default     = ""
}

# ── Service backend selections (mirror .env choices) ─────────────────────────

variable "db_backend" {
  description = "Database backend: postgres | mongodb | sqlite | dynamodb"
  type        = string
  default     = "postgres"
}

variable "vector_db_backend" {
  description = "Vector DB: qdrant | chroma | pinecone | weaviate | pgvector"
  type        = string
  default     = "qdrant"
}

variable "storage_backend" {
  description = "File storage: local | s3 | gcs | azure_blob | minio"
  type        = string
  default     = "s3"
}

variable "deploy_frontend" {
  description = "Whether to deploy frontend via CloudFront"
  type        = bool
  default     = true
}
