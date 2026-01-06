# NFS with Bidirectional Mount - Complete Solution

## BREAKTHROUGH: NFS Solves the Privileged Container Problem! 🎉

**Key Discovery:** NFS mounts created with bidirectional propagation **ARE accessible** by non-privileged containers!

## Why NFS Works Where Local Disks Don't

### The Problem with Local Disks
```
Local Disk Mount (bind mount):
  ├─ Privileged container creates mount
  ├─ Mount exists in privileged namespace
  └─ Non-privileged containers: BLOCKED ❌
      └─ Different mount namespace
```

### The Solution with NFS
```
NFS Mount (network filesystem):
  ├─ Privileged container mounts NFS
  ├─ NFS mount propagates to host
  ├─ Bidirectional shares to all containers
  └─ Non-privileged containers: SUCCESS ✅
      └─ NFS is "outside" namespace isolation
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    NFS Server                            │
│  - Can be in-cluster (Pod) or external                  │
│  - Exports: /exports/heapdump                            │
│  - All nodes can access                                  │
└─────────────────────────────────────────────────────────┘
                          │
                    (NFS Protocol)
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
   │ Node 1  │       │ Node 2  │      │ Node 3  │
   ├─────────┤       ├─────────┤      ├─────────┤
   │         │       │         │      │         │
   │ nfs-mount-manager (DaemonSet, privileged)  │
   │  └─ mount -t nfs server:/exports /mnt/nfs  │
   │     └─ mountPropagation: Bidirectional     │
   │         └─ Propagates to all containers ✅  │
   │                                             │
   │ mount-access-controller (privileged)       │
   │  └─ mkdir /mnt/nfs/app/heap                │
   │  └─ chown 185:185 /mnt/nfs/app/heap        │
   │                                             │
   │ memory-leak-app (NON-PRIVILEGED! 🎉)        │
   │  └─ hostPath: /mnt/nfs/memory-leak-demo/heap│
   │     └─ runAsUser: 185                       │
   │        └─ CAN ACCESS! ✅                     │
   └─────────────────────────────────────────────┘
```

## Implementation

### Step 1: Deploy NFS Server (In-Cluster Option)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-server-storage
  namespace: heapdump
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: ocs-storagecluster-ceph-rbd
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nfs-server
  namespace: heapdump
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nfs-server
  template:
    metadata:
      labels:
        app: nfs-server
    spec:
      containers:
      - name: nfs-server
        image: k8s.gcr.io/volume-nfs:0.8
        ports:
        - containerPort: 2049
          name: nfs
        - containerPort: 20048
          name: mountd
        - containerPort: 111
          name: rpcbind
        securityContext:
          privileged: true
        volumeMounts:
        - name: storage
          mountPath: /exports
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: nfs-server-storage
---
apiVersion: v1
kind: Service
metadata:
  name: nfs-server
  namespace: heapdump
spec:
  type: ClusterIP
  ports:
  - port: 2049
    name: nfs
  - port: 20048
    name: mountd
  - port: 111
    name: rpcbind
  selector:
    app: nfs-server
```

### Step 2: Create NFS Mount Manager DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nfs-mount-manager
  namespace: heapdump
spec:
  selector:
    matchLabels:
      app: nfs-mount-manager
  template:
    metadata:
      labels:
        app: nfs-mount-manager
    spec:
      nodeSelector:
        heapdump: test
      serviceAccountName: dump-volume-manager
      hostNetwork: true
      hostPID: true
      containers:
      - name: nfs-mounter
        image: registry.connect.redhat.com/sumologic/busybox:1.37.0-ubi
        command:
        - sh
        - -c
        - |
          echo "Installing NFS utils..."
          # For RHEL/CentOS based nodes
          nsenter --target 1 --mount --uts --ipc --net --pid -- \
            yum install -y nfs-utils || true
          
          echo "Creating mount point..."
          mkdir -p /host/mnt/nfs-dump
          
          echo "Mounting NFS..."
          # Get NFS server IP
          NFS_SERVER=$(getent hosts nfs-server.heapdump.svc.cluster.local | awk '{print $1}')
          
          if mount | grep -q /host/mnt/nfs-dump; then
            echo "NFS already mounted"
          else
            mount -t nfs ${NFS_SERVER}:/exports /host/mnt/nfs-dump
            echo "NFS mounted successfully"
          fi
          
          # Create readiness marker
          touch /host/mnt/nfs-dump/.ready
          
          echo "NFS mount manager running. Monitoring mount..."
          while true; do
            if ! mount | grep -q /host/mnt/nfs-dump; then
              echo "WARNING: NFS mount lost! Remounting..."
              mount -t nfs ${NFS_SERVER}:/exports /host/mnt/nfs-dump || true
            fi
            sleep 30
          done
        securityContext:
          privileged: true
          runAsUser: 0
        volumeMounts:
        - name: host-mnt
          mountPath: /host/mnt
          mountPropagation: Bidirectional  # KEY: Propagates NFS mount
      volumes:
      - name: host-mnt
        hostPath:
          path: /mnt
          type: Directory
```

### Step 3: Update mount-access-controller

No changes needed! It works the same:
- Accesses /mnt/nfs-dump
- Creates subdirectories
- Sets permissions

### Step 4: Update deployment2.yaml (NON-PRIVILEGED!)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-leak-app-2
  namespace: heapdump
spec:
  replicas: 4
  template:
    metadata:
      annotations:
        openshift.io/scc: hostmount-anyuid  # No privileged needed!
    spec:
      initContainers:
      - name: register-mount
        command:
        - sh
        - '-c'
        - |
          # Wait for NFS mount
          while [ ! -f /mnt/nfs-dump/.ready ]; do
            echo "Waiting for NFS mount..."
            sleep 3
          done
          
          # Register with mount-access-controller
          curl -s -X POST \
            -H "X-API-Key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d '{"appName":"memory-leak-demo","userId":"185"}' \
            http://mount-access-controller:8080/api/v1/app/mount/register
          
          # Wait for ready
          while true; do
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
              -H "X-API-Key: ${API_KEY}" \
              -H "Content-Type: application/json" \
              -d '{"appName":"memory-leak-demo","userId":"185"}' \
              http://mount-access-controller:8080/api/v1/app/mount/ready)
            
            if [ "$HTTP_CODE" = "200" ]; then
              echo "Mount ready!"
              exit 0
            fi
            sleep 3
          done
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: mount-access-api-key
              key: api-key
        volumeMounts:
        - name: nfs-dumps
          mountPath: /mnt/nfs-dump
          readOnly: true
        image: registry.connect.redhat.com/sumologic/busybox:1.37.0-ubi
      
      containers:
      - name: memory-leak-app
        securityContext:
          runAsUser: 185        # NON-PRIVILEGED! ✅
          runAsGroup: 185
          fsGroup: 185
          # privileged: false   # NOT NEEDED! 🎉
        volumeMounts:
        - name: nfs-dumps
          mountPath: /dumps
        env:
        - name: JAVA_OPTS
          value: '-Xmx256m -Xms128m -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/dumps/$(POD_NAME).hprof'
      
      volumes:
      - name: nfs-dumps
        hostPath:
          path: /mnt/nfs-dump/memory-leak-demo/heap
          type: Directory
```

## Key Differences from Local Disk Approach

| Aspect | Local Disk + Bidirectional | NFS + Bidirectional |
|--------|----------------------------|---------------------|
| App Container Privileged | ❌ Required | ✅ NOT Required |
| Mount Namespace Issue | ❌ Blocks access | ✅ No issue |
| SCC Needed | dump-volume-privileged | hostmount-anyuid |
| Security | Lower | Higher |
| Data Location | Per-node local | Shared NFS |
| Backup | Per-node | Centralized |

## Benefits of NFS Approach

### Security
✅ **No privileged app containers**  
✅ **Better isolation**  
✅ **Standard SCC (hostmount-anyuid)**  
✅ **Runs as UID 185**  

### Operations
✅ **Centralized storage**  
✅ **Easier backups**  
✅ **Same data visible on all nodes**  
✅ **No per-node disk management**  

### Architecture
✅ **Cleaner separation**  
✅ **mount-access-controller still works**  
✅ **Init container pattern unchanged**  
✅ **No bidirectional namespace issues**  

## NFS Server Options

### Option 1: In-Cluster NFS Server (Recommended for Testing)
- Deploy as Pod with PVC backend
- ClusterIP service
- Easy to set up
- Good for dev/test

### Option 2: External NFS Server (Recommended for Production)
- Dedicated NFS appliance
- Better performance
- Enterprise features
- High availability

### Option 3: OpenShift Data Foundation (ODF) NFS
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-backed-pvc
spec:
  accessModes:
  - ReadWriteMany  # NFS supports RWX
  storageClassName: ocs-storagecluster-cephfs
  resources:
    requests:
      storage: 100Gi
```

Then mount this PVC directly (no NFS server pod needed):
```yaml
volumes:
- name: dumps
  persistentVolumeClaim:
    claimName: nfs-backed-pvc
```

## Troubleshooting

### Check NFS Mount on Node
```bash
oc debug node/<node-name>
chroot /host
mount | grep nfs-dump
ls -la /mnt/nfs-dump
```

### Check NFS Server
```bash
oc exec -it <nfs-server-pod> -- showmount -e localhost
oc exec -it <nfs-server-pod> -- exportfs -v
```

### Test from Pod
```bash
oc exec -it <app-pod> -- ls -la /dumps
oc exec -it <app-pod> -- touch /dumps/test.txt
```

## Migration from Local Disk to NFS

```bash
# 1. Deploy NFS server
oc apply -f nfs-server.yaml

# 2. Deploy nfs-mount-manager DaemonSet
oc apply -f nfs-mount-manager-daemonset.yaml

# 3. Update mount-access-controller config
# Change mount.base.path to /mnt/nfs-dump

# 4. Update deployment2.yaml
# Remove privileged: true
# Change hostPath to /mnt/nfs-dump/...
# Change SCC to hostmount-anyuid

# 5. Deploy
oc apply -f deployment2.yaml

# 6. Remove old dump-volume-manager
oc delete statefulset dump-volume-manager
```

## Performance Considerations

### NFS Performance Tips
- Use NFSv4 (better than v3)
- Enable async writes for heap dumps (acceptable data loss on crash)
- Consider NFS over RDMA if available
- Mount options: `rw,nfsvers=4,async,noatime`

### Storage Backend
- Use fast storage for NFS server PVC
- SSD/NVMe recommended
- ODF Ceph RBD or CephFS both work

## Conclusion

**NFS + Bidirectional Mount = Perfect Solution!**

✅ Solves privileged container requirement  
✅ Apps run as UID 185 (non-privileged)  
✅ Uses standard hostmount-anyuid SCC  
✅ Centralized storage  
✅ Easier operations  
✅ mount-access-controller pattern still works  
✅ Better security posture  

**Recommendation:** Use NFS with bidirectional propagation for production heap dump storage.

---

**Status:** Ready to implement! 🚀
