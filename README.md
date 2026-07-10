# Portfolio Project: NC Plus One

This is the README file for the portfolio project

## Database Setup

To setup the database for this project execute the below terminal command from the project root directory:

```bash
psql -f db/setup.sql
```

It should then be possible to use the Postgres client to connect to the database using the below command:

```bash
psql -d nc_plus_one
```

## Database Connection

An `.env` file will require creation to allow secure management of credentials when connecting to the database through Python.
The format should be:

```none
DB_NAME=<your_db_name>
DB_USERNAME=<your_db_username>
DB_PASSWORD=<your_password>
DB_HOST=<your_host>
DB_PORT=<your_port>
```

## Terraform Setup

### Configure the Terraform Backend

In order for Terraform to be able to store its state remotely rather than locally, an Amazon Web Services (AWS) S3 bucket must be created in which to store the Terraform state file. The name of this bucket must then be added to the relevant Terraform file to ensure the correct configuration when Terraform is initialised. This can be achieved by following the below steps:

1. Log in to the AWS console using your AWS credentials
2. Navigate to Amazon S3 -> General purpose buckets - > Create Bucket
3. Create a new bucket and make a note of the name you have defined for it
4. In the file `terraform/provider.tf`, update the `bucket` attribute of the `backend` object so that it references your newly-created bucket name:

```hcl
terraform {
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 6.0"
        }
    }
    backend "s3" {
        bucket = "<INSERT YOUR BUCKET NAME HERE>"
        key = "nc-plus-one/terraform.tfstate"
        region = "eu-west-2"
    }
}
```

### Initialise Terraform

Once the backend configuration is complete, initalise terraform by first changing directory to the `terraform` directory and running the command `terraform init`.

### Terraform Plan

If the `terraform init` command executes successfully, execute the `terraform plan` command in order to identify any problems there might be with the Terraform conifiguration

### Terraform Apply

If no problems are identified after executing the `terraform plan` command then the Terraform configuration can be applied using `terraform apply`.
