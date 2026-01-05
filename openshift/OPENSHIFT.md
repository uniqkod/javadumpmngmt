# OpenShift-Specific Deployment Guide

## Overview

This guide covers the OpenShift-specific configurations and deployment steps for the memory leak demo application.

## Key Differences from Vanilla Kubernetes

### 1. Security Context Constraints (SCC)

OpenShift uses SCC instead of Pod Security Policies to control security contexts.

**Created Resources:**
- **SecurityContextConstraints**: `dump-volume-privileged`
- **ServiceAccount**: `dump-volume-manager`
- **ClusterRole**: `dump-volume-scc-user`
- **ClusterRoleBinding**: `dump-volume-scc-binding`

### 2. Removed Restrictions

OpenShift restricts certain capabilities:
- ❌ Removed `hostNetwork: true` from StatefulSet
- ❌ Removed `hostPID: true` from StatefulSet
- ✅ Added explicit `SYS_ADMIN` capability for bind mounts

### 3. OpenShift Routes

Instead of Ingress, OpenShift uses Routes for external access:
- Route with edge TLS termination
- Automatic certificate management
- HAProxy router integration

### 4. Enhanced Labels and Annotations

Added OpenShift-specific metadata:
- `app.openshift.io/runtime: java`
- `openshift.io/cluster-monitoring: "true"`
- OpenShift Console integration labels

## Deployment Order

### Step 1: Create RBAC and SCC (Cluster Admin Required)

```bash
# Must be run by cluster-admin
oc login -u admin

# Create SCC, ServiceAccount, and RBAC
oc apply -f openshift-rbac.yaml
```

**Creates:**
- ServiceAccount: `dump-volume-manager`
- SCC: `dump-volume-privileged`
- ClusterRole: `dump-volume-scc-user`
- ClusterRoleBinding: `dump-volume-scc-binding`

**Verify:**
```bash
# Check SCC
oc get scc dump-volume-privileged

# Check ServiceAccount
oc get sa -n memory-leak-demo dump-volume-manager

# Verify SCC binding
oc describe scc dump-volume-privileged | grep -A 5 Users
```

### Step 2: Deploy StatefulSet

```bash
# Deploy PVC, PriorityClass, and StatefulSet
oc apply -f statefulset-volume.yaml

# Verify StatefulSet
oc get statefulset -n memory-leak-demo
oc get pods -n memory-leak-demo -l app=dump-volume-manager

# Check which SCC is being used
oc get pod -n memory-leak-demo -l app=dump-volume-manager \
  -o jsonpath='{.items[0].metadata.annotations.openshift\.io/scc}'
```

Expected output:
```
dump-volume-privileged
```

### Step 3: Deploy Application

```bash
# Deploy application
oc apply -f deployment.yaml

# Verify deployment
oc get deployment -n memory-leak-demo
oc get pods -n memory-leak-demo -l app=memory-leak-app
```

### Step 4: Create Route

```bash
# Create OpenShift Route
oc apply -f openshift-route.yaml

# Get Route URL
oc get route -n memory-leak-demo memory-leak-app
```

**Access application:**
```bash
ROUTE_URL=$(oc get route -n memory-leak-demo memory-leak-app -o jsonpath='{.spec.host}')
echo "Application URL: https://$ROUTE_URL"

# Test health endpoint
curl -k https://$ROUTE_URL/health
```

## SecurityContextConstraints Details

### SCC: dump-volume-privileged

```yaml
allowHostDirVolumePlugin: true    # Required for hostPath volumes
allowPrivilegedContainer: true    # Required for bind mounts
allowedCapabilities:
  - SYS_ADMIN                     # Required for mount operations
```

**Why these permissions?**
- `allowHostDirVolumePlugin`: StatefulSet needs to mount host path `/mnt`
- `allowPrivilegedContainer`: Bind mount requires elevated privileges
- `SYS_ADMIN`: System capability needed for mount system call

### Checking SCC Assignment

```bash
# See which SCC a pod is using
oc describe pod <pod-name> -n memory-leak-demo | grep scc

# List all pods with their SCCs
oc get pods -n memory-leak-demo -o custom-columns=\
NAME:.metadata.name,\
SCC:.metadata.annotations.openshift\\.io/scc
```

## Storage Class

OpenShift automatically provisions storage using the default storage class:

```bash
# Check default storage class
oc get storageclass

# View PVC details
oc get pvc -n memory-leak-demo dump-storage-pvc
oc describe pvc -n memory-leak-demo dump-storage-pvc
```

## Monitoring and Logging

### OpenShift Console

1. Navigate to **Workloads** → **Pods**
2. Select namespace: `memory-leak-demo`
3. View pod logs directly in console
4. Monitor resource usage in Metrics tab

### CLI Monitoring

```bash
# Watch pods
oc get pods -n memory-leak-demo -w

# Stream logs
oc logs -f -n memory-leak-demo deployment/memory-leak-app

# Check init container
oc logs -n memory-leak-demo -l app=memory-leak-app -c wait-for-volume-manager

# View StatefulSet logs
oc logs -n memory-leak-demo statefulset/dump-volume-manager
```

### Check Heap Dumps

```bash
# List heap dumps
POD=$(oc get pod -n memory-leak-demo -l app=memory-leak-app -o jsonpath='{.items[0].metadata.name}')
oc exec -n memory-leak-demo $POD -- ls -lh /dumps/

# Copy heap dump
oc cp -n memory-leak-demo $POD:/dumps/heap_dump.hprof ./heap_dump.hprof

# Access via StatefulSet
oc exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  ls -lh /host/mnt/dump/memory-leak-demo/
```

## Troubleshooting

### SCC Permission Denied

**Error:**
```
unable to validate against any security context constraint
```

**Solution:**
```bash
# Check if SCC exists
oc get scc dump-volume-privileged

# Verify ServiceAccount has access
oc describe scc dump-volume-privileged

# Check ClusterRoleBinding
oc get clusterrolebinding dump-volume-scc-binding -o yaml
```

### StatefulSet Not Starting

**Check SCC assignment:**
```bash
# Describe pod
oc describe pod -n memory-leak-demo -l app=dump-volume-manager

# Check events
oc get events -n memory-leak-demo --sort-by='.lastTimestamp'
```

**Common issues:**
- ServiceAccount not assigned to StatefulSet spec
- SCC not properly bound to ServiceAccount
- Insufficient permissions (cluster-admin needed to create SCC)

### Application Stuck in Init

```bash
# Check init container logs
oc logs -n memory-leak-demo -l app=memory-leak-app -c wait-for-volume-manager

# Check if .ready file exists
oc exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  cat /host/mnt/dump/.ready
```

### Route Not Accessible

```bash
# Check route
oc get route -n memory-leak-demo
oc describe route -n memory-leak-demo memory-leak-app

# Test internally
oc run curl-test --rm -i --tty --image=curlimages/curl -- \
  curl http://memory-leak-service.memory-leak-demo.svc:8080/health
```

## Security Considerations

### 1. Least Privilege

The StatefulSet requires elevated privileges for bind mounts. In production:
- Use dedicated namespace
- Limit SCC usage to specific ServiceAccounts
- Regularly audit SCC assignments

### 2. Network Policies

Consider adding NetworkPolicy to restrict traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: memory-leak-netpol
  namespace: memory-leak-demo
spec:
  podSelector:
    matchLabels:
      app: memory-leak-app
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          network.openshift.io/policy-group: ingress
    ports:
    - protocol: TCP
      port: 8080
```

### 3. Resource Quotas

Set namespace resource quotas:

```bash
oc create quota memory-leak-quota -n memory-leak-demo \
  --hard=pods=10,requests.cpu=2,requests.memory=2Gi,limits.memory=4Gi
```

## Cleanup

```bash
# Delete application resources
oc delete -f openshift-route.yaml
oc delete -f deployment.yaml
oc delete -f statefulset-volume.yaml

# Delete RBAC and SCC (cluster-admin required)
oc delete -f openshift-rbac.yaml

# Delete namespace (removes everything)
oc delete namespace memory-leak-demo
```

## Differences Summary

| Component | Kubernetes | OpenShift |
|-----------|-----------|-----------|
| Security | PSP / PSS | SCC |
| External Access | Ingress | Route |
| ServiceAccount | Optional | Required for SCC |
| hostNetwork/hostPID | Allowed | Restricted (removed) |
| Capabilities | Implicit | Explicit (SYS_ADMIN) |
| Storage Class | Specified | Auto-detected |
| Labels | Basic | OpenShift-enhanced |

## Additional Resources

- [OpenShift SCC Documentation](https://docs.openshift.com/container-platform/latest/authentication/managing-security-context-constraints.html)
- [OpenShift Routes](https://docs.openshift.com/container-platform/latest/networking/routes/route-configuration.html)
- [OpenShift Storage](https://docs.openshift.com/container-platform/latest/storage/index.html)

---

**Branch:** ocp  
**OpenShift Version:** 4.x  
**Created:** 2025-12-07T19:42:00.000Z
