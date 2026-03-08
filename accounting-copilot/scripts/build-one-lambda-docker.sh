#!/bin/bash
# Build a single Lambda package using Docker for correct platform

FUNCTION=$1

if [ -z "$FUNCTION" ]; then
    echo "Usage: $0 <function_name>"
    exit 1
fi

PACKAGE_DIR="lambda-packages"
FUNC_DIR="${PACKAGE_DIR}/${FUNCTION}"

echo "Building ${FUNCTION} using Docker..."

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

# Clean up
rm -rf "${FUNC_DIR}"

echo "✓ ${FUNCTION}.zip created"
