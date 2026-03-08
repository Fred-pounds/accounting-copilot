#!/bin/bash
# Build only the missing Lambda deployment packages

set -e

PROJECT_NAME="accounting-copilot"
PACKAGE_DIR="lambda-packages"

echo "Building missing Lambda deployment packages..."

mkdir -p "${PACKAGE_DIR}"

# List of missing Lambda functions
FUNCTIONS=(
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
    rm -rf "${FUNC_DIR}"
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
echo "Missing Lambda packages built successfully!"
echo "Total packages:"
ls -lh "${PACKAGE_DIR}"/*.zip | wc -l
