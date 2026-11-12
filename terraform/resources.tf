locals {
  name_suffix = var.environment == "production" ? "" : "-${var.environment}"
  ssm_path    = var.environment == "production" ? "/nc-plus-one" : "/nc-plus-one/${var.environment}"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

data "http" "myip" {
  url = "https://ipv4.icanhazip.com"
}

resource "aws_security_group" "ec2_ssh_sg" {
  name        = "ec2-ssh-sg${local.name_suffix}"
  description = "Allows SSH traffic in from my IP only"
}

resource "aws_vpc_security_group_ingress_rule" "allow_ssh" {
  security_group_id = aws_security_group.ec2_ssh_sg.id
  cidr_ipv4         = "${chomp(data.http.myip.response_body)}/32"
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_security_group" "ec2_http_sg" {
  name        = "ec2-http-sg${local.name_suffix}"
  description = "Allows HTTP traffic from any IP"
}

resource "aws_vpc_security_group_ingress_rule" "allow_http" {
  security_group_id = aws_security_group.ec2_http_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 8000
  to_port           = 8000
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "allow_outbound" {
  security_group_id = aws_security_group.ec2_http_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_instance" "ec2_instance" {
  ami                         = data.aws_ami.ubuntu.id
  depends_on                  = [aws_db_instance.app_db]
  instance_type               = "t3.micro"
  iam_instance_profile        = aws_iam_instance_profile.ec2_instance_profile.name
  associate_public_ip_address = true
  security_groups             = [aws_security_group.ec2_ssh_sg.name, aws_security_group.ec2_http_sg.name]
  key_name                    = "dp-key-pair"
  user_data = templatefile("user_data.sh.tpl", {
    ssm_parameter_prefix = "${local.ssm_path}"
  })

  tags = {
    Name = "AppServer${local.name_suffix}"
  }
}

resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "ec2-instance-profile${local.name_suffix}"
  role = aws_iam_role.ec2_app_role.name
}

output "ec2_ip" {
  description = "Public IP address of the created EC2 instance"
  value       = aws_instance.ec2_instance.public_ip
}

resource "aws_db_instance" "app_db" {
  allocated_storage           = 20
  db_name                     = "nc_plus_one_db"
  deletion_protection         = false
  engine                      = "postgres"
  engine_version              = "16"
  identifier                  = "nc-plus-one-db${local.name_suffix}"
  instance_class              = "db.t4g.micro"
  manage_master_user_password = true
  multi_az                    = false
  port                        = 5432
  publicly_accessible         = false
  skip_final_snapshot         = true
  storage_type                = "gp2"
  storage_encrypted           = true
  username                    = "db_admin"
  vpc_security_group_ids      = [aws_security_group.db_sg.id]
}

resource "aws_ssm_parameter" "app_db_host" {
  name  = "${local.ssm_path}/DB_HOST"
  type  = "String"
  value = aws_db_instance.app_db.address
}

resource "aws_ssm_parameter" "app_db_port" {
  name  = "${local.ssm_path}/DB_PORT"
  type  = "String"
  value = aws_db_instance.app_db.port
}

resource "aws_ssm_parameter" "app_db_username" {
  name  = "${local.ssm_path}/DB_USERNAME"
  type  = "String"
  value = aws_db_instance.app_db.username
}

resource "aws_ssm_parameter" "app_db_name" {
  name  = "${local.ssm_path}/DB_NAME"
  type  = "String"
  value = aws_db_instance.app_db.db_name
}

resource "aws_ssm_parameter" "db_secret_arn" {
  name  = "${local.ssm_path}/DB_SECRET_ARN"
  type  = "String"
  value = aws_db_instance.app_db.master_user_secret[0].secret_arn
}

resource "aws_security_group" "db_sg" {
  name        = "app-db-sg${local.name_suffix}"
  description = "Allow app EC2 connection to app DB"
  vpc_id      = aws_security_group.ec2_http_sg.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "app_db_from_ec2" {
  security_group_id            = aws_security_group.db_sg.id
  referenced_security_group_id = aws_security_group.ec2_http_sg.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "aws_ssm_parameter" "jwt_secret" {
  name  = "${local.ssm_path}/JWT_SECRET"
  type  = "String"
  value = var.jwt_secret
}

resource "aws_ssm_parameter" "jwt_expiry_minutes" {
  name  = "${local.ssm_path}/JWT_EXPIRY_MINUTES"
  type  = "String"
  value = var.jwt_expiry_minutes
}

resource "aws_ssm_parameter" "jwt_algorithm" {
  name  = "${local.ssm_path}/JWT_ALGORITHM"
  type  = "String"
  value = var.jwt_algorithm
}
