#!/bin/bash
set -e

echo "📦 Building Google API Lambda Layer..."

cd terraform/layers
rm -rf google-api/python
mkdir -p google-api/python

# Use Docker to build in a Lambda-like environment (Amazon Linux 2 / Python 3.12)
echo "🐳 Running pip install in Docker..."
docker run --rm -v $(pwd):/var/task public.ecr.aws/sam/build-python3.12:latest \
    pip install -r /var/task/google-api/requirements.txt -t /var/task/google-api/python/

echo "✅ Layer build complete."
