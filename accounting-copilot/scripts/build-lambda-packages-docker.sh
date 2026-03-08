#!/bin/bash
# Build all Lambda packages using Docker for AWS Lambda compatibility

set -e

PACKAGE_DIR="lambda-packages"
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

echo "Building Lambda packages using Docker (AWS Lambda Python 3.11 image)..."
echo "This ensures GLIBC compatibility with AWS Lambda runtime"
echo ""

# Create package directory
mkdir -p "${PACKAGE_DIR}"

# Build each function
for FUNCTION in "${FUNCTIONS[@]}"; do
    echo "Building ${FUNCTION}..."
    
    FUNC_DIR="${PACKAGE_DIR}/${FUNCTION}"
    
    # Create temp directory
    mkdir -p "${FUNC_DIR}"
    
    # Copy shared code
    cp -r src/shared "${FUNC_DIR}/"
    
    # Copy function code
    cp src/lambdas/${FUNCTION}/handler.py "${FUNC_DIR}/"
    
    # Copy requirements
    cp requirements.txt "${FUNC_DIR}/"
    
    # Build using Lambda Docker image
    docker run --rm \
        -v "$(pwd)/${FUNC_DIR}:/var/task" \
        public.ecr.aws/lambda/python:3.11 \
        bash -c "pip install -r /var/task/requirements.txt -t /var/task/ --no-cache-dir && rm /var/task/requirements.txt"
    
    # Create zip
    cd "${FUNC_DIR}"
    zip -r "../${FUNCTION}.zip" . -q
    cd - > /dev/null
    
    # Clean up temp directory
    rm -rf "${FUNC_DIR}"
    
    # Get file size
    SIZE=$(du -h "${PACKAGE_DIR}/${FUNCTION}.zip" | cut -f1)
    echo "✓ ${FUNCTION}.zip created (${SIZE})"
    echo ""
done

echo "All Lambda packages built successfully!"
echo "Packages location: ${PACKAGE_DIR}/"
ls -lh ${PACKAGE_DIR}/*.zip
