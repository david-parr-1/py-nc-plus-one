terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }

    http = {
      source  = "hashicorp/http"
      version = "~> 3.6"
    }
  }
  backend "s3" {
    bucket = "dp-tf-deploy"
    key    = "nc-plus-one/terraform.tfstate"
    region = "eu-west-2"
  }
}

provider "aws" {
  region = "eu-west-2"
  default_tags {
    tags = {
      ProjectName  = "NC-Plus-One"
      DeployedFrom = "Terraform"
      Repository   = "https://github.com/david-parr-1/py-nc-plus-one.git"
    }
  }
}
