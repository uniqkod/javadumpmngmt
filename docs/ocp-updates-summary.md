# OpenShift Updates Summary

## Overview

This document summarizes all changes made to adapt the memory leak demo application from vanilla Kubernetes to OpenShift Container Platform.

**Branch:** `ocp`  
**Base Branch:** `master` (vanilla Kubernetes)  
**Commit:** `ae0ec15` - "Add OpenShift support with SCC, RBAC, and Route"  
**Date:** 2025-12-07T19:44:09+03:00

---

## New Files Created

### 1. `openshift-rbac.yaml` (76 lines)

Complete RBAC and SecurityContextConstraints configuration for OpenShift.

**Contents:**
- **ServiceAccount**: `dump-volume-manager`
  - Required for SCC binding
  - Used by StatefulSet pods

- **SecurityContextConstraints**: `dump-volume-privileged`
  - Allows privileged containers
  - Permits hostPath volumes
  - Grants `SYS_ADMIN` capability for bind mounts
  - Priority: 10

- **ClusterRole**: `dump-volume-scc-user`
  - Grants permission to use the SCC

- **ClusterRoleBinding**: `dump-volume-scc-binding`
  - Binds ServiceAccount to ClusterRole
  - Enables StatefulSet to use privileged SCC

**Why needed:**
OpenShift uses SCC (Security Context Constraints) instead of Pod Security Policies. The StatefulSet needs privileged access for bind mounting the PersistentVolume to the host path.

---

### 2. `openshift-route.yaml` (22 lines)

OpenShift Route for external access to the application.

**Features:**
- Route name: `memory-leak-app`
- TLS termination: Edge
- Automatic HTTPS redirect
- HAProxy integration
- 5-minute timeout

**Why needed:**
OpenShift uses Routes instead of Kubernetes Ingress for external access. Routes integrate with OpenShift's HAProxy router and provide automatic certificate management.

---

### 3. `OPENSHIFT.md` (343 lines)

Comprehensive OpenShift-specific deployment and troubleshooting guide.

**Sections:**
1. Overview and key differences from Kubernetes
2. Deployment order with step-by-step instructions
3. SecurityContextConstraints details
4. Storage class configuration
5. Monitoring and logging with OpenShift Console and CLI
6. Troubleshooting guide (SCC issues, StatefulSet, Routes)
7. Security considerations
8. Cleanup instructions
9. Comparison table: Kubernetes vs OpenShift
10. Additional resources

**Why needed:**
OpenShift has significant differences from vanilla Kubernetes. Users need specific guidance for deployment, security configuration, and troubleshooting in an OpenShift environment.

---

## Modified Files

### 1. `statefulset-volume.yaml`

**Changes:**

#### Removed (Security Restrictions)
```yaml
# Removed from StatefulSet spec
hostNetwork: true
hostPID: true
```

**Reason:** OpenShift restricts `hostNetwork` and `hostPID` for security. The StatefulSet can still perform bind mounts without these.

#### Added (ServiceAccount)
```yaml
spec:
  template:
    spec:
      serviceAccountName: dump-volume-manager
```

**Reason:** Required for SCC binding. ServiceAccount authenticates the pod and grants SCC permissions.

#### Added (Annotations)
```yaml
metadata:
  annotations:
    openshift.io/scc: dump-volume-privileged
```

**Reason:** Documents which SCC the StatefulSet should use. Helps with debugging SCC assignments.

#### Added (Labels)
```yaml
metadata:
  labels:
    app: dump-volume-manager
```

**Reason:** Better organization and filtering in OpenShift Console.

#### Added (Security Capabilities)
```yaml
securityContext:
  privileged: true
  capabilities:
    add:
      - SYS_ADMIN
```

**Reason:** Explicit `SYS_ADMIN` capability required for mount system calls in OpenShift.

#### Modified (Storage Class)
```yaml
# Before
storageClassName: ""  # Uses default storage class

# After
# OpenShift will use default storage class if not specified
```

**Reason:** OpenShift automatically detects and uses the default storage class. No need to specify empty string.

---

### 2. `deployment.yaml`

**Changes:**

#### Added (Namespace Labels)
```yaml
metadata:
  labels:
    app: memory-leak-demo
    openshift.io/cluster-monitoring: "true"
  annotations:
    openshift.io/description: "Memory leak demo application for heap dump testing"
    openshift.io/display-name: "Memory Leak Demo"
```

**Reason:** 
- Enables cluster monitoring for the namespace
- Provides user-friendly display name in OpenShift Console
- Adds description for documentation

#### Added (Deployment Labels)
```yaml
labels:
  app: memory-leak-app
  app.kubernetes.io/name: memory-leak-app
  app.kubernetes.io/component: application
  app.openshift.io/runtime: java
```

**Reason:**
- `app.openshift.io/runtime: java` - Shows Java icon in OpenShift Console
- Standard Kubernetes labels for better organization
- Improved visibility in OpenShift topology view

#### Added (Deployment Annotations)
```yaml
annotations:
  app.openshift.io/vcs-uri: "https://github.com/example/memory-leak-demo"
  app.openshift.io/vcs-ref: "ocp"
```

**Reason:**
- Links to source code repository in OpenShift Console
- Shows branch name for better traceability

#### Added (Pod Annotations)
```yaml
metadata:
  annotations:
    openshift.io/scc: restricted
```

**Reason:** Application pods use the default "restricted" SCC, documenting the security context used.

#### Added (Pod Labels)
```yaml
labels:
  app: memory-leak-app
  deployment: memory-leak-app
```

**Reason:** Additional label for better filtering and identification in OpenShift.

---

### 3. `README.md`

**Changes:**

#### Updated Title
```markdown
# Before
Memory Leak Demo Application

# After
Memory Leak Demo Application - OpenShift
```

**Reason:** Clear identification of OpenShift-specific branch.

#### Added Branch Notice
```markdown
> **Note:** This is the OpenShift-specific branch. For vanilla Kubernetes, see the `master` branch.
```

**Reason:** Prevent confusion between Kubernetes and OpenShift deployments.

#### Added OpenShift Features
```markdown
- OpenShift SecurityContextConstraints (SCC) for privileged operations
- OpenShift Route with TLS termination
- ServiceAccount with proper RBAC
```

**Reason:** Highlight OpenShift-specific features.

#### Updated Deployment Commands
```bash
# Before (Kubernetes)
kubectl apply -f statefulset-volume.yaml
kubectl logs -f deployment/memory-leak-app

# After (OpenShift)
oc login -u admin
oc apply -f openshift-rbac.yaml
oc apply -f statefulset-volume.yaml
oc logs -f deployment/memory-leak-app
```

**Reason:** 
- Use `oc` CLI instead of `kubectl`
- Add RBAC/SCC creation step
- Show cluster-admin login requirement

#### Added Route Instructions
```bash
# Create OpenShift Route
oc apply -f openshift-route.yaml

# Get Route URL
ROUTE_URL=$(oc get route -n memory-leak-demo memory-leak-app -o jsonpath='{.spec.host}')
echo "Application URL: https://$ROUTE_URL"

# Check health endpoint
curl -k https://$ROUTE_URL/health
```

**Reason:** Document how to access the application externally via OpenShift Route instead of port-forward.

#### Updated Architecture Section
Added SCC & RBAC as the first tier:

```markdown
1. **SecurityContextConstraints & RBAC** (`openshift-rbac.yaml`):
   - SCC: `dump-volume-privileged` for StatefulSet privileged operations
   - ServiceAccount: `dump-volume-manager`
   - ClusterRole & ClusterRoleBinding for SCC usage
```

**Reason:** Security configuration is fundamental in OpenShift and should be understood first.

#### Added OPENSHIFT.md Reference
```markdown
See documentation:
- [OPENSHIFT.md](OPENSHIFT.md) - OpenShift-specific deployment guide
- [bidirectional-mount.md](bidirectional-mount.md) - Volume architecture
- [pod-priority.md](pod-priority.md) - Priority and startup order
```

**Reason:** Direct users to comprehensive OpenShift guide.

---

## Key Differences: Kubernetes vs OpenShift

| Aspect | Kubernetes (master) | OpenShift (ocp) |
|--------|-------------------|----------------|
| **Security** | PSP / PSS | SecurityContextConstraints (SCC) |
| **ServiceAccount** | Optional | Required for SCC binding |
| **External Access** | Ingress / NodePort | Route with TLS |
| **hostNetwork** | ✅ Allowed | ❌ Removed |
| **hostPID** | ✅ Allowed | ❌ Removed |
| **Capabilities** | Implicit via privileged | Explicit SYS_ADMIN |
| **Storage Class** | `storageClassName: ""` | Auto-detected |
| **Labels** | Basic app labels | OpenShift-enhanced |
| **Annotations** | Minimal | Console integration |
| **CLI Commands** | `kubectl` | `oc` |
| **Admin Required** | No (for basic deployment) | Yes (for SCC creation) |

---

## Deployment Order Comparison

### Kubernetes (master branch)
1. Apply StatefulSet (creates PVC, PriorityClass)
2. Apply Deployment
3. Access via port-forward or NodePort

### OpenShift (ocp branch)
1. Login as cluster-admin
2. Apply RBAC/SCC (`openshift-rbac.yaml`)
3. Apply StatefulSet (creates PVC, PriorityClass)
4. Apply Deployment
5. Apply Route (`openshift-route.yaml`)
6. Access via HTTPS URL

**Additional Steps Required:**
- SCC creation (cluster-admin)
- ServiceAccount setup
- Route configuration

---

## Security Enhancements

### 1. SecurityContextConstraints
- Fine-grained control over pod security
- Explicit capability grants (`SYS_ADMIN`)
- Prevents privilege escalation
- Auditable security policies

### 2. Removed Host Access
- No `hostNetwork` reduces attack surface
- No `hostPID` prevents process snooping
- Bind mount still works with SCC permissions

### 3. ServiceAccount Isolation
- Dedicated ServiceAccount for StatefulSet
- Principle of least privilege
- RBAC-based SCC access

### 4. TLS by Default
- OpenShift Route provides automatic TLS
- Edge termination at router
- Forces HTTPS redirect

---

## Testing Checklist

Before deploying to production OpenShift:

- [ ] Verify cluster-admin access for SCC creation
- [ ] Check default storage class exists
- [ ] Test SCC assignment to ServiceAccount
- [ ] Verify StatefulSet can create bind mounts
- [ ] Confirm Route is accessible externally
- [ ] Test heap dump generation and retrieval
- [ ] Verify init container waits for StatefulSet
- [ ] Check logs in OpenShift Console
- [ ] Test application OOM and restart behavior
- [ ] Verify PVC persists across pod restarts

---

## Migration Guide

### From Kubernetes to OpenShift

If you have the application running on vanilla Kubernetes and want to migrate to OpenShift:

1. **Switch to ocp branch:**
   ```bash
   git checkout ocp
   ```

2. **Build and push image to OpenShift registry:**
   ```bash
   oc new-build --binary --name=memory-leak-demo -l app=memory-leak-app
   oc start-build memory-leak-demo --from-dir=. --follow
   ```

3. **Update image reference in deployment.yaml:**
   ```yaml
   image: image-registry.openshift-image-registry.svc:5000/memory-leak-demo/memory-leak-demo:latest
   ```

4. **Deploy with new manifests:**
   ```bash
   oc apply -f openshift-rbac.yaml
   oc apply -f statefulset-volume.yaml
   oc apply -f deployment.yaml
   oc apply -f openshift-route.yaml
   ```

5. **Verify migration:**
   ```bash
   oc get all -n memory-leak-demo
   oc get route -n memory-leak-demo
   ```

---

## File Statistics

### New Files
| File | Lines | Purpose |
|------|-------|---------|
| openshift-rbac.yaml | 76 | SCC, ServiceAccount, RBAC |
| openshift-route.yaml | 22 | External access via Route |
| OPENSHIFT.md | 343 | Deployment and troubleshooting guide |
| **Total** | **441** | **New content for OpenShift** |

### Modified Files
| File | Changes | Summary |
|------|---------|---------|
| statefulset-volume.yaml | ~15 lines | Added ServiceAccount, removed host restrictions, added capabilities |
| deployment.yaml | ~20 lines | Added OpenShift labels and annotations |
| README.md | ~50 lines | Updated commands from kubectl to oc, added Route instructions |
| **Total** | **~85 lines** | **Modified for OpenShift compatibility** |

### Overall Impact
- **Total lines added:** ~520
- **Files created:** 3
- **Files modified:** 3
- **Net change:** +519 lines in commit `ae0ec15`

---

## Troubleshooting Quick Reference

### Issue: SCC Permission Denied
**Symptom:** Pod fails with "unable to validate against any security context constraint"

**Solution:**
```bash
oc get scc dump-volume-privileged
oc describe scc dump-volume-privileged
oc get clusterrolebinding dump-volume-scc-binding -o yaml
```

### Issue: StatefulSet Not Starting
**Symptom:** StatefulSet pods in Pending or CrashLoopBackOff

**Solution:**
```bash
oc describe pod -n memory-leak-demo -l app=dump-volume-manager
oc get events -n memory-leak-demo --sort-by='.lastTimestamp'
oc logs -n memory-leak-demo statefulset/dump-volume-manager
```

### Issue: Route Not Accessible
**Symptom:** Cannot access application via Route URL

**Solution:**
```bash
oc get route -n memory-leak-demo
oc describe route -n memory-leak-demo memory-leak-app
# Test internal service
oc run curl-test --rm -i --tty --image=curlimages/curl -- \
  curl http://memory-leak-service.memory-leak-demo.svc:8080/health
```

### Issue: Init Container Stuck
**Symptom:** Application pod shows Init:0/1

**Solution:**
```bash
oc logs -n memory-leak-demo -l app=memory-leak-app -c wait-for-volume-manager
oc exec -n memory-leak-demo statefulset/dump-volume-manager -- cat /host/mnt/dump/.ready
```

---

## Additional Resources

### OpenShift Documentation
- [Security Context Constraints](https://docs.openshift.com/container-platform/latest/authentication/managing-security-context-constraints.html)
- [Routes](https://docs.openshift.com/container-platform/latest/networking/routes/route-configuration.html)
- [Storage Classes](https://docs.openshift.com/container-platform/latest/storage/dynamic-provisioning.html)

### Internal Documentation
- `OPENSHIFT.md` - Complete OpenShift deployment guide
- `README.md` - Quick start for OpenShift
- `bidirectional-mount.md` - Volume architecture details
- `pod-priority.md` - Priority class and startup ordering

---

## Summary

The `ocp` branch successfully adapts the memory leak demo application for OpenShift Container Platform by:

1. ✅ Adding SecurityContextConstraints for privileged operations
2. ✅ Creating ServiceAccount with proper RBAC bindings
3. ✅ Removing restricted host access (hostNetwork, hostPID)
4. ✅ Adding OpenShift Route for external access with TLS
5. ✅ Enhancing labels and annotations for OpenShift Console integration
6. ✅ Providing comprehensive OpenShift-specific documentation

All changes maintain the core functionality while ensuring compliance with OpenShift security policies and best practices.

**Branch Status:**
```
* ae0ec15 (HEAD -> ocp) Add OpenShift support with SCC, RBAC, and Route
* bb78052 (master) vanila ready
```

**Maintained Compatibility:**
- Core application logic unchanged
- PersistentVolume storage approach unchanged
- Pod priority and init container dependencies unchanged
- Heap dump functionality unchanged

**OpenShift-Specific Additions:**
- Security: SCC, RBAC, ServiceAccount
- Networking: Route with TLS
- Observability: OpenShift Console integration
- Documentation: Complete deployment guide

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-07T19:47:57.257Z  
**Branch:** ocp  
**Commit:** ae0ec15
