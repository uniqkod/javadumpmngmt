# NFS Mount Manager Container Image

# Use CentOS Stream 9 which has nfs-utils in default repos
# Alternative: registry.access.redhat.com/ubi9/ubi-init:latest
FROM quay.io/centos/centos:stream9

# Install CA certificates first to fix SSL issues
RUN dnf install -y ca-certificates && dnf clean all

# Update CA trust
RUN update-ca-trust

# Install NFS client utilities and required tools
RUN dnf install -y \
    nfs-utils \
    util-linux \
    procps-ng \
    iproute \
    findutils \
    && dnf clean all \
    && rm -rf /var/cache/dnf

# Verify NFS utilities are installed
RUN mount.nfs -V && \
    mountpoint -V && \
    echo "NFS utilities successfully installed"

# Create mount point directory
RUN mkdir -p /mnt/nfs-dump

LABEL name="nfs-mount-manager" \
      vendor="Custom" \
      version="1.0.0" \
      summary="NFS mount manager with pre-installed NFS utilities" \
      description="Container for managing NFS mounts on Kubernetes/OpenShift nodes. \
                   Based on CentOS Stream 9. Includes nfs-utils, util-linux for mount operations."

# Default command (will be overridden by StatefulSet)
CMD ["/bin/bash"]
