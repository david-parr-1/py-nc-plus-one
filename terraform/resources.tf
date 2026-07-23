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
  name        = "ec2-ssh-sg"
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
  name        = "ec2-http-sg"
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
  instance_type               = "t2.micro"
  associate_public_ip_address = true
  security_groups             = [aws_security_group.ec2_ssh_sg.name, aws_security_group.ec2_http_sg.name]
  key_name                    = "DPFirstServer"

  tags = {
    Name = "AppServer"
  }

  user_data = templatefile("user_data.sh.tpl", {
    db_name            = "dummy db name"
    db_username        = "dummy db user"
    db_password        = "dummy db password"
    db_host            = "dummy db host"
    db_port            = "dummy db port"
    jwt_expiry_minutes = 30
    jwt_algorithm      = "dummy jwt algorithm"
    jwt_secret         = "dummy jwt secret"
  })

  user_data_replace_on_change = true
}

output "ec2_ip" {
  description = "Public IP address of the created EC2 instance"
  value       = aws_instance.ec2_instance.public_ip
}
