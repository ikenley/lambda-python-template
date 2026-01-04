# ------------------------------------------------------------------------------
# Summarize phara insights using AI
# ------------------------------------------------------------------------------

locals {
  pharmai_id   = "${local.id}-pharmai"
  pharmai_desc = "Summarize pharma insights using AI"
}

# ------------------------------------------------------------------------------
# Pharma AI insights Lambda Function
# ------------------------------------------------------------------------------

module "pharmai" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.1.2"

  function_name = local.pharmai_id
  description   = local.pharmai_desc
  handler       = "function.handler"
  runtime       = "python3.12"
  publish       = true
  timeout       = 180 # 3 minutes

  source_path = "../../../src/pharmai/src"

  layers = [
    module.pharmai_layer.lambda_layer_arn,
  ]

  environment_variables = {
    EVENT_BUS_NAME                = data.aws_ssm_parameter.event_bus_name.value
    S3_BUCKET_NAME                = data.aws_ssm_parameter.data_lake_s3_bucket_name.value
    SES_FROM_EMAIL_ADDRESS        = data.aws_ssm_parameter.ses_email_address.value
    TO_EMAIL_ADDRESSES_PARAM_NAME = aws_ssm_parameter.pharmai_to_email_addresses_json.name
    OPENAI_API_KEY                = var.openai_api_key
  }

  tags = local.tags
}

module "pharmai_layer" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.1.2"

  create_layer = true

  layer_name          = "${local.pharmai_id}-layer"
  description         = "Lambda layer for ${local.pharmai_id}"
  runtime             = "python3.12"
  compatible_runtimes = ["python3.12"]

  source_path = [{
    pip_requirements = "../../../src/pharmai/layer/requirements.txt"
    prefix_in_zip    = "python"
  }]

}

resource "aws_iam_policy" "pharmai" {
  name = local.pharmai_id

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Sid" : "ListObjectsInBucket",
        "Effect" : "Allow",
        "Action" : ["s3:ListBucket"],
        "Resource" : [data.aws_ssm_parameter.data_lake_s3_bucket_arn.value]
      },
      {
        "Sid" : "AllObjectActions",
        "Effect" : "Allow",
        "Action" : "s3:GetObject",
        "Resource" : ["${data.aws_ssm_parameter.data_lake_s3_bucket_arn.value}/news/*"]
      },
      {
        "Sid" : "PutEvents",
        "Effect" : "Allow",
        "Action" : "events:PutEvents",
        "Resource" : [data.aws_ssm_parameter.event_bus_arn.value],
        "Condition" : {
          "StringEqualsIfExists" : {
            "events:source" : "lambdapythontemplate.revisitnewsfunction"
          }
        }
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "ssm:DescribeParameters"
        ],
        "Resource" : "*"
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "ssm:GetParameter"
        ],
        "Resource" : [aws_ssm_parameter.pharmai_to_email_addresses_json.arn]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "ses:SendEmail"
        ],
        "Resource" : [data.aws_ssm_parameter.ses_email_arn.value]
      }
    ]
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "pharmai" {
  role       = module.pharmai.lambda_role_name
  policy_arn = aws_iam_policy.pharmai.arn
}

# ------------------------------------------------------------------------------
# Event trigger
# ------------------------------------------------------------------------------

resource "aws_cloudwatch_event_rule" "pharmai" {
  name        = local.pharmai_id
  description = local.pharmai_desc

  schedule_expression = "cron(0 10 * * ? *)" # Every morning at 5am EST # 0 0 6 ? * TUE # Every Tuesday at 6am

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "pharmai" {
  target_id = local.pharmai_id
  rule      = aws_cloudwatch_event_rule.pharmai.name
  arn       = module.pharmai.lambda_function_arn
}

resource "aws_lambda_permission" "pharmai_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.pharmai.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.pharmai.arn
}
