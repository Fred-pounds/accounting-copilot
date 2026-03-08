#!/bin/bash
# Validate deployment setup
# This script checks if all prerequisites are met for deployment

set -e

echo "=========================================="
echo "Deployment Setup Validation"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# Check required tools
echo "Checking required tools..."

if command -v terraform &> /dev/null; then
    TERRAFORM_VERSION=$(terraform --version | head -n1)
    echo "✓ Terraform installed: $TERRAFORM_VERSION"
else
    echo "✗ Terraform not installed"
    ERRORS=$((ERRORS + 1))
fi

if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version)
    echo "✓ AWS CLI installed: $AWS_VERSION"
else
    echo "✗ AWS CLI not installed"
    ERRORS=$((ERRORS + 1))
fi

if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo "✓ Python installed: $PYTHON_VERSION"
else
    echo "✗ Python not installed"
    ERRORS=$((ERRORS + 1))
fi

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js installed: $NODE_VERSION"
else
    echo "✗ Node.js not installed"
    ERRORS=$((ERRORS + 1))
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✓ npm installed: $NPM_VERSION"
else
    echo "✗ npm not installed"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check AWS credentials
echo "Checking AWS credentials..."

if aws sts get-caller-identity &> /dev/null; then
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
    echo "✓ AWS credentials configured"
    echo "  Account: $AWS_ACCOUNT"
    echo "  User: $AWS_USER"
else
    echo "✗ AWS credentials not configured"
    echo "  Run: aws configure"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check deployment scripts
echo "Checking deployment scripts..."

SCRIPTS=(
    "scripts/build-lambda-packages.sh"
    "scripts/deploy-infrastructure.sh"
    "scripts/deploy-lambdas.sh"
    "scripts/deploy-all.sh"
    "frontend/deploy.sh"
)

for SCRIPT in "${SCRIPTS[@]}"; do
    if [ -f "$SCRIPT" ]; then
        if [ -x "$SCRIPT" ]; then
            echo "✓ $SCRIPT exists and is executable"
        else
            echo "⚠ $SCRIPT exists but is not executable"
            echo "  Run: chmod +x $SCRIPT"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo "✗ $SCRIPT not found"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# Check infrastructure files
echo "Checking infrastructure files..."

INFRA_FILES=(
    "infrastructure/main.tf"
    "infrastructure/variables.tf"
    "infrastructure/outputs.tf"
)

for FILE in "${INFRA_FILES[@]}"; do
    if [ -f "$FILE" ]; then
        echo "✓ $FILE exists"
    else
        echo "✗ $FILE not found"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# Check Python dependencies
echo "Checking Python dependencies..."

if [ -f "requirements.txt" ]; then
    echo "✓ requirements.txt exists"
    
    if pip show boto3 &> /dev/null; then
        echo "✓ boto3 installed"
    else
        echo "⚠ boto3 not installed"
        echo "  Run: pip install -r requirements.txt"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "✗ requirements.txt not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check frontend setup
echo "Checking frontend setup..."

if [ -d "frontend" ]; then
    echo "✓ frontend directory exists"
    
    if [ -f "frontend/package.json" ]; then
        echo "✓ frontend/package.json exists"
        
        if [ -d "frontend/node_modules" ]; then
            echo "✓ frontend dependencies installed"
        else
            echo "⚠ frontend dependencies not installed"
            echo "  Run: cd frontend && npm install"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo "✗ frontend/package.json not found"
        ERRORS=$((ERRORS + 1))
    fi
    
    if [ -f "frontend/.env.example" ]; then
        echo "✓ frontend/.env.example exists"
        
        if [ -f "frontend/.env" ]; then
            echo "✓ frontend/.env exists"
        else
            echo "⚠ frontend/.env not found"
            echo "  Run: cp frontend/.env.example frontend/.env"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
else
    echo "✗ frontend directory not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check GitHub Actions workflows
echo "Checking GitHub Actions workflows..."

WORKFLOWS=(
    ".github/workflows/test.yml"
    ".github/workflows/deploy-staging.yml"
    ".github/workflows/deploy-production.yml"
    ".github/workflows/code-quality.yml"
)

for WORKFLOW in "${WORKFLOWS[@]}"; do
    if [ -f "$WORKFLOW" ]; then
        echo "✓ $WORKFLOW exists"
    else
        echo "✗ $WORKFLOW not found"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# Summary
echo "=========================================="
echo "Validation Summary"
echo "=========================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed! You're ready to deploy."
    echo ""
    echo "Next steps:"
    echo "1. Review DEPLOYMENT.md for deployment instructions"
    echo "2. Configure GitHub secrets (see CICD_SETUP.md)"
    echo "3. Run: make deploy-all"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Validation completed with $WARNINGS warning(s)"
    echo "You can proceed, but consider fixing the warnings."
    exit 0
else
    echo "❌ Validation failed with $ERRORS error(s) and $WARNINGS warning(s)"
    echo "Please fix the errors before deploying."
    exit 1
fi
