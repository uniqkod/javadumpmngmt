# NFS Mount Manager

Custom container image with NFS client utilities pre-installed for managing NFS mounts on Kubernetes/OpenShift nodes.

## Overview

This image is based on Red Hat UBI 9 and includes all necessary NFS utilities to mount NFS shares on host nodes without runtime package installation.

## Included Packages

- **nfs-utils**: NFS client utilities (mount.nfs, showmount, etc.)
- **util-linux**: Mount/unmount utilities (mountpoint, etc.)
- **procps-ng**: Process utilities (ps, etc.)
- **iproute**: Network utilities (ip, etc.)

## Build

### Local Build with Podman/Docker

```bash
cd apps/nfs-mount-manager
podman build -t nfs-mount-manager:1.0.0 .
```

### OpenShift BuildConfig

```bash
# Create ImageStream
oc apply -f openshift/buildconfigs/nfs-mount-manager-is.yaml

# Create BuildConfig
oc apply -f openshift/buildconfigs/nfs-mount-manager-bc.yaml

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

# Push to registry
podman push quay.io/yourorg/nfs-mount-manager:1.0.0
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
        image: image-registry.openshift-image-registry.svc:5000/heapdump/nfs-mount-manager:latest
        # Or external registry
        # image: quay.io/yourorg/nfs-mount-manager:1.0.0
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
```

## Benefits

✅ **No Runtime Installation**: NFS utils pre-installed, faster pod startup  
✅ **Offline Compatible**: Works without package repository access  
✅ **Immutable**: Consistent image across all deployments  
✅ **Scannable**: Can be scanned for vulnerabilities  
✅ **Cacheable**: Image layers cached, faster deployments  
✅ **Reliable**: No dependency on external package repos  

## Image Size

Approximate size: ~250MB (compressed)

## Updates

To update packages:

1. Edit `Dockerfile`
2. Rebuild image
3. Push to registry
4. Restart StatefulSet pods

## Security

- Based on Red Hat UBI 9 (enterprise-grade base)
- Only necessary packages installed
- Regular security updates via base image
- No unnecessary tools or shells

## License

Inherits license from Red Hat UBI (freely redistributable)

## See Also

- [NFS Mount StatefulSet](../../k8s/dump-volume-manager/nfs-mount-statefulset.yaml)
- [BuildConfig](../../openshift/buildconfigs/nfs-mount-manager-bc.yaml)
- [NFS Bidirectional Solution](../../docs/NFS_BIDIRECTIONAL_SOLUTION.md)
