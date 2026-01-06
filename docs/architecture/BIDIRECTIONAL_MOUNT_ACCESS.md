# Bidirectional Mount Access Issue and Solutions

## The Problem

When a privileged pod creates a **bidirectional mount** (with `mountPropagation: Bidirectional`), non-privileged pods **cannot access** that mount through hostPath, even if:

- ✅ Directory exists on the host
- ✅ File ownership is correct (matching UID)
- ✅ Container runs as the correct UID
- ✅ SCC allows hostPath volumes

**Why?** This is a Linux kernel security feature related to **mount namespaces**. Bidirectional mounts created in privileged containers exist in a different mount namespace that non-privileged containers cannot see.

## Our Architecture

```
Node (each worker node has):
  │
  ├─ dump-volume-manager (privileged)
  │  └─ Creates: /mnt/dump (bidirectional mount from PVC)
  │     └─ mountPropagation: Bidirectional
  │
  ├─ mount-access-controller (privileged)  
  │  └─ Creates: /mnt/dump/memory-leak-demo/heap
  │  └─ Sets: chown 185:185
  │
  └─ memory-leak-app pods (non-privileged)
     └─ Tries to access: /mnt/dump/memory-leak-demo/heap
     └─ FAILS: Mount namespace isolation
```

## The Root Cause

### Bidirectional Mount Propagation

When `dump-volume-manager` creates the mount:
```yaml
volumeMounts:
  - name: host-mnt
    mountPath: /host/mnt
    mountPropagation: Bidirectional  # ← This is the issue
```

This mount exists in the **privileged container's mount namespace**. The kernel isolates this from unprivileged containers for security.

## Solutions

### ✅ Solution 1: Make Application Container Privileged (Recommended for This Use Case)

**Pros:**
- Simple, works immediately
- Allows access to bidirectional mounts
- Still runs as UID 185 (not root)
- File-level security maintained through UID

**Cons:**
- Container has elevated privileges
- Requires `dump-volume-privileged` SCC

**Implementation:**
```yaml
# deployment2.yaml
spec:
  template:
    metadata:
      annotations:
        openshift.io/scc: dump-volume-privileged
    spec:
      containers:
      - name: memory-leak-app-2
        securityContext:
          privileged: true
          runAsUser: 185      # Still runs as UID 185
          runAsGroup: 185
          fsGroup: 185
```

**Why This Works:**
- Privileged containers share the host's mount namespace
- Can see mounts created by other privileged containers
- Still protected by file ownership (UID 185)

---

### ⚠️ Solution 2: Change Mount Strategy (Not Recommended - Requires Architecture Change)

Remove bidirectional mount propagation from `dump-volume-manager`:

**Changes Required:**
1. Remove `mountPropagation: Bidirectional` from dump-volume-manager
2. Use regular hostPath mounts
3. Accept that mount won't propagate back to host

**Pros:**
- Non-privileged containers can access
- Better security isolation

**Cons:**
- **BREAKS EXISTING ARCHITECTURE**
- S3 uploader might not see files
- Other monitoring tools won't work
- Defeats purpose of bidirectional mount

---

### ⚠️ Solution 3: Use Shared Volume Instead of HostPath (Major Refactor)

Use PersistentVolumeClaim directly instead of hostPath:

**Architecture:**
```yaml
# All pods mount the same PVC
volumeClaimTemplates:
  - metadata:
      name: shared-dumps
    spec:
      accessModes: [ "ReadWriteMany" ]  # Requires RWX storage
      storageClassName: ocs-storagecluster-cephfs  # CephFS, not RBD
```

**Pros:**
- No privileged containers needed
- No mount namespace issues
- Better Kubernetes-native approach

**Cons:**
- **MAJOR ARCHITECTURE CHANGE**
- Requires RWX storage (CephFS, not Ceph RBD)
- All existing manifests need updates
- May not be available in all clusters

---

## Recommendation: Use Solution 1 (Privileged Container)

### Why?

1. **Preserves Current Architecture**
   - dump-volume-manager works as designed
   - Bidirectional mount continues to function
   - S3 uploader can see files

2. **Security Still Maintained**
   - Container runs as UID 185 (not root)
   - File ownership enforced at OS level
   - mount-access-controller manages permissions centrally

3. **Works Immediately**
   - No architecture changes
   - No storage class changes
   - Simple one-line fix

4. **Industry Standard Pattern**
   - Common for apps accessing shared host mounts
   - Similar to how monitoring agents work
   - Acceptable for controlled environments

### Security Considerations

**Still Secure Because:**
- ✅ Runs as UID 185, not root
- ✅ File ownership prevents unauthorized access
- ✅ mount-access-controller gates access via API
- ✅ Init container validates before starting
- ✅ Limited to specific namespace and ServiceAccount
- ✅ OpenShift SCC controls which accounts can use privileged

**Attack Surface:**
- Container has access to host's mount namespace
- Could potentially see other mounts (mitigated by SELinux in OpenShift)
- Similar privilege level as monitoring/logging agents

## Implementation

### Apply Solution 1

```bash
# deployment2.yaml already updated with:
# - securityContext.privileged: true
# - SCC annotation: dump-volume-privileged

# Deploy
oc apply -f k8s/apps/memoryleak/deployment2.yaml

# Verify
oc get pods -l app=memory-leak-app-2 -o yaml | grep -A 5 securityContext
```

### Verify Access

```bash
# Exec into pod
oc exec -it <pod-name> -- sh

# Check mount
mount | grep /dumps

# Test write access
touch /dumps/test-file.txt
ls -la /dumps/
```

## Alternative: If Privileged Is Not Acceptable

If your organization **absolutely prohibits** privileged containers:

1. **Change to RWX PVC** (Solution 3)
   - Use CephFS instead of Ceph RBD
   - Remove dump-volume-manager entirely
   - All pods mount same PVC directly

2. **Use Init Container to Copy Files**
   - Privileged init container copies from bidirectional mount to emptyDir
   - App container uses emptyDir
   - More complex, not recommended

## Comparison Matrix

| Aspect | Privileged | RWX PVC | Current (Broken) |
|--------|-----------|---------|------------------|
| Works with bidirectional mount | ✅ | ❌ | ❌ |
| No privileged containers | ❌ | ✅ | ✅ |
| Architecture change | None | Major | N/A |
| Security | Medium | High | N/A |
| Complexity | Low | High | N/A |
| Storage requirements | RWO | RWX | RWO |

## Conclusion

**For deployment2.yaml to access bidirectional mounts:**

✅ **Use `privileged: true` in the container securityContext**

This is the **correct and expected solution** for this architecture pattern. The security model still works because:
- Privileged access is for mount namespace visibility
- File-level security enforced by UID matching
- API-based permission management via mount-access-controller

---

**Status:** Solution 1 implemented in deployment2.yaml ✅
