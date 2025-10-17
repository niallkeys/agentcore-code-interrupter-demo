.PHONY: help bootstrap-dev bootstrap-staging bootstrap-prod init-dev init-staging init-prod plan-dev plan-staging plan-prod apply-dev apply-staging apply-prod destroy-dev destroy-staging destroy-prod

help:
	@echo "Dynamic Tool Runtime - Terraform Commands"
	@echo ""
	@echo "Bootstrap (first time only):"
	@echo "  make bootstrap-dev       - Create state management for dev"
	@echo "  make bootstrap-staging   - Create state management for staging"
	@echo "  make bootstrap-prod      - Create state management for prod"
	@echo ""
	@echo "Infrastructure deployment:"
	@echo "  make init-dev            - Initialize Terraform for dev"
	@echo "  make plan-dev            - Plan infrastructure changes for dev"
	@echo "  make apply-dev           - Apply infrastructure changes for dev"
	@echo "  make destroy-dev         - Destroy dev infrastructure"
	@echo ""
	@echo "Replace 'dev' with 'staging' or 'prod' for other environments"

# Bootstrap commands
bootstrap-dev:
	cd bootstrap && \
	terraform init && \
	terraform apply \
		-var="environment=dev" \
		-var="state_bucket_name=dynamic-tool-runtime-tfstate-dev" \
		-var="lock_table_name=dynamic-tool-runtime-tflock-dev"

bootstrap-staging:
	cd bootstrap && \
	terraform init && \
	terraform apply \
		-var="environment=staging" \
		-var="state_bucket_name=dynamic-tool-runtime-tfstate-staging" \
		-var="lock_table_name=dynamic-tool-runtime-tflock-staging"

bootstrap-prod:
	cd bootstrap && \
	terraform init && \
	terraform apply \
		-var="environment=prod" \
		-var="state_bucket_name=dynamic-tool-runtime-tfstate-prod" \
		-var="lock_table_name=dynamic-tool-runtime-tflock-prod"

# Dev environment
init-dev:
	terraform init -backend-config=environments/dev-backend.hcl

plan-dev: init-dev
	terraform plan -var-file=environments/dev.tfvars

apply-dev: init-dev
	terraform apply -var-file=environments/dev.tfvars

destroy-dev: init-dev
	terraform destroy -var-file=environments/dev.tfvars

# Staging environment
init-staging:
	terraform init -backend-config=environments/staging-backend.hcl -reconfigure

plan-staging: init-staging
	terraform plan -var-file=environments/staging.tfvars

apply-staging: init-staging
	terraform apply -var-file=environments/staging.tfvars

destroy-staging: init-staging
	terraform destroy -var-file=environments/staging.tfvars

# Prod environment
init-prod:
	terraform init -backend-config=environments/prod-backend.hcl -reconfigure

plan-prod: init-prod
	terraform plan -var-file=environments/prod.tfvars

apply-prod: init-prod
	terraform apply -var-file=environments/prod.tfvars

destroy-prod: init-prod
	terraform destroy -var-file=environments/prod.tfvars
