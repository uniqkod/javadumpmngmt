#!/bin/bash
# Build script for NFS mount manager image

set -e

IMAGE_NAME="${IMAGE_NAME:-nfs-mount-manager}"
IMAGE_TAG="${IMAGE_TAG:-1.0.0}"
REGISTRY="${REGISTRY:-quay.io/yourorg}"
NO_TLS_VERIFY="${NO_TLS_VERIFY:-false}"

echo "Building NFS Mount Manager Image"
echo "================================="
echo "Image: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
echo ""

# Choose Dockerfile
DOCKERFILE="${1:-Dockerfile}"

if [ ! -f "$DOCKERFILE" ]; then
    echo "Error: $DOCKERFILE not found"
    echo "Usage: $0 [Dockerfile|Dockerfile.fedora]"
    exit 1
fi

echo "Using: $DOCKERFILE"
echo ""

# Build flags
BUILD_FLAGS=""
if [ "$NO_TLS_VERIFY" = "true" ]; then
    echo "⚠️  TLS verification disabled"
    BUILD_FLAGS="--tls-verify=false"
fi

# Build image
echo "Building image..."
podman build $BUILD_FLAGS -f "$DOCKERFILE" -t "${IMAGE_NAME}:${IMAGE_TAG}" .

# Tag for registry
echo ""
echo "Tagging for registry..."
podman tag "${IMAGE_NAME}:${IMAGE_TAG}" "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
podman tag "${IMAGE_NAME}:${IMAGE_TAG}" "${REGISTRY}/${IMAGE_NAME}:latest"

# Test image
echo ""
echo "Testing image..."
podman run --rm "${IMAGE_NAME}:${IMAGE_TAG}" mount.nfs -V
podman run --rm "${IMAGE_NAME}:${IMAGE_TAG}" mountpoint -V

echo ""
echo "✅ Build successful!"
echo ""
echo "To push to registry:"
echo "  podman push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
echo "  podman push ${REGISTRY}/${IMAGE_NAME}:latest"
echo ""
echo "If you encounter TLS/SSL issues during build:"
echo "  NO_TLS_VERIFY=true ./build.sh"
echo ""
echo "To use in OpenShift:"
echo "  Update image in StatefulSet to: ${REGISTRY}/${IMAGE_NAME}:latest"

