# OpenShift SCC Configuration for deployment2.yaml

## Using Predefined SCC: hostmount-anyuid

For `deployment2.yaml`, we use the **predefined OpenShift SCC** `hostmount-anyuid` instead of creating a custom one.

### Why hostmount-anyuid?

✅ **Allows hostPath volumes** - Required for accessing `/mnt/dump/memory-leak-demo/heap`  
✅ **Allows any UID** - Can run as UID 185  
✅ **No privileged containers** - More secure than `privileged` SCC  
✅ **Predefined** - No need to create custom SCC  
✅ **Standard** - Available in all OpenShift clusters  

### Configuration

**1. Deployment Annotation:**
```yaml
metadata:
  annotations:
    openshift.io/scc: hostmount-anyuid
```

**2. ServiceAccount Binding:**
```bash
oc adm policy add-scc-to-user hostmount-anyuid \
  -z dump-volume-manager -n heapdump
```

Or use the RoleBinding:
```bash
oc apply -f openshift/rbac/hostmount-anyuid-binding.yaml
```

**3. Security Context:**
```yaml
securityContext:
  runAsUser: 185
  runAsGroup: 185
  fsGroup: 185
```

## Comparison: Custom vs Predefined SCC

### Custom SCC (dump-volume-privileged)
- Used for: dump-volume-manager StatefulSet
- Reason: Needs `SYS_ADMIN` capability for `chown` operations
- Allows: Privileged containers
- Use case: Service that manages permissions

### Predefined SCC (hostmount-anyuid)
- Used for: memory-leak-app deployment2
- Reason: Only needs hostPath access, no privileged operations
- Allows: hostPath volumes, any UID
- Use case: Application that uses managed volumes

## Setup Steps

### Option 1: Using oc command (Recommended)
```bash
# Grant hostmount-anyuid to ServiceAccount
oc adm policy add-scc-to-user hostmount-anyuid \
  -z dump-volume-manager -n heapdump

# Verify
oc get scc hostmount-anyuid
oc describe scc hostmount-anyuid
```

### Option 2: Using RoleBinding
```bash
# Apply the binding
oc apply -f openshift/rbac/hostmount-anyuid-binding.yaml

# Verify
oc get clusterrolebinding heapdump-hostmount-anyuid
```

## Verification

```bash
# Check which SCC is being used by pod
oc get pod <pod-name> -o yaml | grep openshift.io/scc

# Should show: hostmount-anyuid

# Check ServiceAccount permissions
oc describe sa dump-volume-manager -n heapdump
```

## Benefits

1. **No Custom SCC Needed** - Uses standard OpenShift resource
2. **Less Privileged** - Only grants necessary permissions
3. **Portable** - Works across different OpenShift clusters
4. **Maintainable** - No custom SCC to track and update
5. **Secure** - Follows principle of least privilege

## Alternative SCCs (Not Recommended)

| SCC | hostPath | Why Not Use It |
|-----|----------|----------------|
| restricted | ❌ | Default, doesn't allow hostPath |
| anyuid | ❌ | Allows any UID but no hostPath |
| privileged | ✅ | Too permissive, grants all capabilities |
| hostnetwork | ✅ | Designed for network workloads |

## Migration from Custom SCC

If you previously used `dump-volume-privileged`:

```bash
# Remove old custom SCC binding (optional)
oc delete clusterrolebinding dump-volume-scc-binding

# Add hostmount-anyuid
oc adm policy add-scc-to-user hostmount-anyuid \
  -z dump-volume-manager -n heapdump

# Update deployment annotation
# (already done in deployment2.yaml)

# Restart pods to apply new SCC
oc rollout restart deployment memory-leak-app-2 -n heapdump
```

## Summary

**For deployment2.yaml:**
- ✅ Use `hostmount-anyuid` (predefined SCC)
- ✅ Allows hostPath volumes
- ✅ Runs as UID 185
- ✅ No privileged containers
- ✅ Minimal permissions

**For dump-volume-manager:**
- ✅ Keep `dump-volume-privileged` (custom SCC)
- ✅ Needs privileged access for chown operations
- ✅ Runs as root with SYS_ADMIN capability

---

**Recommended:** Use `hostmount-anyuid` for application workloads that only need hostPath access.
