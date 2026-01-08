# ------------------------------------------------------------------------------
# revisit_prediction.tf
# ------------------------------------------------------------------------------

# resource "aws_ssm_parameter" "revisit_prediction__function_arn" {
#   name  = "${local.output_prefix}/revisit_prediction/function_arn"
#   type  = "SecureString"
#   value = module.revisit_prediction_lambda.lambda_function_arn
# }

# resource "aws_ssm_parameter" "revisit_prediction__function_name" {
#   name  = "${local.output_prefix}/revisit_prediction/function_name"
#   type  = "SecureString"
#   value = module.revisit_prediction_lambda.lambda_function_name
# }

resource "aws_ssm_parameter" "to_email_addresses_json" {
  name  = "${local.output_prefix}/revisit_news_lambda/to_email_addresses_json"
  type  = "SecureString"
  value = "['user@example.net']"

  # This will managed by an external process
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "pharmai_to_email_addresses_json" {
  name  = "${local.output_prefix}/pharmai/to_email_addresses_json"
  type  = "SecureString"
  value = "['user@example.net']"

  # This will managed by an external process
  lifecycle {
    ignore_changes = [value]
  }
}


# CodeBuild env var secret
# An AWS Secret would be better, but costs money
resource "aws_ssm_parameter" "codebuild_terraform_news_api_key" {
  name  = "${local.output_prefix}/codebuild_terraform/news_api_key"
  type  = "SecureString"
  value = "CHANGE_THIS_TO_THE_REAL_VALUE"

  # This will managed by an external process
  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "codebuild_terraform_openai_api_key" {
  name  = "${local.output_prefix}/codebuild_terraform/openai_api_key"
  type  = "SecureString"
  value = "CHANGE_THIS_TO_THE_REAL_VALUE"

  # This will managed by an external process
  lifecycle {
    ignore_changes = [value]
  }
}
