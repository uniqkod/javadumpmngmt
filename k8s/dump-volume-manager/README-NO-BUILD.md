# NFS Mount Manager - No Custom Image Required
# Uses standard UBI Minimal image with runtime NFS installation on host

This solution works in restricted corporate environments by:
1. Using standard Red Hat UBI image (no custom build needed)
2. Installing NFS utils on the HOST node at runtime
3. No external registry or package repo access needed from build system

## How It Works

The StatefulSet uses a base UBI image and installs nfs-utils directly on the **OpenShift node** (not in the container) using `nsenter`.

## Deployment

```bash
# Just deploy - no build needed!
oc apply -f nfs-mount-hostinstall-statefulset.yaml
```

## What It Does

1. Starts with `registry.access.redhat.com/ubi9/ubi-minimal:latest` (always accessible)
2. Uses `nsenter` to run commands on the host node
3. Installs nfs-utils on the host using host's package manager
4. Mounts NFS on the host filesystem
5. Other pods access via hostPath

## Node Requirements

- OpenShift nodes must have access to Red Hat repos (they usually do)
- Nodes need `microdnf`, `dnf`, or `yum` available
- For CoreOS/RHCOS: uses `rpm-ostree` (may require node reboot)

## Advantages in Restricted Environments

✅ No custom image build required
✅ No external registry access needed
✅ Uses only Red Hat official images
✅ Works behind corporate firewall
✅ Package installation happens on node (has proper network access)

## Files

- `nfs-mount-hostinstall-statefulset.yaml` - StatefulSet that installs on host
- Uses: `registry.access.redhat.com/ubi9/ubi-minimal:latest`

## Comparison

| Approach | Custom Image | Network Access Needed | Works in Restricted Env |
|----------|--------------|----------------------|------------------------|
| Custom Image (Alpine/CentOS) | ✅ Required | Build system needs internet | ❌ No |
| Host Install (This) | ❌ Not needed | Only OpenShift nodes | ✅ Yes |

## Deploy

```bash
# Create ImageStream and StatefulSet
oc apply -f ../../openshift/buildconfigs/nfs-mount-manager-is.yaml
oc apply -f nfs-mount-hostinstall-statefulset.yaml

# Watch pods start
oc get pods -w -l app=nfs-mount-manager

# Check logs
oc logs -f nfs-mount-manager-0
```

## Verification

```bash
# Check if NFS is mounted on host
oc exec -it nfs-mount-manager-0 -- nsenter --target 1 --mount --uts --ipc --net --pid -- mount | grep nfs-dump

# Check NFS utils installed on host
oc exec -it nfs-mount-manager-0 -- nsenter --target 1 --mount --uts --ipc --net --pid -- rpm -qa | grep nfs-utils

# Check from application pod
oc exec -it memory-leak-app-xxx -- ls -la /dumps
```

## Limitations

**CoreOS/RHCOS nodes:** 
- Uses `rpm-ostree` which may require node reboot to activate
- Check with: `oc exec -it nfs-mount-manager-0 -- nsenter --target 1 --mount --uts --ipc --net --pid -- rpm-ostree status`

## Troubleshooting

If installation fails:
```bash
# Check what package manager is available
oc exec -it nfs-mount-manager-0 -- nsenter --target 1 --mount --uts --ipc --net --pid -- which microdnf dnf yum rpm-ostree

# Manual install test
oc exec -it nfs-mount-manager-0 -- nsenter --target 1 --mount --uts --ipc --net --pid -- microdnf install -y nfs-utils

# Check if already installed
oc exec -it nfs-mount-manager-0 -- nsenter --target 1 --mount --uts --ipc --net --pid -- rpm -qa | grep nfs
```

## Alternative: Pre-installed NFS on Nodes

If you can't install at runtime, ensure nodes have nfs-utils pre-installed via:
- MachineConfig (for CoreOS/RHCOS)
- Node configuration management (Ansible, etc.)

Then the StatefulSet will just use the existing installation.
