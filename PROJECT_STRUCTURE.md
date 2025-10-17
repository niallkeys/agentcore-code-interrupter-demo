# Dynamic Tool Runtime - Project Structure

## Overview

This document describes the project structure for the Dynamic Tool Runtime system.

## Directory Structure

```
dynamic-tool-runtime/
├── .kiro/
│   └── specs/
│       └── dynamic-tool-runtime/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
├── terraform/                          # Infrastructure as Code
│   ├── main.tf                        # Root module
│   ├── variables.tf                   # Input variables
│   ├── outputs.tf                     # Output values
│   ├── Makefile                       # Deployment automation
│   ├── README.md                      # Deployment guide
│   ├── .gitignore                     # Git ignore rules
│   ├── bootstrap/                     # State management setup
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── modules/                       # Reusable modules
│   │   ├── api_gateway/              # API Gateway configuration
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── cloudwatch/               # Monitoring and logging
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── dynamodb/                 # Tool metadata storage
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── iam/                      # IAM roles and policies
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── lambda/                   # Lambda functions
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   ├── handler.py           # Placeholder Lambda code
│   │   │   └── placeholder.zip      # Deployment package
│   │   └── s3/                       # Code artifact storage
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── outputs.tf
│   └── environments/                  # Environment configs
│       ├── dev.tfvars
│       ├── dev-backend.hcl
│       ├── staging.tfvars
│       ├── staging-backend.hcl
│       ├── prod.tfvars
│       └── prod-backend.hcl
└── PROJECT_STRUCTURE.md              # This file
```

## Infrastructure Components

### AWS Services Configured

1. **DynamoDB** - Tool metadata storage with GSI for agent and code hash lookups
2. **S3** - Code artifact storage with versioning and lifecycle policies
3. **Lambda** - Three functions (Tool Manager, Authorizer, Monitoring) using Python 3.12
4. **API Gateway** - HTTP API with custom authorizer and CORS support
5. **IAM** - Roles and policies for secure service communication
6. **CloudWatch** - Logging, metrics, alarms, and dashboards

### Key Features

- **State Management**: S3 backend with DynamoDB locking
- **Multi-Environment**: Separate configs for dev, staging, and prod
- **Security**: Encryption at rest, least privilege IAM, public access blocked
- **Monitoring**: CloudWatch logs, metrics, alarms, and dashboards
- **Cost Optimization**: On-demand billing, lifecycle policies, appropriate sizing

## Next Steps

After infrastructure setup, the following components need to be implemented:

1. Lambda function code (Task 2-8)
2. Data models and interfaces
3. Code validation system
4. AgentCore integration
5. Monitoring and observability

See `.kiro/specs/dynamic-tool-runtime/tasks.md` for the complete implementation plan.
