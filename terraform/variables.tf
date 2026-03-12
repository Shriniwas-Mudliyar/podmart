variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "podmart"
}

variable "bucket_name" {
  description = "S3 bucket for Terraform state"
  type        = string
  default     = "podmart-tf-state-061785"
}
