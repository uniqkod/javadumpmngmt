# OpenShift Local Disk Strategies

## Question: How to mount local disk to every node and share access via hostPath?

**Answer: YES!** OpenShift provides multiple approaches. Here are all options:

---

## Option 1: Local Storage Operator ✅ RECOMMENDED

**Official OpenShift solution for local disk management.**

### How It Works
1. Install Local Storage Operator from OperatorHub
2. Create `LocalVolume` CR to define which disks to use
3. Operator auto-discovers and creates PersistentVolumes
4. Apps use standard PVCs (no hostPath needed!)

### Installation

```bash
# Install via OperatorHub UI or CLI
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: openshift-local-storage
---
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: local-operator-group
  namespace: openshift-local-storage
spec:
  targetNamespaces:
  - openshift-local-storage
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: local-storage-operator
  namespace: openshift-local-storage
spec:
  channel: stable
  name: local-storage-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF
```

### Configure Local Disks

```yaml
apiVersion: local.storage.openshift.io/v1
kind: LocalVolume
metadata:
  name: heap-dump-storage
  namespace: openshift-local-storage
spec:
  nodeSelector:
    nodeSelectorTerms:
    - matchExpressions:
      - key: heapdump
        operator: In
        values:
        - test
  storageClassDevices:
  - storageClassName: heap-dump-local
    volumeMode: Filesystem
    fsType: xfs
    devicePaths:
    - /dev/vdb              # Your local disk
    - /dev/disk/by-id/...   # Or by disk ID
```

### Use in Application

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: memory-leak-app
spec:
  serviceName: memory-leak
  replicas: 2  # One per node with heapdump=test label
  volumeClaimTemplates:
  - metadata:
      name: heap-dumps
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: heap-dump-local
      resources:
        requests:
          storage: 25Gi
  template:
    spec:
      containers:
      - name: app
        volumeMounts:
        - name: heap-dumps
          mountPath: /dumps
        securityContext:
          runAsUser: 185  # No privileged needed!
```

### Benefits
✅ No privileged containers needed  
✅ Standard PV/PVC workflow  
✅ Automatic disk discovery  
✅ Official Red Hat support  
✅ Node affinity built-in  
✅ Clean, Kubernetes-native  

### Drawbacks
⚠️ Requires operator installation  
⚠️ Disk must be unmounted and empty  

---

## Option 2: MachineConfig + DaemonSet ⚙️ CURRENT APPROACH

**Your current setup with dump-volume-manager.**

### MachineConfig to Mount Disk at Boot

```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineConfig
metadata:
  labels:
    machineconfiguration.openshift.io/role: worker
  name: 99-worker-heap-dump-disk
spec:
  config:
    ignition:
      version: 3.2.0
    systemd:
      units:
      - name: mnt-dump.mount
        enabled: true
        contents: |
          [Unit]
          Description=Mount heap dump disk
          Before=local-fs.target
          
          [Mount]
          What=/dev/vdb
          Where=/mnt/dump-disk
          Type=xfs
          Options=defaults
          
          [Install]
          WantedBy=local-fs.target
    storage:
      filesystems:
      - device: /dev/vdb
        format: xfs
        label: dump-disk
        wipeFilesystem: false
```

### DaemonSet to Manage Mount

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: dump-disk-manager
spec:
  selector:
    matchLabels:
      app: dump-disk-manager
  template:
    metadata:
      labels:
        app: dump-disk-manager
    spec:
      nodeSelector:
        heapdump: test
      containers:
      - name: manager
        image: busybox
        command: ["sleep", "infinity"]
        volumeMounts:
        - name: dump-disk
          mountPath: /dump-disk
          mountPropagation: Bidirectional  # Share to other containers
        securityContext:
          privileged: true
      volumes:
      - name: dump-disk
        hostPath:
          path: /mnt/dump-disk
          type: Directory
```

### Access from Application

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-leak-app
spec:
  template:
    spec:
      containers:
      - name: app
        volumeMounts:
        - name: dumps
          mountPath: /dumps
        securityContext:
          privileged: true  # Required for bidirectional mount access
      volumes:
      - name: dumps
        hostPath:
          path: /mnt/dump-disk/memory-leak-demo
          type: Directory
```

### Benefits
✅ Full control over mount  
✅ Can customize filesystem  
✅ Works with existing setup  

### Drawbacks
⚠️ Requires privileged containers  
⚠️ MachineConfig needs node reboot  
⚠️ Manual disk management  
⚠️ HostPath security concerns  

---

## Option 3: Manual Local PersistentVolumes 📝 MANUAL

**Create PVs manually for each node.**

### Create PV for Each Node

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: heap-dump-pv-node1
spec:
  capacity:
    storage: 25Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-heap-dump
  local:
    path: /mnt/dump-disk  # Must exist on node
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - worker-node-1
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: heap-dump-pv-node2
spec:
  capacity:
    storage: 25Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-heap-dump
  local:
    path: /mnt/dump-disk
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - worker-node-2
```

### Use in Application

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: memory-leak-app
spec:
  serviceName: memory-leak
  replicas: 2
  volumeClaimTemplates:
  - metadata:
      name: heap-dumps
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: local-heap-dump
      resources:
        requests:
          storage: 10Gi
```

### Benefits
✅ No operator needed  
✅ Standard Kubernetes resources  
✅ No privileged containers  

### Drawbacks
⚠️ Manual PV creation per node  
⚠️ Disk must be pre-mounted on nodes  
⚠️ Scaling complexity  

---

## Comparison Matrix

| Feature | Local Storage Operator | MachineConfig + DaemonSet | Manual Local PV |
|---------|------------------------|---------------------------|-----------------|
| **No Privileged** | ✅ | ❌ | ✅ |
| **Auto Discovery** | ✅ | ❌ | ❌ |
| **Official Support** | ✅ | ✅ | ✅ |
| **Setup Complexity** | Medium | High | Medium |
| **Node Reboot** | No | Yes | No |
| **Scalability** | High | Medium | Low |
| **PV/PVC** | ✅ | ❌ (hostPath) | ✅ |
| **HostPath** | ❌ | ✅ | ❌ |

---

## Recommended Migration Path

### From Current Setup → Local Storage Operator

**Step 1: Install Local Storage Operator**
```bash
# Via OpenShift Console: OperatorHub → Local Storage
# Or via CLI (see above)
```

**Step 2: Prepare Disks**
```bash
# On each node, ensure disk is unmounted
ssh core@node1 "sudo umount /mnt/dump"
```

**Step 3: Create LocalVolume**
```yaml
apiVersion: local.storage.openshift.io/v1
kind: LocalVolume
metadata:
  name: heap-dump-volumes
  namespace: openshift-local-storage
spec:
  nodeSelector:
    nodeSelectorTerms:
    - matchExpressions:
      - key: heapdump
        operator: In
        values:
        - test
  storageClassDevices:
  - storageClassName: heap-dump-local
    volumeMode: Filesystem
    fsType: xfs
    devicePaths:
    - /dev/vdb
```

**Step 4: Update Applications**
```yaml
# Change from Deployment to StatefulSet
# Replace hostPath with volumeClaimTemplates
# Remove privileged securityContext
```

**Step 5: Remove Old Resources**
```bash
oc delete daemonset dump-volume-manager
oc delete machineconfig 99-worker-heap-dump-disk
```

### Benefits of Migration
✅ Remove all privileged containers  
✅ Standard Kubernetes workflow  
✅ Better security posture  
✅ Easier to manage  
✅ Official Red Hat support  

---

## Quick Decision Guide

**Use Local Storage Operator if:**
- Want official Red Hat support
- Can install operators
- Want automatic disk management
- Prefer PV/PVC over hostPath
- Want to remove privileged containers

**Use MachineConfig + DaemonSet if:**
- Already implemented (your current setup)
- Need full control over mount
- Can accept privileged containers
- Have custom filesystem requirements

**Use Manual Local PV if:**
- Cannot install operators
- Small number of nodes (manual scaling OK)
- Want PV/PVC without operator

---

## Example: Convert Current Setup to Local Storage Operator

See separate document: `docs/LOCAL_STORAGE_MIGRATION.md`

---

**Recommendation:** Migrate to Local Storage Operator for production deployments.
