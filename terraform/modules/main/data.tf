locals {
  core_output_prefix = "/${var.namespace}/${var.env}/core"
}

data "aws_ssm_parameter" "vpc_id" {
  name = "${local.core_output_prefix}/vpc_id"
}

# Core management
data "aws_ssm_parameter" "event_bus_arn" {
  name = "${local.core_output_prefix}/event_bus_arn"
}
data "aws_ssm_parameter" "event_bus_name" {
  name = "${local.core_output_prefix}/event_bus_name"
}
data "aws_ssm_parameter" "ses_email_address" {
  name = "${local.core_output_prefix}/ses_email_address"
}
data "aws_ssm_parameter" "ses_email_arn" {
  name = "${local.core_output_prefix}/ses_email_arn"
}
data "aws_ses_domain_identity" "ianandcatherine" {
  domain = "ian-and-catherine.com"
}
data "aws_ses_domain_identity" "ikenley" {
  domain = "ikenley.com"
}

# Data environment
data "aws_ssm_parameter" "data_lake_s3_bucket_arn" {
  name = "${local.core_output_prefix}/data_lake_s3_bucket_arn"
}
data "aws_ssm_parameter" "data_lake_s3_bucket_name" {
  name = "${local.core_output_prefix}/data_lake_s3_bucket_name"
}
