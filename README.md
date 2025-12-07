# Memory Leak Demo Application

A Spring Boot application that deliberately causes memory leaks to demonstrate OutOfMemoryError handling and heap dump generation in Kubernetes.

## Features

- Scheduled memory leak that allocates 10MB every 5 seconds
- Automatic heap dump generation on OutOfMemoryError
- Health check endpoints
- PersistentVolume (10Gi) for storing heap dumps
- DaemonSet with bidirectional mount for host path access
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

## Deploy to Kubernetes

```bash
# Step 1: Deploy DaemonSet (creates PriorityClass, PVC, and mounts to /mnt/dump)
kubectl apply -f daemonset-volume.yaml

# Verify DaemonSet is running and ready
kubectl get daemonset -n memory-leak-demo
kubectl get pvc -n memory-leak-demo
kubectl get priorityclass dump-volume-critical

# Step 2: Deploy the application (will wait for DaemonSet via init container)
kubectl apply -f deployment.yaml

# Check the deployment status
kubectl get pods -n memory-leak-demo

# Check init container (should complete quickly if DaemonSet is ready)
kubectl logs -n memory-leak-demo -l app=memory-leak-app -c wait-for-volume-manager

# Watch the application logs
kubectl logs -f -n memory-leak-demo deployment/memory-leak-app

# Check health endpoint
kubectl port-forward -n memory-leak-demo service/memory-leak-service 8080:8080
curl http://localhost:8080/health

# After OOM, access the heap dump
kubectl exec -n memory-leak-demo deployment/memory-leak-app -- ls -lh /dumps/

# Copy heap dump to local machine
POD_NAME=$(kubectl get pod -n memory-leak-demo -l app=memory-leak-app -o jsonpath='{.items[0].metadata.name}')
kubectl cp -n memory-leak-demo $POD_NAME:/dumps/heap_dump.hprof ./heap_dump.hprof

# Alternative: Access from host (if you have node SSH access)
ssh node-hostname
ls -lh /mnt/dump/memory-leak-demo/
```

## Analyze Heap Dump

You can analyze the heap dump using:
- Eclipse Memory Analyzer (MAT)
- VisualVM
- JProfiler
- IntelliJ IDEA Ultimate

## Clean Up

```bash
kubectl delete namespace memory-leak-demo
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

1. **PriorityClass** (`daemonset-volume.yaml`):
   - Priority value: 1,000,000 (high priority)
   - Ensures DaemonSet is scheduled before application pods

2. **DaemonSet** (`daemonset-volume.yaml`):
   - Creates a 10Gi PersistentVolumeClaim
   - Mounts PVC to `/pv-storage` in container
   - Creates bidirectional bind mount to host `/mnt/dump`
   - Creates `.ready` marker file when mount is complete
   - Runs on every node with high priority

3. **Deployment** (`deployment.yaml`):
   - Init container waits for DaemonSet `.ready` marker
   - Application pods mount host path `/mnt/dump/memory-leak-demo`
   - Writes heap dumps to `/dumps` inside container
   - Mapped to PV-backed storage via host path

See documentation:
- [bidirectional-mount.md](bidirectional-mount.md) - Volume architecture
- [pod-priority.md](pod-priority.md) - Priority and startup order
