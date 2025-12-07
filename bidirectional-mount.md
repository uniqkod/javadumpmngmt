# Bidirectional Mount in Kubernetes

## Overview

This document explains the purpose and implementation of bidirectional mount propagation in the memory leak demo application's volume management strategy.

## What is Bidirectional Mount Propagation?

Bidirectional mount propagation is a Kubernetes volume mount feature that allows mount events to propagate in both directions between the host and the container:

- **Host → Container**: Mounts created on the host are visible inside the container
- **Container → Host**: Mounts created inside the container are visible on the host

## Why Do We Need It?

In our memory leak demo application, we use bidirectional mount propagation for the following reasons:

### 1. **Dynamic Volume Management**
The DaemonSet can dynamically manage storage on each Kubernetes node without requiring pre-configured volumes or storage classes.

### 2. **Cross-Pod Visibility**
Multiple pods across different nodes can share and access heap dumps through a consistent host path (`/mnt/dump`).

### 3. **Persistent Storage With PVC**
Uses a PersistentVolumeClaim (10Gi) backed by the default storage class, then bind-mounts it to the host path `/mnt/dump` for easy access and persistence.

### 4. **Host-Level Access**
Administrators can directly access heap dumps on the host without needing `kubectl cp` commands:
```bash
# Direct access on the node
ls -lh /mnt/dump/memory-leak-demo/
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Kubernetes Node                          │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │       PersistentVolume (10Gi - Default StorageClass)        │ │
│  │                                                              │ │
│  │              PersistentVolumeClaim: dump-storage-pvc        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│                              │ Mounted to                        │
│                              ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              DaemonSet: dump-volume-manager                 │ │
│  │                                                              │ │
│  │  Container: volume-manager                                  │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │  Volume Mounts:                                        │ │ │
│  │  │  1. PVC → /pv-storage                                 │ │ │
│  │  │  2. /mnt → /host/mnt (Bidirectional)                 │ │ │
│  │  │                                                         │ │ │
│  │  │  Actions:                                              │ │ │
│  │  │  - Creates: /host/mnt/dump                            │ │ │
│  │  │  - Bind mount: /pv-storage → /host/mnt/dump          │ │ │
│  │  │  - Sets permissions: 777                              │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│                              │ Bidirectional                      │
│                              │ Propagation                        │
│                              ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Host Filesystem                          │ │
│  │                                                              │ │
│  │              /mnt/dump/ (backed by PV)                      │ │
│  │              └── memory-leak-demo/                          │ │
│  │                  ├── heap_dump.hprof                        │ │
│  │                  └── gc.log                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ▲                                    │
│                              │ HostPath                          │
│                              │ Mount                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         Deployment: memory-leak-app                         │ │
│  │                                                              │ │
│  │  Container: memory-leak-app                                 │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │  Mount: /dumps → /mnt/dump/memory-leak-demo (HostPath)│ │ │
│  │  │                                                         │ │ │
│  │  │  - Writes: heap_dump.hprof                            │ │ │
│  │  │  - Writes: gc.log                                     │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Details

### DaemonSet Configuration

```yaml
# PersistentVolumeClaim for 10Gi storage
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dump-storage-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: ""  # Uses default storage class

---
# DaemonSet configuration
volumeMounts:
- name: host-mnt
  mountPath: /host/mnt
  mountPropagation: Bidirectional  # Key setting for bidirectional propagation
- name: pv-storage
  mountPath: /pv-storage  # PVC mounted here

volumes:
- name: host-mnt
  hostPath:
    path: /mnt
    type: DirectoryOrCreate
- name: pv-storage
  persistentVolumeClaim:
    claimName: dump-storage-pvc  # 10Gi PVC
```

### Mount Propagation Types

Kubernetes supports three mount propagation modes:

| Mode | Host → Container | Container → Host | Use Case |
|------|------------------|------------------|----------|
| **None** | ❌ No | ❌ No | Isolated mounts |
| **HostToContainer** | ✅ Yes | ❌ No | Read host mounts (default) |
| **Bidirectional** | ✅ Yes | ✅ Yes | Dynamic volume management |

### Security Considerations

Bidirectional mount propagation requires:

1. **Privileged Container**
   ```yaml
   securityContext:
     privileged: true
   ```

2. **Host Access**
   - `hostNetwork: true` - Access to host network namespace
   - `hostPID: true` - Access to host process namespace

3. **Tolerations**
   - Allows DaemonSet to run on all nodes including control plane

## Benefits in Our Use Case

### 1. **Simplified Deployment**
Uses default storage class - works on any Kubernetes cluster without custom storage configuration.

### 2. **Persistent Storage**
10Gi PersistentVolume ensures heap dumps survive pod restarts and have dedicated storage space.

### 3. **Guaranteed Startup Order**
PriorityClass ensures DaemonSet runs first, and init containers ensure application waits for storage readiness. See [pod-priority.md](pod-priority.md) for details.

### 4. **Automatic Cleanup**
DaemonSet ensures `/mnt/dump` exists and has correct permissions on every node.

### 5. **Debugging Efficiency**
Multiple access methods:
- Via kubectl: `kubectl cp`
- Via host: Direct file access on the node
- Via shared volume: Other pods can mount the same path

### 6. **Multi-Application Support**
Other applications can use subdirectories under `/mnt/dump/`:
```
/mnt/dump/
├── memory-leak-demo/
│   └── heap_dump.hprof
├── app-one/
│   └── dumps/
└── app-two/
    └── diagnostics/
```

## Usage Instructions

### Deploy the DaemonSet
```bash
# Deploy DaemonSet first to prepare the host directories
kubectl apply -f daemonset-volume.yaml

# This creates:
# - PriorityClass: dump-volume-critical (priority: 1,000,000)
# - PersistentVolumeClaim: dump-storage-pvc (10Gi)
# - DaemonSet: dump-volume-manager

# Verify DaemonSet is running on all nodes
kubectl get priorityclass dump-volume-critical
kubectl get pvc -n memory-leak-demo
kubectl get daemonset -n memory-leak-demo
kubectl get pods -n memory-leak-demo -l app=dump-volume-manager

# Check DaemonSet is ready (should show READY 1/1)
kubectl get pods -n memory-leak-demo -l app=dump-volume-manager -o wide
```

### Deploy the Application
```bash
# Deploy the memory leak application
kubectl apply -f deployment.yaml

# The app will:
# 1. Start with init container
# 2. Wait for /mnt/dump/.ready file (created by DaemonSet)
# 3. Once ready, start main container
# 4. Write heap dumps to /mnt/dump/memory-leak-demo/

# Watch init container wait for DaemonSet
kubectl logs -n memory-leak-demo -l app=memory-leak-app -c wait-for-volume-manager -f

# Once init completes, watch application
kubectl logs -n memory-leak-demo -l app=memory-leak-app -f
```

### Access Heap Dumps

**Method 1: Via kubectl**
```bash
POD_NAME=$(kubectl get pod -n memory-leak-demo -l app=memory-leak-app -o jsonpath='{.items[0].metadata.name}')
kubectl cp -n memory-leak-demo $POD_NAME:/dumps/heap_dump.hprof ./heap_dump.hprof
```

**Method 2: Direct host access**
```bash
# SSH to the Kubernetes node
ssh node-hostname

# Access dumps directly
ls -lh /mnt/dump/memory-leak-demo/
cp /mnt/dump/memory-leak-demo/heap_dump.hprof /tmp/
```

**Method 3: Via debug pod**
```bash
kubectl run -it --rm debug \
  --image=busybox \
  --restart=Never \
  -n memory-leak-demo \
  --overrides='
{
  "spec": {
    "containers": [{
      "name": "debug",
      "image": "busybox",
      "stdin": true,
      "tty": true,
      "volumeMounts": [{
        "name": "dumps",
        "mountPath": "/dumps"
      }]
    }],
    "volumes": [{
      "name": "dumps",
      "hostPath": {
        "path": "/mnt/dump"
      }
    }]
  }
}' \
  -- sh -c "ls -lh /dumps/memory-leak-demo/"
```

## Troubleshooting

### Check Mount Propagation
```bash
# Inside the DaemonSet pod
kubectl exec -n memory-leak-demo daemonset/dump-volume-manager -- \
  cat /proc/self/mountinfo | grep /host/mnt
```

### Verify Directory Permissions
```bash
kubectl exec -n memory-leak-demo daemonset/dump-volume-manager -- \
  ls -la /host/mnt/dump
```

### Check Available Space
```bash
kubectl exec -n memory-leak-demo daemonset/dump-volume-manager -- \
  df -h /host/mnt/dump
```

### View DaemonSet Logs
```bash
kubectl logs -n memory-leak-demo daemonset/dump-volume-manager
```

Expected output:
```
Starting dump volume manager...
Mounting PV to host /mnt/dump...
PV is mounted at /pv-storage
Creating bind mount to /host/mnt/dump...
Bind mount created successfully
Permissions set to 777
Available space on /mnt/dump:
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb        10G   0     10G   0% /host/mnt/dump
Mount information:
/dev/sdb on /host/mnt/dump type ext4 (rw,relatime)
Volume manager running. Keeping pod alive...
```

### Verify Priority and Readiness
```bash
# Check pod priority
kubectl get pod -n memory-leak-demo -o custom-columns=NAME:.metadata.name,PRIORITY:.spec.priority,READY:.status.conditions[?\(@.type==\"Ready\"\)].status

# Verify .ready marker file exists
kubectl exec -n memory-leak-demo daemonset/dump-volume-manager -- \
  cat /host/mnt/dump/.ready
```

## Limitations and Considerations

### 1. **Node-Specific Storage**
Heap dumps are stored on the node where the pod runs. If the pod moves to another node, previous dumps won't be accessible unless manually copied.

### 2. **Disk Space Management**
The PersistentVolume provides 10Gi of dedicated storage. Monitor disk usage:
```bash
kubectl exec -n memory-leak-demo daemonset/dump-volume-manager -- \
  df -h /host/mnt/dump
```

If more space is needed, update the PVC:
```bash
kubectl edit pvc dump-storage-pvc -n memory-leak-demo
# Change storage: 10Gi to storage: 20Gi
```

### 3. **Security Implications**
Privileged containers and host path mounts increase security risks. Use only in controlled environments.

### 4. **Cluster Policies**
Some Kubernetes clusters (GKE Autopilot, managed services) may restrict:
- Privileged containers
- Host path volumes
- Bidirectional mount propagation

### 5. **Cleanup Required**
Heap dumps persist on the host after pod deletion. Manual cleanup may be needed:
```bash
# On the host or via DaemonSet
rm -rf /mnt/dump/memory-leak-demo/*
```

## Current Implementation vs Alternatives

### Current: PersistentVolume + Bidirectional Mount (Implemented)
**Pros**: 
- Standard Kubernetes storage approach
- Dedicated 10Gi storage space
- Works with default storage class
- Accessible via host path for easy debugging
**Cons**: 
- Requires privileged DaemonSet for bind mount
- Slightly more complex setup

### emptyDir
**Pros**: Simple, no host access needed
**Cons**: Data lost when pod is deleted

### Network Storage (NFS, Ceph)
**Pros**: Shared across all nodes
**Cons**: Network overhead, additional infrastructure

### Cloud Storage (S3, GCS)
**Pros**: Unlimited storage, accessible from anywhere
**Cons**: Requires code changes to upload dumps, egress costs

## Conclusion

This implementation combines the best of both worlds:
- **PersistentVolume**: Provides reliable, dedicated storage (10Gi) backed by Kubernetes storage infrastructure
- **Bidirectional Mount**: Enables easy host-level access at `/mnt/dump` for debugging and administration

The solution is ideal for development/testing environments where you need:
- Persistent heap dump storage
- Easy access for analysis
- Flexibility for multiple access methods

For production environments, consider additional features like:
- Automated upload to object storage (S3, GCS)
- Retention policies and cleanup automation
- Integration with observability platforms
- Encrypted storage volumes

---

**Last Updated**: 2025-12-07T19:33:36.130Z  
**Author**: Generated for memory-leak-demo project  
**Storage**: 10Gi PersistentVolume using default StorageClass  
**Priority**: DaemonSet priority 1,000,000 with init container dependency  
**Related Files**: 
- `daemonset-volume.yaml` - PriorityClass, PVC, and DaemonSet configuration
- `deployment.yaml` - Application deployment with init container and hostPath mount
- `pod-priority.md` - Detailed explanation of priority and startup ordering
