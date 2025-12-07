# Memory Leak Demo Application - OpenShift

A Spring Boot application that deliberately causes memory leaks to demonstrate OutOfMemoryError handling and heap dump generation in **OpenShift Container Platform**.

> **Note:** This is the OpenShift-specific branch. For vanilla Kubernetes, see the `master` branch.

## Features

- Scheduled memory leak that allocates 10MB every 5 seconds
- Automatic heap dump generation on OutOfMemoryError
- Health check endpoints
- PersistentVolume (10Gi) for storing heap dumps
- DaemonSet with bidirectional mount for host path access
- OpenShift SecurityContextConstraints (SCC) for privileged operations
- OpenShift Route with TLS termination
- ServiceAccount with proper RBAC
- Pod priority to guarantee DaemonSet runs before application
- Init container to ensure storage readiness
- GC logging enabled

## How It Works

The application uses a scheduled task that runs every 5 seconds, allocating 10MB of memory each time and storing it in a static list that never gets garbage collected. With a 256MB heap, it will crash in approximately 2-3 minutes.

## Build and Run Locally

```bash
# Build with Maven
mvn clean package

# Run locally
java -Xmx256m -Xms128m -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=./heap_dump.hprof -jar target/memory-leak-demo-1.0.0.jar
```

## Build Docker Image

```bash
docker build -t memory-leak-demo:1.0.0 .
```

## Deploy to OpenShift

```bash
# Login to OpenShift (cluster-admin required for SCC creation)
oc login -u admin

# Step 1: Create SecurityContextConstraints, ServiceAccount, and RBAC
oc apply -f openshift-rbac.yaml

# Verify SCC
oc get scc dump-volume-privileged
oc get sa -n memory-leak-demo dump-volume-manager

# Step 2: Deploy DaemonSet (creates PriorityClass, PVC, and mounts to /mnt/dump)
oc apply -f daemonset-volume.yaml

# Verify DaemonSet is running and ready
oc get daemonset -n memory-leak-demo
oc get pvc -n memory-leak-demo
oc get priorityclass dump-volume-critical

# Step 3: Deploy the application (will wait for DaemonSet via init container)
oc apply -f deployment.yaml

# Check the deployment status
oc get pods -n memory-leak-demo

# Check init container (should complete quickly if DaemonSet is ready)
oc logs -n memory-leak-demo -l app=memory-leak-app -c wait-for-volume-manager

# Watch the application logs
oc logs -f -n memory-leak-demo deployment/memory-leak-app

# Step 4: Create Route for external access
oc apply -f openshift-route.yaml

# Get Route URL
ROUTE_URL=$(oc get route -n memory-leak-demo memory-leak-app -o jsonpath='{.spec.host}')
echo "Application URL: https://$ROUTE_URL"

# Check health endpoint
curl -k https://$ROUTE_URL/health

# After OOM, access the heap dump
POD_NAME=$(oc get pod -n memory-leak-demo -l app=memory-leak-app -o jsonpath='{.items[0].metadata.name}')
oc exec -n memory-leak-demo $POD_NAME -- ls -lh /dumps/

# Copy heap dump to local machine
oc cp -n memory-leak-demo $POD_NAME:/dumps/heap_dump.hprof ./heap_dump.hprof

# Alternative: Access from DaemonSet
oc exec -n memory-leak-demo daemonset/dump-volume-manager -- \
  ls -lh /host/mnt/dump/memory-leak-demo/
```

## Analyze Heap Dump

You can analyze the heap dump using:
- Eclipse Memory Analyzer (MAT)
- VisualVM
- JProfiler
- IntelliJ IDEA Ultimate

## Clean Up

```bash
oc delete namespace memory-leak-demo
```

## Configuration

- **Heap Size**: 256MB (configurable via JAVA_OPTS)
- **Memory Leak Rate**: 10MB every 5 seconds
- **Expected Crash Time**: ~2-3 minutes after startup
- **Heap Dump Location**: `/dumps/heap_dump.hprof` inside the container
- **Host Path**: `/mnt/dump/memory-leak-demo/` on Kubernetes nodes
- **PersistentVolume**: 10Gi storage using default storage class

## Architecture

The application uses a three-tier approach with guaranteed startup order:

1. **SecurityContextConstraints & RBAC** (`openshift-rbac.yaml`):
   - SCC: `dump-volume-privileged` for DaemonSet privileged operations
   - ServiceAccount: `dump-volume-manager`
   - ClusterRole & ClusterRoleBinding for SCC usage

2. **PriorityClass** (`daemonset-volume.yaml`):
   - Priority value: 1,000,000 (high priority)
   - Ensures DaemonSet is scheduled before application pods

3. **DaemonSet** (`daemonset-volume.yaml`):
   - Uses ServiceAccount with SCC permissions
   - Creates a 10Gi PersistentVolumeClaim
   - Mounts PVC to `/pv-storage` in container
   - Creates bidirectional bind mount to host `/mnt/dump`
   - Creates `.ready` marker file when mount is complete
   - Runs on every node with high priority

4. **Deployment** (`deployment.yaml`):
   - Init container waits for DaemonSet `.ready` marker
   - Application pods mount host path `/mnt/dump/memory-leak-demo`
   - Writes heap dumps to `/dumps` inside container
   - Mapped to PV-backed storage via host path

5. **Route** (`openshift-route.yaml`):
   - OpenShift Route with TLS edge termination
   - External access to application

See documentation:
- [OPENSHIFT.md](OPENSHIFT.md) - OpenShift-specific deployment guide
- [bidirectional-mount.md](bidirectional-mount.md) - Volume architecture
- [pod-priority.md](pod-priority.md) - Priority and startup order
