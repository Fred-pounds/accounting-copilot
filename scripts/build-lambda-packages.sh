#!/bin/bash
# Build Lambda deployment packages
# This script creates deployment packages for all Lambda functions

set -e

PROJECT_NAME="accounting-copilot"
PACKAGE_DIR="lambda-packages"

echo "Building Lambda deployment packages for ${PROJECT_NAME}..."

# Clean previous packages
rm -rf "${PACKAGE_DIR}"
mkdir -p "${PACKAGE_DIR}"

# List of Lambda functions
FUNCTIONS=(
    "document_upload_handler"
    "ocr_processor"
    "transaction_classifier"
    "data_validator"
    "reconciliation_engine"
    "dashboard_api"
    "financial_assistant"
    "audit_logger"
)

# Build each function package
for FUNCTION in "${FUNCTIONS[@]}"; do
    echo "Building ${FUNCTION}..."
    
    # Create function package directory
    FUNC_DIR="${PACKAGE_DIR}/${FUNCTION}"
    mkdir -p "${FUNC_DIR}"
    
    # Copy shared code
    if [ -d "src/shared" ]; then
        cp -r src/shared "${FUNC_DIR}/"
    fi
    
    # Copy function code
    if [ -f "src/lambdas/${FUNCTION}/handler.py" ]; then
        cp src/lambdas/${FUNCTION}/handler.py "${FUNC_DIR}/"
    else
        echo "Warning: handler.py not found for ${FUNCTION}"
        continue
    fi
    
    # Copy function-specific requirements if exists
    if [ -f "src/lambdas/${FUNCTION}/requirements.txt" ]; then
        pip install -r "src/lambdas/${FUNCTION}/requirements.txt" -t "${FUNC_DIR}/" --quiet --upgrade
    fi
    
    # Install common dependencies
    pip install -r requirements.txt -t "${FUNC_DIR}/" --quiet --upgrade
    
    # Create zip file
    cd "${FUNC_DIR}"
    zip -r "../${FUNCTION}.zip" . -q
    cd - > /dev/null
    
    # Get zip size
    SIZE=$(du -h "${PACKAGE_DIR}/${FUNCTION}.zip" | cut -f1)
    echo "✓ ${FUNCTION}.zip created (${SIZE})"
done

echo ""
echo "All Lambda packages built successfully!"
echo "Packages location: ${PACKAGE_DIR}/"
ls -lh "${PACKAGE_DIR}"/*.zip
