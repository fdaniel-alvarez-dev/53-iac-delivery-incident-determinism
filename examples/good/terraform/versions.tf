terraform {
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.24"
    }
  }

  backend "s3" {
    bucket         = "example-terraform-state-bucket"
    key            = "blockchain-product/devops-demo/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "example-terraform-locks"
    encrypt        = true
  }
}

