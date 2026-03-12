output "s3_bucket_name" {
  description = "Terraform state S3 bucket name"
  value       = aws_s3_bucket.tf_state.bucket
}

output "s3_bucket_arn" {
  description = "Terraform state S3 bucket ARN"
  value       = aws_s3_bucket.tf_state.arn
}

output "iam_user_name" {
  description = "IAM deploy user name"
  value       = aws_iam_user.deploy.name
}

output "iam_access_key_id" {
  description = "IAM access key ID"
  value       = aws_iam_access_key.deploy.id
}

output "iam_secret_access_key" {
  description = "IAM secret access key"
  value       = aws_iam_access_key.deploy.secret
  sensitive   = true
}
