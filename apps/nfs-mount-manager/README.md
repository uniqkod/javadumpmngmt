# NFS Mount Manager

Custom container image with NFS client utilities pre-installed for managing NFS mounts on Kubernetes/OpenShift nodes.

## Overview

This image includes all necessary NFS utilities to mount NFS shares on host nodes without runtime package installation.

## Base Image Options

We provide two Dockerfile variants:

### 1. Dockerfile (CentOS Stream 9) - **Recommended**
```dockerfile
FROM quay.io/centos/centos:stream9
```
- ✅ Free and open source
- ✅ RHEL-compatible
- ✅ nfs-utils in default repos
- ✅ Enterprise-ready
- Size: ~280MB

### 2. Dockerfile.fedora (Fedora 39) - **Alternative**
```dockerfile
FROM registry.fedoraproject.org/fedora:39
```
- ✅ Latest packages
- ✅ Excellent package availability
- ✅ Fast updates
- Size: ~300MB

## Why Not UBI?

Red Hat UBI 9 doesn't include `nfs-utils` in its default repositories (subscription required). CentOS Stream 9 provides the same packages freely without subscription.

## Included Packages

- **nfs-utils**: NFS client utilities (mount.nfs, showmount, etc.)
- **util-linux**: Mount/unmount utilities (mountpoint, etc.)
- **procps-ng**: Process utilities (ps, etc.)
- **iproute**: Network utilities (ip, etc.)
- **findutils**: File utilities (find, etc.)

## Build

### Option 1: Using Build Script (Recommended)

```bash
cd apps/nfs-mount-manager

# Build with default (CentOS Stream)
./build.sh

# Or build with Fedora
./build.sh Dockerfile.fedora

# Set custom registry and version
IMAGE_NAME=nfs-mount-manager \
IMAGE_TAG=1.0.0 \
REGISTRY=quay.io/yourorg \
./build.sh
```

### Option 2: Manual Build with Podman/Docker

```bash
cd apps/nfs-mount-manager

# Build with CentOS Stream
podman build -t nfs-mount-manager:1.0.0 .

# Or build with Fedora
podman build -f Dockerfile.fedora -t nfs-mount-manager:1.0.0 .

# Test the image
podman run --rm nfs-mount-manager:1.0.0 mount.nfs -V
```

### Option 3: OpenShift BuildConfig

```bash
# Create ImageStream
oc apply -f ../../openshift/buildconfigs/nfs-mount-manager-is.yaml

# Create BuildConfig
oc apply -f ../../openshift/buildconfigs/nfs-mount-manager-bc.yaml

# Start build
oc start-build nfs-mount-manager

# Watch build logs
oc logs -f bc/nfs-mount-manager

# Check ImageStream
oc get is nfs-mount-manager
```

### Push to Registry

```bash
# Tag for registry
podman tag nfs-mount-manager:1.0.0 quay.io/yourorg/nfs-mount-manager:1.0.0
podman tag nfs-mount-manager:1.0.0 quay.io/yourorg/nfs-mount-manager:latest

# Login to registry
podman login quay.io

# Push to registry
podman push quay.io/yourorg/nfs-mount-manager:1.0.0
podman push quay.io/yourorg/nfs-mount-manager:latest
```

## Usage

Update the StatefulSet to use the custom image:

```yaml
# k8s/dump-volume-manager/nfs-mount-statefulset.yaml
spec:
  template:
    spec:
      containers:
      - name: nfs-mounter
        # OpenShift internal registry
        image: image-registry.openshift-image-registry.svc:5000/heapdump/nfs-mount-manager:latest
        
        # Or external registry
        # image: quay.io/yourorg/nfs-mount-manager:latest
```

## Verification

Verify NFS utilities are available in the image:

```bash
# Run interactive shell
podman run -it nfs-mount-manager:1.0.0 /bin/bash

# Check utilities
mount.nfs -V
mountpoint -V
showmount -h
rpm -qa | grep nfs-utils
```

## Troubleshooting

### Build Fails: "Unable to find a match: nfs-utils"

**Cause:** UBI images require Red Hat subscription for additional packages.

**Solution:** Use CentOS Stream or Fedora base images (included):
```bash
# Use CentOS Stream (default)
./build.sh

# Or use Fedora
./build.sh Dockerfile.fedora
```

### SSL/TLS Handshake Errors During Build

**Symptoms:**
```
Error: error creating build container: SSL handshake error
Failed to download metadata for repo 'fedora'
```

**Causes:**
- Corporate proxy/firewall intercepting SSL
- Outdated CA certificates on host
- Network security policies

**Solutions:**

**Option 1: Update CA certificates in Dockerfile (Already included)**
```dockerfile
RUN dnf install -y ca-certificates && dnf clean all
RUN update-ca-trust
```

**Option 2: Disable TLS verification (temporary workaround)**
```bash
NO_TLS_VERIFY=true ./build.sh
```

**Option 3: Configure proxy if behind corporate firewall**
```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1

# Build with proxy
podman build --build-arg HTTP_PROXY=$HTTP_PROXY \
             --build-arg HTTPS_PROXY=$HTTPS_PROXY \
             -f Dockerfile -t nfs-mount-manager:1.0.0 .
```

**Option 4: Use host's CA certificates**
```bash
# Mount host CA certs during build
podman build --volume /etc/pki/ca-trust:/etc/pki/ca-trust:ro \
             -f Dockerfile -t nfs-mount-manager:1.0.0 .
```

**Option 5: Use CentOS Stream instead of Fedora**
```bash
# CentOS Stream may have better SSL compatibility
./build.sh Dockerfile
```

### OpenShift Build Fails

Check BuildConfig is pointing to correct Dockerfile:
```bash
oc get bc nfs-mount-manager -o yaml | grep dockerfilePath
```

View build logs:
```bash
oc logs -f bc/nfs-mount-manager
```

### DNS Resolution Issues in Container

If the container can't resolve NFS server:
```bash
# Check DNS from within container
podman run --rm nfs-mount-manager:1.0.0 getent hosts nfs-server.heapdump.svc.cluster.local

# Add DNS servers to build if needed
podman build --dns 8.8.8.8 --dns 8.8.4.4 -f Dockerfile -t nfs-mount-manager:1.0.0 .
```

## Benefits

✅ **No Runtime Installation**: NFS utils pre-installed, faster pod startup  
✅ **Offline Compatible**: Works without package repository access  
✅ **Immutable**: Consistent image across all deployments  
✅ **Scannable**: Can be scanned for vulnerabilities  
✅ **Cacheable**: Image layers cached, faster deployments  
✅ **Reliable**: No dependency on external package repos during runtime  
✅ **No Subscription**: Uses freely available base images  

## Image Size

- CentOS Stream variant: ~280MB (compressed)
- Fedora variant: ~300MB (compressed)

## Updates

To update packages:

1. Edit `Dockerfile` or `Dockerfile.fedora`
2. Rebuild image: `./build.sh`
3. Push to registry
4. Restart StatefulSet pods

## Base Image Comparison

| Base Image | nfs-utils Available | Subscription | Size | Update Frequency |
|------------|-------------------|--------------|------|------------------|
| UBI 9 | ❌ No (requires subscription) | Required | ~220MB | Slow |
| CentOS Stream 9 | ✅ Yes | Not required | ~280MB | Regular |
| Fedora 39 | ✅ Yes | Not required | ~300MB | Fast |

## Security

- Based on enterprise-grade distributions
- Only necessary packages installed
- Regular security updates via base image
- Can be scanned with Trivy, Clair, etc.

## License

- CentOS Stream: Freely redistributable
- Fedora: Freely redistributable

## See Also

- [NFS Mount StatefulSet](../../k8s/dump-volume-manager/nfs-mount-statefulset.yaml)
- [BuildConfig](../../openshift/buildconfigs/nfs-mount-manager-bc.yaml)
- [NFS Bidirectional Solution](../../docs/NFS_BIDIRECTIONAL_SOLUTION.md)

