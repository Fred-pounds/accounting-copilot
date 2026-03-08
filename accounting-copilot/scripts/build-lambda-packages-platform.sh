#!/bin/bash
# Build Lambda deployment packages with correct platform compatibility

set -e

PROJECT_NAME="accounting-copilot"
PACKAGE_DIR="lambda-packages"

echo "Building Lambda deployment packages for ${PROJECT_NAME} with platform compatibility..."

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
    "transaction_api"
    "document_api"
    "audit_trail_api"
    "approval_manager"
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
    
    # Install dependencies with Lambda-compatible platform
    echo "  Installing dependencies for Lambda platform..."
    pip install -r requirements.txt -t "${FUNC_DIR}/" \
        --quiet \
        --upgrade \
        --platform manylinux2014_x86_64 \
        --implementation cp \
        --python-version 3.11 \
        --only-binary=:all: \
        --target "${FUNC_DIR}/"
    
    # Create zip file
    cd "${FUNC_DIR}"
    zip -r "../${FUNCTION}.zip" . -q
    cd - > /dev/null
    
    # Clean up extracted directory
    rm -rf "${FUNC_DIR}"
    
    # Get zip size
    SIZE=$(du -h "${PACKAGE_DIR}/${FUNCTION}.zip" | cut -f1)
    echo "✓ ${FUNCTION}.zip created (${SIZE})"
done

echo ""
echo "All Lambda packages built successfully with platform compatibility!"
echo "Packages location: ${PACKAGE_DIR}/"
ls -lh "${PACKAGE_DIR}"/*.zip
