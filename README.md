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

## Documentation

See complete documentation in `/docs` folder:
- [Implementation Plan](docs/plan.md) - Full implementation roadmap
- [Project Structure Status](docs/project-structure-status.md) - Current status
- [Deployment Guides](docs/deployments/) - Kubernetes and OpenShift guides
- [Development Setup](docs/development/) - Local development guide
- [Commit Details](docs/commits/) - Features, fixes, and refactors

### Implemented Features

Detailed feature documentation in [docs/commits/features/](docs/commits/features/):

- [Bidirectional Mount](docs/commits/features/bidirectional-mount.md) - Host path volume propagation for dump storage
- [Mount Access Controller](docs/commits/features/mount-access-controller.md) - API-based permission management for shared volumes
- [NFS Mount Solution](docs/commits/features/nfs-mount-solution.md) - NFS-based storage eliminating privileged app containers ⭐
- [Mount Recovery](docs/commits/features/mount-recovery.md) - Automatic remount on volume manager restart
- [S3 Uploader](docs/commits/features/s3-uploader.md) - Automatic heap dump backup to S3
- [Pod Priority](docs/commits/features/pod-priority.md) - Guaranteed startup order for infrastructure pods
- [BuildConfig](docs/commits/features/buildconfig.md) - OpenShift Source-to-Image builds
- [OpenShift Updates](docs/commits/features/ocp-updates-summary.md) - OpenShift-specific enhancements
- [Branch Creation](docs/commits/features/opc-branch-creation-summary.md) - OpenShift release branch summary

## Build and Run Locally

```bash
# Build with Maven
cd apps/memoryleak
mvn clean package

# Run locally
java -Xmx256m -Xms128m -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=./heap_dump.hprof -jar target/memory-leak-demo-1.0.0.jar
```

## Build Docker Image

```bash
cd apps/memoryleak
docker build -t memory-leak-demo:1.0.0 .
```

## Deploy to Kubernetes/OpenShift

**Deployment Order:**

1. **Create namespace**
   ```bash
   kubectl apply -f k8s/namespaces.yaml
   ```

2. **Deploy application** (for Kubernetes)
   ```bash
   kubectl apply -f k8s/apps/memoryleak/
   ```

3. **For OpenShift:** Apply additional RBAC and Routes
   ```bash
   oc apply -f openshift/rbac/scc.yaml
   oc apply -f openshift/routes/memory-leak-app.yaml
   ```

4. **Verify deployment**
   ```bash
   kubectl get pods -n memory-leak-demo
   ```

For detailed deployment instructions, see [k8s/README.md](k8s/README.md), [helm/README.md](helm/README.md), or [openshift/README.md](openshift/README.md).

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

The application uses a multi-tier approach with guaranteed startup order. For detailed architecture documentation, see [docs/deployments/](docs/deployments/).

**Key Components:**

1. **Application** (`apps/memoryleak/`) - Spring Boot memory leak demo
2. **Kubernetes Manifests** (`k8s/`) - Complete K8s deployment configs
3. **Helm Charts** (`helm/`) - Templated deployments for multi-environment
4. **OpenShift Configs** (`openshift/`) - OpenShift-specific resources (SCC, Routes, BuildConfigs)
5. **Documentation** (`docs/`) - Complete setup, deployment, and architecture guides

 



## Kubernetes & OpenShift Deployment

### Kubernetes
```bash
# Deploy using kubectl
kubectl apply -f k8s/namespaces.yaml
kubectl apply -f k8s/apps/memoryleak/
```

### Helm
```bash
# Deploy using Helm
helm install memory-leak-demo ./helm -f helm/values-prod.yaml
```

### OpenShift
```bash
# Deploy using OpenShift
oc apply -f openshift/rbac/scc.yaml
oc apply -f k8s/apps/memoryleak/
oc apply -f openshift/routes/memory-leak-app.yaml
```

See detailed guides:
- [Kubernetes Documentation](k8s/README.md)
- [Helm Documentation](helm/README.md)
- [OpenShift Documentation](openshift/README.md)
