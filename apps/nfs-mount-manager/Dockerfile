# NFS Mount Manager Container Image

FROM registry.access.redhat.com/ubi9/ubi:latest

# Install NFS client utilities and required tools
RUN dnf install -y \
    nfs-utils \
    util-linux \
    procps-ng \
    iproute \
    && dnf clean all \
    && rm -rf /var/cache/dnf

# Verify NFS utilities are installed
RUN mount.nfs -V && \
    mountpoint -V

# Create mount point directory
RUN mkdir -p /mnt/nfs-dump

LABEL name="nfs-mount-manager" \
      vendor="Custom" \
      version="1.0.0" \
      summary="NFS mount manager with pre-installed NFS utilities" \
      description="Container for managing NFS mounts on Kubernetes/OpenShift nodes. \
                   Includes nfs-utils, util-linux for mount operations."

# Default command (will be overridden by StatefulSet)
CMD ["/bin/bash"]
