# Bind Mount Persistence and Recovery

## Problem: Bind Mount Loss on Container Restart

### What Happens When StatefulSet Restarts?

When the StatefulSet container stops or crashes:

1. **Container dies** → Bind mount is removed from the host
2. **Host path `/mnt/dump`** becomes an empty directory (or inaccessible)
3. **Application pods** lose access to `/mnt/dump/memory-leak-demo`
4. **Heap dump writes fail** with "No such file or directory" or "Permission denied"
5. **Init container** may fail to find `.ready` file

### Why Does This Happen?

Bind mounts are tied to the process that created them. When the container process exits:
- Linux kernel removes the mount point
- The directory remains but no longer points to the PVC
- Data in the PVC is safe, but inaccessible via the bind mount path

---

## Solution Implemented

### 1. Mount Existence Check on Startup

The StatefulSet script now checks if a mount already exists:

```bash
if mountpoint -q /host/mnt/dump; then
  echo "WARNING: /host/mnt/dump is already a mountpoint"
  echo "Attempting to unmount existing mount..."
  umount /host/mnt/dump || echo "Unmount failed, will try to mount anyway"
fi
```

**Why:** After a crash or restart, orphaned mount points may exist. We clean them up before remounting.

### 2. Mount Verification After Creation

```bash
mount --bind /pv-storage /host/mnt/dump

# Verify mount succeeded
if mountpoint -q /host/mnt/dump; then
  echo "Bind mount created successfully"
else
  echo "ERROR: Bind mount failed"
  exit 1
fi
```

**Why:** Ensures the bind mount actually succeeded before marking as ready.

### 3. Continuous Mount Monitoring

The main loop now monitors the mount point every 30 seconds:

```bash
while true; do
  sleep 30
  if ! mountpoint -q /host/mnt/dump; then
    echo "WARNING: Mount point lost! Attempting to remount..."
    mount --bind /pv-storage /host/mnt/dump
    if mountpoint -q /host/mnt/dump; then
      echo "Remount successful"
      echo "ready" > /host/mnt/dump/.ready
    else
      echo "ERROR: Remount failed"
      rm -f /host/mnt/dump/.ready 2>/dev/null || true
    fi
  fi
done
```

**Why:** 
- Detects if the mount point is lost (shouldn't happen in normal operation)
- Automatically attempts to remount
- Updates `.ready` marker to reflect actual state

### 4. Enhanced Probes

#### Readiness Probe
```yaml
readinessProbe:
  exec:
    command:
    - sh
    - -c
    - test -f /host/mnt/dump/.ready && mountpoint -q /host/mnt/dump
  initialDelaySeconds: 5
  periodSeconds: 5
```

**Why:** Checks both:
- `.ready` file exists
- Mount point is actually mounted

This ensures the pod is only marked "ready" when the mount is truly accessible.

#### Liveness Probe
```yaml
livenessProbe:
  exec:
    command:
    - sh
    - -c
    - mountpoint -q /host/mnt/dump
  initialDelaySeconds: 10
  periodSeconds: 30
```

**Why:** 
- Checks if mount is still present
- If mount is lost and can't be recovered, pod restarts
- Kubernetes will restart the container to fix the issue

---

## Failure Scenarios and Handling

### Scenario 1: Container Crashes

**What happens:**
1. Container process exits
2. Bind mount is removed
3. `/mnt/dump` becomes empty directory

**Recovery:**
1. StatefulSet restarts container (RestartPolicy: Always)
2. Script detects no mount: `if ! mountpoint -q /host/mnt/dump`
3. Creates fresh bind mount: `mount --bind /pv-storage /host/mnt/dump`
4. Recreates `.ready` marker
5. Application pods can resume writing

**Impact:**
- Brief interruption (seconds to a minute)
- Application init container waits for `.ready` file
- No data loss (PVC data is preserved)

### Scenario 2: OOM Kill of StatefulSet

**What happens:**
1. StatefulSet pod is OOM killed
2. Mount is lost immediately
3. Application may be mid-write to heap dump

**Recovery:**
1. Same as Scenario 1
2. Partial heap dump file may exist in PVC
3. New heap dump writes will succeed after remount

**Impact:**
- Application may need to restart if it was writing during mount loss
- Old heap dumps in PVC are preserved

### Scenario 3: Node Reboot

**What happens:**
1. All containers on node stop
2. All mounts are lost
3. Node comes back up

**Recovery:**
1. StatefulSet pod starts on node
2. Creates fresh bind mount
3. All data from PVC is accessible again

**Impact:**
- All pods on node restart
- No data loss (PVC persists across node reboots)

### Scenario 4: Mount Point Corruption

**What happens:**
1. Mount point exists but is inaccessible
2. Operations fail with "Stale file handle" or similar

**Recovery:**
1. Monitoring loop detects mount failure
2. Attempts unmount: `umount /host/mnt/dump`
3. Remounts: `mount --bind /pv-storage /host/mnt/dump`
4. If unmount fails, liveness probe fails
5. Container restarts and cleans up

**Impact:**
- Automatic recovery via monitoring loop
- If auto-recovery fails, container restart fixes it

---

## Testing the Recovery

### Test 1: Kill StatefulSet Container

```bash
# Find StatefulSet pod
POD=$(oc get pod -n memory-leak-demo -l app=dump-volume-manager -o jsonpath='{.items[0].metadata.name}')

# Kill the container
oc exec -n memory-leak-demo $POD -- kill 1

# Watch recovery
oc logs -n memory-leak-demo $POD -f
```

**Expected:**
- Container restarts
- Mount is recreated
- `.ready` file reappears
- Application continues working

### Test 2: Manually Unmount

```bash
# SSH to node (if accessible)
ssh node-hostname

# Find the mount
mount | grep /mnt/dump

# Unmount it
umount /mnt/dump

# Watch StatefulSet detect and remount
oc logs -n memory-leak-demo -l app=dump-volume-manager -f
```

**Expected:**
- Monitoring loop detects missing mount (within 30 seconds)
- Automatic remount occurs
- `.ready` file recreated

### Test 3: Delete and Recreate StatefulSet

```bash
# Delete StatefulSet
oc delete statefulset -n memory-leak-demo dump-volume-manager

# Application should show Init:0/1 (waiting)
oc get pods -n memory-leak-demo -l app=memory-leak-app

# Recreate StatefulSet
oc apply -f statefulset-volume.yaml

# Watch application init container complete
oc logs -n memory-leak-demo -l app=memory-leak-app -c wait-for-volume-manager
```

**Expected:**
- Application waits in init
- StatefulSet recreates mount
- Init container detects `.ready` and completes
- Application starts

---

## Best Practices

### 1. Monitor StatefulSet Health

```bash
# Check if all StatefulSet pods are ready
oc get statefulset -n memory-leak-demo dump-volume-manager

# Should show: DESIRED = CURRENT = READY
```

### 2. Monitor Mount Status

```bash
# Check mount from StatefulSet
oc exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  mountpoint -q /host/mnt/dump && echo "Mounted" || echo "NOT MOUNTED"

# Check files are accessible
oc exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  ls -lh /host/mnt/dump/
```

### 3. Set Up Alerts

Create alerts for:
- StatefulSet pod not ready
- Frequent StatefulSet restarts (CrashLoopBackOff)
- Mount failures in logs

### 4. Application Resilience

Applications should handle mount unavailability gracefully:

```java
try {
    // Write heap dump
    Files.write(path, data);
} catch (NoSuchFileException e) {
    logger.error("Mount point not available, will retry");
    // Retry logic or store in local emptyDir temporarily
}
```

---

## Limitations

### What This Solution CANNOT Fix

1. **Simultaneous StatefulSet and Application Crash**
   - If node goes down, both lose state
   - Both restart and recover independently
   - Brief window where application may fail writes

2. **PVC Deletion**
   - If PVC is deleted, data is lost
   - Bind mount will fail (no source to bind)
   - StatefulSet will crash and not recover

3. **Storage Backend Failure**
   - If underlying storage (NFS, Ceph, etc.) fails
   - Mount may become stale
   - Requires manual intervention

### Mitigation Strategies

1. **Use StatefulSet for application** (if ordering matters)
2. **Implement retry logic** in application for heap dump writes
3. **Monitor storage backend** health separately
4. **Regular PVC snapshots** for disaster recovery

---

## Monitoring Commands

### Check Current Mount Status

```bash
# Via StatefulSet
oc exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  sh -c 'mountpoint /host/mnt/dump && echo OK || echo FAILED'

# Check .ready marker
oc exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  test -f /host/mnt/dump/.ready && echo "Ready" || echo "Not Ready"
```

### View Recent Mount Events

```bash
# Check StatefulSet logs for mount activity
oc logs -n memory-leak-demo statefulset/dump-volume-manager --tail=100 | \
  grep -E "mount|bind|ready"
```

### Check Probe Status

```bash
# See probe failures
oc describe pod -n memory-leak-demo -l app=dump-volume-manager | \
  grep -A 5 "Liveness\|Readiness"
```

---

## Summary

The improved StatefulSet now handles bind mount persistence through:

1. ✅ **Startup mount verification** - Cleans up stale mounts
2. ✅ **Post-mount validation** - Ensures mount succeeded
3. ✅ **Continuous monitoring** - Checks mount every 30 seconds
4. ✅ **Automatic recovery** - Remounts if mount is lost
5. ✅ **Enhanced probes** - Readiness checks mount + marker, liveness checks mount
6. ✅ **Graceful restarts** - Application waits via init container

**Result:** High availability with automatic recovery from most failure scenarios.

---

**Created:** 2025-12-07T19:55:21.842Z  
**Branch:** ocp  
**Related Files:**
- `statefulset-volume.yaml` - Enhanced with monitoring loop and probes
