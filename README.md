# Memory Leak Demo Application - OpenShift

A Spring Boot application that deliberately causes memory leaks to demonstrate OutOfMemoryError handling and heap dump generation in **OpenShift Container Platform**.

> **Note:** This is the OpenShift-specific final release canditade branch. For the first vanilla Kubernetes draft version see the `draft' tag

## Features

- Scheduled memory leak that allocates 10MB every 5 seconds
- Automatic heap dump generation on OutOfMemoryError
- Health check endpoints
- PersistentVolume (10Gi) for storing heap dumps
- StatefulSet with bidirectional mount for host path access
- **Automatic S3 backup** - Second StatefulSet uploads heap dumps to S3
- OpenShift SecurityContextConstraints (SCC) for privileged operations
- OpenShift Route with TLS termination
- ServiceAccount with proper RBAC
- Pod priority to guarantee StatefulSet runs before application
- Init container to ensure storage readiness
- **Bind mount recovery** - Automatic remount if volume manager restarts
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

# Step 2: Deploy StatefulSet (creates PriorityClass, PVC, and mounts to /mnt/dump)
oc apply -f statefulset-volume.yaml

# Verify StatefulSet is running and ready
oc get statefulset -n memory-leak-demo
oc get pvc -n memory-leak-demo
oc get priorityclass dump-volume-critical

# Step 3: (Optional) Deploy S3 Uploader for automatic backup
# Edit credentials first
vi s3-uploader-statefulset.yaml

oc apply -f s3-uploader-statefulset.yaml

# Verify S3 uploader
oc get statefulset -n memory-leak-demo heap-dump-s3-uploader
oc logs -n memory-leak-demo -l app=s3-uploader

# Step 4: Deploy the application (will wait for StatefulSet via init container)
oc apply -f deployment.yaml

# Check the deployment status
oc get pods -n memory-leak-demo

# Check init container (should complete quickly if StatefulSet is ready)
oc logs -n memory-leak-demo -l app=memory-leak-app -c wait-for-volume-manager

# Watch the application logs
oc logs -f -n memory-leak-demo deployment/memory-leak-app

# Step 5: Create Route for external access
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

# Alternative: Access from StatefulSet
oc exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  ls -lh /host/mnt/dump/memory-leak-demo/

# If S3 uploader is enabled, check S3 bucket
aws s3 ls s3://heap-dumps/memory-leak-demo/ --recursive --human-readable
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

The application uses a multi-tier approach with guaranteed startup order:

1. **SecurityContextConstraints & RBAC** (`openshift-rbac.yaml`):
   - SCC: `dump-volume-privileged` for StatefulSet privileged operations
   - ServiceAccount: `dump-volume-manager`
   - ClusterRole & ClusterRoleBinding for SCC usage

2. **PriorityClass** (`statefulset-volume.yaml`):
   - Priority value: 1,000,000 (high priority)
   - Ensures StatefulSets are scheduled before application pods

3. **Volume Manager StatefulSet** (`statefulset-volume.yaml`):
   - Uses ServiceAccount with SCC permissions
   - Creates a 10Gi PersistentVolumeClaim
   - Mounts PVC to `/pv-storage` in container
   - Creates bidirectional bind mount to host `/mnt/dump`
   - Creates `.ready` marker file when mount is complete
   - Monitors mount every 30 seconds with auto-recovery
   - Runs on every node with high priority

4. **S3 Uploader StatefulSet** (`s3-uploader-statefulset.yaml`) - *Optional*:
   - Waits for volume manager `.ready` marker via init container
   - Monitors `/mnt/dump` recursively for `.hprof` files
   - Detects file stability (waits until file stops growing)
   - Uploads completed heap dumps to S3 with node metadata
   - Tracks uploaded files to prevent duplicates
   - Runs on every node with low resource usage

5. **Application Deployment** (`deployment.yaml`):
   - Init container waits for volume manager `.ready` marker
   - Application pods mount host path `/mnt/dump/memory-leak-demo`
   - Writes heap dumps to `/dumps` inside container
   - Mapped to PV-backed storage via host path

6. **OpenShift Route** (`openshift-route.yaml`):
   - OpenShift Route with TLS edge termination
   - External access to application

See documentation:
- [OPENSHIFT.md](OPENSHIFT.md) - OpenShift-specific deployment guide
- [bidirectional-mount.md](bidirectional-mount.md) - Volume architecture
- [pod-priority.md](pod-priority.md) - Priority and startup order
- [mount-recovery.md](mount-recovery.md) - Bind mount recovery details
- [s3-uploader.md](s3-uploader.md) - S3 automatic backup configuration
- [session-summary.md](session-summary.md) - Complete feature summary
