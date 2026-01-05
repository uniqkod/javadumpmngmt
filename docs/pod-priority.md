# Pod Priority and Startup Order

## Overview

This document explains how we ensure the StatefulSet runs before application pods using Kubernetes priority classes and init containers.

## Implementation

### 1. PriorityClass for StatefulSet

**File:** `statefulset-volume.yaml`

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: dump-volume-critical
value: 1000000
globalDefault: false
description: "High priority for dump volume manager StatefulSet"
```

**How it works:**
- Priority value of 1,000,000 (very high)
- Kubernetes scheduler prioritizes pods with higher priority values
- StatefulSet pods will be scheduled before lower-priority pods
- Not set as global default (only applies when explicitly set)

**Priority Levels:**
- **System Critical**: 2,000,000,000+ (reserved for system components)
- **High Priority**: 1,000,000 (our StatefulSet)
- **Default**: 0 (most application pods)
- **Low Priority**: negative values (can be preempted)

### 2. StatefulSet with Priority

**Applied to StatefulSet:**
```yaml
spec:
  template:
    spec:
      priorityClassName: dump-volume-critical
```

**Benefits:**
- Scheduler gives preference to StatefulSet pods
- StatefulSet pods are scheduled first on new nodes
- StatefulSet pods are less likely to be evicted during resource pressure

### 3. Readiness Probe

**StatefulSet signals readiness:**
```yaml
readinessProbe:
  exec:
    command:
    - sh
    - -c
    - test -f /host/mnt/dump/.ready
  initialDelaySeconds: 5
  periodSeconds: 5
```

**In the StatefulSet script:**
```bash
# Create readiness marker file
echo "ready" > /host/mnt/dump/.ready
```

### 4. Init Container in Application Pod

**File:** `deployment.yaml`

```yaml
initContainers:
- name: wait-for-volume-manager
  image: busybox:latest
  command:
  - sh
  - -c
  - |
    echo "Waiting for dump volume manager to be ready..."
    while [ ! -f /mnt/dump/.ready ]; do
      echo "Volume manager not ready yet, waiting..."
      sleep 2
    done
    echo "Volume manager is ready, proceeding with application startup"
  volumeMounts:
  - name: host-dumps
    mountPath: /mnt/dump
    readOnly: true
```

**How it works:**
1. Application pod starts
2. Init container runs first (before main container)
3. Checks for `/mnt/dump/.ready` file
4. Loops every 2 seconds until file exists
5. Once found, init container completes
6. Main application container starts

## Startup Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Scheduler                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
                ┌─────────────┴──────────────┐
                │                            │
                │  Sorts pods by priority    │
                │  value (highest first)     │
                │                            │
                └─────────────┬──────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 1: StatefulSet Pod (Priority: 1,000,000)                    │
│                                                                   │
│  1. PVC binds to PV                                              │
│  2. Pod scheduled on node                                        │
│  3. Container starts                                             │
│  4. Mounts PVC to /pv-storage                                   │
│  5. Creates bind mount to /host/mnt/dump                        │
│  6. Creates /host/mnt/dump/.ready marker                        │
│  7. Readiness probe passes                                       │
│  8. Pod marked as READY                                          │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ StatefulSet is READY
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  Step 2: Application Pod (Priority: 0 - default)                │
│                                                                   │
│  1. Pod scheduled (after StatefulSet due to priority)             │
│  2. Init container starts                                        │
│  3. Checks for /mnt/dump/.ready file                            │
│  4. Waits in loop if not found                                  │
│  5. File found → init container completes                       │
│  6. Main application container starts                            │
│  7. Application writes heap dumps to /dumps                      │
│  8. Dumps saved to /mnt/dump/memory-leak-demo/                  │
└──────────────────────────────────────────────────────────────────┘
```

## Guarantees

### What is Guaranteed:

✅ **StatefulSet scheduling priority**: StatefulSet pods are scheduled before application pods due to higher priority

✅ **StatefulSet readiness**: Init container ensures volume manager is ready before app starts

✅ **Storage availability**: Application never starts until `/mnt/dump` is mounted and ready

✅ **Node-level guarantee**: Each node runs StatefulSet before scheduling lower-priority pods

### What is NOT Guaranteed:

❌ **Absolute first**: System-critical pods (kube-proxy, CNI) may still start first

❌ **Zero waiting time**: Application pods may wait briefly in init container

❌ **Cross-node dependency**: Application on Node A doesn't wait for StatefulSet on Node B

## Verification

### Check Priority Class
```bash
kubectl get priorityclass dump-volume-critical
```

Expected output:
```
NAME                    VALUE      GLOBAL-DEFAULT   AGE
dump-volume-critical    1000000    false            5m
```

### Check StatefulSet Pod Priority
```bash
kubectl get pod -n memory-leak-demo -l app=dump-volume-manager -o jsonpath='{.items[0].spec.priorityClassName}'
```

Expected output:
```
dump-volume-critical
```

### Watch Startup Order
```bash
# Terminal 1: Watch StatefulSet
kubectl get pods -n memory-leak-demo -l app=dump-volume-manager -w

# Terminal 2: Watch Application
kubectl get pods -n memory-leak-demo -l app=memory-leak-app -w

# Terminal 3: View init container logs
kubectl logs -n memory-leak-demo -l app=memory-leak-app -c wait-for-volume-manager -f
```

### Check Init Container Status
```bash
kubectl describe pod -n memory-leak-demo -l app=memory-leak-app
```

Look for:
```
Init Containers:
  wait-for-volume-manager:
    State:          Terminated
      Reason:       Completed
      Exit Code:    0
```

## Troubleshooting

### Application Pod Stuck in Init:0/1
```bash
# Check init container logs
kubectl logs -n memory-leak-demo <pod-name> -c wait-for-volume-manager

# Check if .ready file exists on host
kubectl exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  ls -la /host/mnt/dump/.ready
```

**Common causes:**
- StatefulSet not running or not ready
- StatefulSet failed to create bind mount
- Permissions issue on /mnt/dump

### StatefulSet Not Scheduling First
```bash
# Check priority class
kubectl get priorityclass

# Check pod priority
kubectl get pod -n memory-leak-demo -o custom-columns=NAME:.metadata.name,PRIORITY:.spec.priority
```

### Node Has No StatefulSet Pod
```bash
# Check StatefulSet status
kubectl get statefulset -n memory-leak-demo

# Check node taints
kubectl describe node <node-name> | grep Taints
```

Ensure StatefulSet tolerations match node taints.

## Alternative: System Critical Priority

For even higher priority (use with caution):

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: dump-volume-system-critical
value: 2000000000
globalDefault: false
description: "System-level priority for dump volume manager"
```

**Warning:** Very high priority values (2 billion+) are typically reserved for critical system components. Use only if StatefulSet is truly critical for cluster operation.

## Best Practices

1. **Use appropriate priority values**
   - Reserve very high values (2B+) for system components
   - Use 1M range for important infrastructure
   - Keep application pods at default (0)

2. **Add readiness probes**
   - Always signal when StatefulSet is ready
   - Use marker files or health endpoints

3. **Use init containers**
   - Explicit dependency management
   - Better error messages than implicit ordering

4. **Test the order**
   - Deploy StatefulSet and application together
   - Verify init container waits correctly
   - Check logs for proper sequencing

5. **Handle failures gracefully**
   - Init container should have timeout
   - Log clear messages about what it's waiting for
   - Consider alerting if init takes too long

## Summary

The implementation provides strong guarantees:
- **PriorityClass**: Ensures StatefulSet is scheduled first
- **Readiness Probe**: Signals when StatefulSet is ready
- **Init Container**: Application explicitly waits for StatefulSet
- **Marker File**: Simple, reliable readiness signal

This combination ensures the storage infrastructure is ready before any application attempts to write heap dumps.

---

**Related Files:**
- `statefulset-volume.yaml` - PriorityClass and StatefulSet with readiness
- `deployment.yaml` - Application with init container
