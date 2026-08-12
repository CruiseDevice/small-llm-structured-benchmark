#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${1:-youruser/small-llm-benchmark}"
TAG="${TAG:-latest}"
FULL_TAG="${IMAGE_NAME}:${TAG}"

echo "============================================"
echo " Building: ${FULL_TAG}"
echo " Platform: linux/amd64 (for Vast.ai / RunPod)"
echo "============================================"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

docker buildx build \
    --platform linux/amd64 \
    --progress=plain \
    -t "$FULL_TAG" \
    --load \
    .

echo ""
echo "✅ Built: ${FULL_TAG}"
echo "   Size: $(docker image inspect "$FULL_TAG" --format='{{.Size}}' | awk '{printf "%.1f GB\n", $1/1024/1024/1024}')"

if [ -z "${SKIP_PUSH:-}" ]; then
    echo ""
    echo "Pushing to registry..."
    docker push "$FULL_TAG"
    echo "✅ Pushed: ${FULL_TAG}"
else
    echo "⏭️  Skipping push (SKIP_PUSH=1)"
fi

echo ""
echo "============================================"
echo " Usage:"
echo "   RunPod:  Use '${FULL_TAG}' as custom image"
echo "   Vast.ai: Set image to '${FULL_TAG}'"
echo "============================================"
