resource "aws_iam_role" "ec2_app_role" {
  name               = "ec2-assume-role${local.name_suffix}"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_policy" "get_db_parameters" {
  name        = "get-db-parameters${local.name_suffix}"
  description = "Allow retrieval of DB parameters from SSM and Secrets Manager"

  policy = jsonencode(
    {
      "Version" : "2012-10-17"
      "Statement" : [
        {
          Effect   = "Allow"
          Action   = ["ssm:GetParameter", "ssm:GetParameters"]
          Resource = "arn:aws:ssm:*:*:parameter/nc-plus-one/*"
        },
        {
          Effect   = "Allow"
          Action   = ["secretsmanager:GetSecretValue"]
          Resource = aws_db_instance.app_db.master_user_secret[0].secret_arn
        },
        {
          Effect   = "Allow"
          Action   = ["kms:Decrypt"]
          Resource = aws_db_instance.app_db.master_user_secret[0].kms_key_id
        }
      ]
    }
  )
}

resource "aws_iam_role_policy_attachment" "attach_parameters_policy" {
  role       = aws_iam_role.ec2_app_role.name
  policy_arn = aws_iam_policy.get_db_parameters.arn
}
