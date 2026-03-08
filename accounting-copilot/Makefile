# Makefile for AI Accounting Copilot

.PHONY: help install test lint format clean deploy-infra destroy-infra build-lambdas deploy-lambdas deploy-frontend deploy-all

help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install         - Install Python dependencies"
	@echo "  make test            - Run all tests"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make test-props      - Run property-based tests"
	@echo "  make lint            - Run linters"
	@echo "  make format          - Format code with black"
	@echo "  make clean           - Clean build artifacts"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy-infra    - Deploy infrastructure with Terraform"
	@echo "  make build-lambdas   - Build Lambda deployment packages"
	@echo "  make deploy-lambdas  - Deploy Lambda functions to AWS"
	@echo "  make deploy-frontend - Deploy frontend to S3/CloudFront"
	@echo "  make deploy-all      - Deploy everything (infra + lambdas + frontend)"
	@echo "  make destroy-infra   - Destroy infrastructure"
	@echo "  make validate-setup  - Validate deployment setup"
	@echo ""
	@echo "CI/CD:"
	@echo "  make ci-test         - Run tests in CI mode"
	@echo "  make ci-deploy       - Deploy in CI mode"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-props:
	pytest tests/properties/ -v

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/
	pylint src/
	mypy src/

format:
	black src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov/

deploy-infra:
	cd infrastructure && terraform init && terraform apply

destroy-infra:
	cd infrastructure && terraform destroy

plan-infra:
	cd infrastructure && terraform plan

build-lambdas:
	@echo "Building Lambda deployment packages..."
	./scripts/build-lambda-packages.sh

deploy-lambdas:
	@echo "Deploying Lambda functions..."
	./scripts/deploy-lambdas.sh

deploy-frontend:
	@echo "Deploying frontend..."
	cd frontend && ./deploy.sh

deploy-all:
	@echo "Deploying complete application..."
	./scripts/deploy-all.sh

ci-test:
	@echo "Running tests in CI mode..."
	pytest tests/ -v --tb=short --cov=src --cov-report=xml

ci-deploy:
	@echo "Deploying in CI mode..."
	./scripts/build-lambda-packages.sh
	./scripts/deploy-lambdas.sh

validate-setup:
	@echo "Validating deployment setup..."
	./scripts/validate-deployment-setup.sh
