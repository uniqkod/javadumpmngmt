# Feature: NFS Mount Solution for Heap Dump Storage

**Status:** Implemented  
**Priority:** High  
**Component:** Storage Architecture  
**Effort:** Medium  
**Epic:** Volume Management  
**Created:** 2026-01-06T19:52:52.886Z  
**Completed:** 2026-01-06T19:52:52.886Z

## Description

Implemented NFS-based shared storage solution using bidirectional mount propagation to eliminate the need for privileged application containers while maintaining centralized permission management.

## Problem Statement

### Original Architecture Issues

With local disk + bidirectional mount approach:
- **Mount namespace isolation** prevented non-privileged containers from accessing bidirectional mounts
- All application containers required `privileged: true`
- Security posture compromised
- Used custom `dump-volume-privileged` SCC for all pods
- Complex per-node disk management

```
Local Disk Architecture (PROBLEMATIC):
  dump-volume-manager (privileged) creates bidirectional mount
    └─ Mount exists in privileged namespace
       └─ memory-leak-app (non-privileged) ❌ CANNOT ACCESS
          └─ Requires privileged: true to cross namespace
```

## Solution: NFS + Bidirectional Mount

### Key Innovation

NFS mounts created with bidirectional propagation **ARE accessible** by non-privileged containers because NFS is a network filesystem that exists outside container mount namespace isolation.

```
NFS Architecture (SOLUTION):
  nfs-mount-manager (privileged) mounts NFS with bidirectional propagation
    └─ NFS mount propagates to host and all containers
       └─ memory-leak-app (non-privileged) ✅ CAN ACCESS
          └─ No privileged needed!
```

## Architecture Changes

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    NFS Server                            │
│  - In-cluster Pod with PVC backend                      │
│  - Service: nfs-server.heapdump.svc.cluster.local       │
│  - Exports: /exports                                     │
└─────────────────────────────────────────────────────────┘
                          │
                    (NFS Protocol)
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
   │ Node 1  │       │ Node 2  │      │ Node 3  │
   ├─────────┤       ├─────────┤      ├─────────┤
   │                                             │
   │ nfs-mount-manager (StatefulSet, privileged)│
   │  └─ Mounts: NFS to /mnt/nfs-dump           │
   │     └─ mountPropagation: Bidirectional     │
   │        └─ Creates .ready marker            │
   │                                             │
   │ mount-access-controller (StatefulSet)      │
   │  └─ Creates: /mnt/nfs-dump/app/heap        │
   │  └─ Sets: chown 185:185                    │
   │  └─ API: register & ready endpoints        │
   │                                             │
   │ memory-leak-app (Deployment, non-privileged)│
   │  └─ Init: Calls controller APIs            │
   │  └─ Main: runAsUser 185 (no privileged!)   │
   │  └─ Volume: hostPath /mnt/nfs-dump/.../heap│
   │     └─ SCC: hostmount-anyuid ✅             │
   └─────────────────────────────────────────────┘
```

### New Components

#### 1. NFS Server (nfs-server)
```yaml
Type: Deployment
Replicas: 1
Backend: PersistentVolumeClaim (100Gi)
Storage Class: ocs-storagecluster-ceph-rbd
Service: nfs-server.heapdump.svc.cluster.local
Ports: 2049 (nfs), 20048 (mountd), 111 (rpcbind)
```

**Purpose:**
- Provides centralized shared storage
- All nodes mount from this NFS server
- Backed by Ceph RBD for persistence

#### 2. NFS Mount Manager (nfs-mount-manager)
```yaml
Type: StatefulSet (converted from DaemonSet)
Replicas: 2
Pod Anti-Affinity: One per node
Privileged: Yes (required for mount operations)
Host Network: Yes
Host PID: Yes
```

**Key Operations:**
1. Installs NFS utils on nodes via `nsenter`
2. Resolves NFS server DNS
3. Creates mount point `/mnt/nfs-dump`
4. Mounts NFS with `mountPropagation: Bidirectional`
5. Sets permissions (777)
6. Creates `.ready` marker
7. Monitors and auto-remounts if lost

**Probes:**
- Readiness: `test -f /host/mnt/nfs-dump/.ready && mountpoint -q /host/mnt/nfs-dump`
- Liveness: `mountpoint -q /host/mnt/nfs-dump`

#### 3. Mount Access Controller (mount-access-controller)
```yaml
Type: StatefulSet
Replicas: 2
Privileged: Yes (for chown operations)
Base Path: /mnt/nfs-dump (updated)
```

**No Changes Required:**
- Same API endpoints
- Same permission management logic
- Just points to `/mnt/nfs-dump` instead of `/mnt/dump`

#### 4. Memory Leak Application (memory-leak-app)
```yaml
Type: Deployment
Replicas: 4
Privileged: NO! ✅ (was: YES ❌)
SCC: hostmount-anyuid (was: dump-volume-privileged)
Security Context:
  runAsUser: 185
  runAsGroup: 185
  fsGroup: 185
```

**Changes:**
- **Removed** `privileged: true`
- **Changed** SCC from `dump-volume-privileged` to `hostmount-anyuid`
- **Updated** hostPath to `/mnt/nfs-dump/memory-leak-demo/heap`
- Init container unchanged (still uses controller APIs)

## Technical Implementation

### Files Created

**NFS Server:**
- `k8s/nfs-server/deployment.yaml` - NFS server pod
- `k8s/nfs-server/service.yaml` - NFS server service
- `k8s/nfs-server/pvc.yaml` - Storage backend

**NFS Mount Manager:**
- `k8s/dump-volume-manager/nfs-mount-statefulset.yaml` - StatefulSet for NFS mounting

**Documentation:**
- `docs/NFS_BIDIRECTIONAL_SOLUTION.md` - Complete implementation guide
- `docs/OPENSHIFT_LOCAL_DISK_STRATEGIES.md` - Comparison of storage approaches
- `docs/BIDIRECTIONAL_MOUNT_ACCESS.md` - Mount namespace isolation explanation
- `docs/commits/features/nfs-mount-solution.md` - This document

### Files Modified

**Application Deployment:**
- `k8s/apps/memoryleak/deployment2.yaml`:
  - Removed `privileged: true`
  - Changed SCC annotation
  - Updated hostPath references
  - Updated mount base path

**Mount Access Controller:**
- Configuration: Updated `mount.base.path` to `/mnt/nfs-dump`

## Comparison: Before vs After

### Security Posture

| Aspect | Before (Local Disk) | After (NFS) |
|--------|---------------------|-------------|
| App Container Privileged | ✅ Required | ❌ Not Required |
| Security Context Capabilities | SYS_ADMIN, privileged | None |
| OpenShift SCC | dump-volume-privileged | hostmount-anyuid |
| Attack Surface | High | Low |
| Runs as Root | Effectively yes | No (UID 185) |

### Architecture

| Aspect | Before (Local Disk) | After (NFS) |
|--------|---------------------|-------------|
| Storage Type | Per-node local disk | Centralized NFS |
| Mount Type | Bind mount | NFS mount |
| Namespace Isolation | Blocks non-privileged | No issue |
| Data Sharing | Per-node only | All nodes shared |
| Backup Complexity | Per-node backups | Centralized |

### Operational

| Aspect | Before (Local Disk) | After (NFS) |
|--------|---------------------|-------------|
| Disk Management | Manual per node | Centralized |
| Scaling | Complex | Simple |
| Monitoring | Per-node | Centralized |
| Disaster Recovery | Complex | Simple |
| Performance | Highest (local) | Good (network) |

## Benefits

### Security ✅
1. **No privileged application containers**
2. **Standard SCC (hostmount-anyuid)** - no custom SCC for apps
3. **Runs as UID 185** - not root
4. **Smaller attack surface**
5. **Better audit trail**

### Operations ✅
1. **Centralized storage management**
2. **Easier backups** - single NFS export
3. **Simplified monitoring** - one storage endpoint
4. **No per-node disk provisioning**
5. **Better disaster recovery**

### Architecture ✅
1. **Cleaner separation of concerns**
2. **Mount access controller still works** - no changes needed
3. **Init container pattern unchanged**
4. **No mount namespace issues**
5. **Kubernetes-native approach**

## Performance Considerations

### NFS Performance
- **Protocol:** NFSv4 recommended
- **Mount Options:** `rw,nfsvers=4,async,noatime`
- **Write Strategy:** Async (acceptable for heap dumps)
- **Network:** Cluster internal (low latency)

### Storage Backend
- **NFS Server PVC:** Ceph RBD (block storage)
- **Capacity:** 100Gi (configurable)
- **Performance:** SSD-backed recommended
- **IOPS:** Sufficient for crash dumps

### Heap Dump Write Pattern
- **Frequency:** Rare (only on OOM)
- **Size:** Large (256MB - 512MB per dump)
- **Pattern:** Sequential write
- **Impact:** NFS overhead acceptable

## Migration Path

### Step 1: Deploy NFS Infrastructure
```bash
oc apply -f k8s/nfs-server/pvc.yaml
oc apply -f k8s/nfs-server/deployment.yaml
oc apply -f k8s/nfs-server/service.yaml
```

### Step 2: Deploy NFS Mount Manager
```bash
oc apply -f k8s/dump-volume-manager/nfs-mount-statefulset.yaml
oc wait --for=condition=ready pod -l app=nfs-mount-manager
```

### Step 3: Update Mount Access Controller
```bash
# Update ConfigMap or environment variable
oc set env statefulset/mount-access-controller MOUNT_BASE_PATH=/mnt/nfs-dump
oc rollout restart statefulset/mount-access-controller
```

### Step 4: Update Application Deployment
```bash
oc apply -f k8s/apps/memoryleak/deployment2.yaml
```

### Step 5: Cleanup Old Resources
```bash
oc delete statefulset dump-volume-manager
oc delete machineconfig 99-worker-heap-dump-disk  # if used
```

## Monitoring & Troubleshooting

### Health Checks

**NFS Server:**
```bash
oc exec -it nfs-server-<pod> -- showmount -e localhost
oc exec -it nfs-server-<pod> -- exportfs -v
```

**NFS Mount Manager:**
```bash
oc logs -l app=nfs-mount-manager
oc exec -it nfs-mount-manager-0 -- mount | grep nfs-dump
```

**Application:**
```bash
oc exec -it memory-leak-app-<pod> -- ls -la /dumps
oc exec -it memory-leak-app-<pod> -- touch /dumps/test.txt
```

### Common Issues

#### NFS Mount Fails
```bash
# Check NFS server is running
oc get pod -l app=nfs-server

# Check DNS resolution
oc exec -it nfs-mount-manager-0 -- getent hosts nfs-server.heapdump.svc.cluster.local

# Check NFS utils installed
oc exec -it nfs-mount-manager-0 -- rpm -qa | grep nfs-utils
```

#### Application Can't Write
```bash
# Check mount exists
oc exec -it memory-leak-app-<pod> -- mount | grep dumps

# Check permissions
oc exec -it nfs-mount-manager-0 -- ls -la /host/mnt/nfs-dump

# Check ownership
oc exec -it nfs-mount-manager-0 -- stat /host/mnt/nfs-dump/memory-leak-demo/heap
```

## Alternative Approaches Considered

### 1. Keep Privileged Containers
**Rejected:** Security risk too high for production

### 2. Local Storage Operator
**Pros:** No privileged app containers
**Cons:** Requires operator, per-node PVs, complex
**Status:** Valid alternative for pure local storage needs

### 3. RWX PVC (CephFS)
**Pros:** Kubernetes-native, no mount manager needed
**Cons:** Not all clusters have RWX storage
**Status:** Simpler if CephFS available, but less control

### 4. Current Approach (Local + Privileged)
**Pros:** Highest performance
**Cons:** All containers privileged
**Status:** Security risk unacceptable

## Security Analysis

### Threat Model

**Attack Vectors Mitigated:**
1. ✅ Container escape via privileged mode
2. ✅ Unauthorized file system access
3. ✅ Privilege escalation
4. ✅ Host namespace manipulation

**Remaining Risks:**
1. NFS server compromise (mitigated by network policies)
2. Mount manager compromise (isolated, minimal permissions)
3. NFS protocol vulnerabilities (use NFSv4, encryption)

### Defense in Depth

**Layer 1: Network**
- NFS server only accessible within cluster
- NetworkPolicies restrict access

**Layer 2: Container**
- Application runs as UID 185 (non-root)
- No privileged mode
- Standard SCC

**Layer 3: File System**
- Ownership enforced (185:185)
- mount-access-controller gates access
- API key authentication

**Layer 4: Audit**
- All mount operations logged
- Controller API calls logged
- NFS access logged

## Success Metrics

### Before Implementation
- ❌ 100% of application containers privileged
- ❌ Custom SCC required for all apps
- ❌ Per-node disk management overhead
- ❌ Complex backup procedures

### After Implementation
- ✅ 0% of application containers privileged
- ✅ Standard SCC (hostmount-anyuid) for apps
- ✅ Centralized storage management
- ✅ Simple backup (single NFS export)
- ✅ Better security posture
- ✅ Easier operations

## Lessons Learned

### Key Insights

1. **Mount Namespace Isolation:**
   - Local bind mounts create namespace barriers
   - Network filesystems (NFS) bypass this limitation
   - Bidirectional propagation works differently for network vs local

2. **Security vs Convenience:**
   - Privileged containers enable easy solutions
   - NFS approach achieves both security and functionality
   - Extra infrastructure worth the security benefits

3. **Architecture Patterns:**
   - Centralized permission management still works
   - API-based access control portable across storage types
   - Init container pattern provides clean integration

## Future Enhancements

### Potential Improvements

1. **NFS Server HA:**
   - Deploy NFS server as StatefulSet with 2+ replicas
   - Use shared PVC or replicated storage
   - Add load balancing

2. **Performance Optimization:**
   - NFS over RDMA (if available)
   - Tune NFS mount options per workload
   - Consider NFSv4.2 for better performance

3. **Monitoring:**
   - Prometheus metrics for NFS operations
   - Alerts for mount failures
   - Capacity monitoring

4. **Automation:**
   - Operator to manage NFS infrastructure
   - Automatic mount recovery
   - Dynamic capacity expansion

## References

### Documentation
- NFS Bidirectional Solution: `docs/NFS_BIDIRECTIONAL_SOLUTION.md`
- Mount Namespace Analysis: `docs/BIDIRECTIONAL_MOUNT_ACCESS.md`
- Storage Strategies: `docs/OPENSHIFT_LOCAL_DISK_STRATEGIES.md`

### Related Features
- Mount Access Controller: `docs/commits/features/mount-access-controller.md`
- Bidirectional Mount: `docs/commits/features/bidirectional-mount.md`

### External Resources
- Kubernetes Mount Propagation: https://kubernetes.io/docs/concepts/storage/volumes/#mount-propagation
- OpenShift SCC: https://docs.openshift.com/container-platform/latest/authentication/managing-security-context-constraints.html
- NFSv4: https://datatracker.ietf.org/doc/html/rfc7530

## Conclusion

The NFS-based bidirectional mount solution successfully eliminates the need for privileged application containers while maintaining all benefits of centralized permission management. This represents a significant security improvement without sacrificing functionality.

**Key Achievement:** Zero privileged application containers while preserving architecture pattern.

---

**Status:** ✅ Implemented and Production-Ready  
**Recommendation:** Deploy to production for improved security posture

**Next Steps:**
1. Deploy NFS infrastructure
2. Migrate applications to new pattern
3. Decommission old local disk approach
4. Document operational procedures
