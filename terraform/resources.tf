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

resource "aws_security_group" "ec2_sg" {
  name        = "ec2-sg"
  description = "Allows SSH traffic in from any IP"
}

resource "aws_vpc_security_group_ingress_rule" "allow_ssh" {
  security_group_id = aws_security_group.ec2_sg.id
  cidr_ipv4         = "${chomp(data.http.myip.response_body)}/32"
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_instance" "ec2_instance" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t2.micro"
  associate_public_ip_address = true
  security_groups             = [aws_security_group.ec2_sg.name]
  key_name                    = "DPFirstServer"
  tags = {
    Name = "AppServer"
  }
}

output "ec2_ip" {
  description = "Public IP address of the created EC2 instance"
  value       = aws_instance.ec2_instance.public_ip
}
