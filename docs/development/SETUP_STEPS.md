# Complete Setup Steps - Memory Leak Demo Application

## Project Overview
This document contains every step to create, build, deploy, and troubleshoot a Spring Boot application that deliberately causes memory leaks and generates heap dumps in Kubernetes.

---

## Step 1: Project Structure Creation

### 1.1 Create Project Directories
```bash
mkdir -p /home/ozgur/workspace/ai/javadumpmngmt/apps/memoryleak
cd /home/ozgur/workspace/ai/javadumpmngmt/apps/memoryleak
mkdir -p src/main/java/com/example/memoryleak
mkdir -p src/main/resources
```

---

## Step 2: Create Maven Configuration

### 2.1 Create `apps/memoryleak/pom.xml`
Create the Maven project file with Spring Boot dependencies:
- Spring Boot Starter Web (for REST endpoints)
- Spring Boot Starter Actuator (for health checks)
- Java 17
- Spring Boot 3.2.0

**File:** `apps/memoryleak/pom.xml`

---

## Step 3: Create Java Application Files

### 3.1 Create Main Application Class
**File:** `apps/memoryleak/src/main/java/com/example/memoryleak/MemoryLeakApplication.java`

Features:
- `@SpringBootApplication` annotation
- `@EnableScheduling` to enable scheduled tasks
- Main method to start the application

### 3.2 Create Memory Leak Service
**File:** `apps/memoryleak/src/main/java/com/example/memoryleak/MemoryLeakService.java`

Features:
- `@Service` annotation
- `@Scheduled(fixedRate = 5000)` - runs every 5 seconds
- Allocates 10MB of memory each iteration
- Stores data in static List (never garbage collected)
- Fills byte arrays with random data to prevent JVM optimizations
- Prints memory usage statistics to console

Logic:
1. Every 5 seconds, allocate 10MB byte array
2. Fill with random bytes
3. Add to static list (memory leak!)
4. Log current memory usage

### 3.3 Create Health Controller
**File:** `apps/memoryleak/src/main/java/com/example/memoryleak/HealthController.java`

Endpoints:
- `GET /` - Basic status endpoint
- `GET /health` - Returns memory usage statistics
  - usedMemoryMB
  - maxMemoryMB
  - usagePercent

---

## Step 4: Create Application Configuration

### 4.1 Create `apps/memoryleak/application.properties`
**File:** `apps/memoryleak/src/main/resources/application.properties`

Configuration:
- Application name: memory-leak-demo
- Server port: 8080
- Actuator endpoints exposed: health, info, metrics
- Health details: always shown

---

## Step 5: Create Docker Configuration

### 5.1 Create Dockerfile
**File:** `apps/memoryleak/Dockerfile`

Multi-stage build:

**Stage 1: Build**
- Base: maven:3.9-eclipse-temurin-17
- Copy pom.xml and src
- Run: mvn clean package -DskipTests

**Stage 2: Runtime**
- Base: eclipse-temurin:17-jre-alpine
- Create /dumps directory for heap dumps
- Copy JAR from build stage
- Set JAVA_OPTS environment variable:
  - `-Xmx256m` - Maximum heap size 256MB
  - `-Xms128m` - Initial heap size 128MB
  - `-XX:+HeapDumpOnOutOfMemoryError` - Generate heap dump on OOM
  - `-XX:HeapDumpPath=/dumps/heap_dump.hprof` - Heap dump location
  - `-XX:+PrintGCDetails` - Print GC logs
  - `-XX:+PrintGCDateStamps` - Add timestamps to GC logs
  - `-Xloggc:/dumps/gc.log` - GC log file location
- Expose port 8080
- Entrypoint: Run Java with JAVA_OPTS

### 5.2 Create `.dockerignore`
**File:** `apps/memoryleak/.dockerignore`

Excludes from Docker build:
- target/
- .git/
- *.hprof files
- *.log files
- IDE files (.idea/, *.iml, .vscode/)

---

## Step 6: Create Kubernetes Configuration

### 6.1 Create `statefulset-volume.yaml`
**File:** `statefulset-volume.yaml`

Contains 3 Kubernetes resources:

#### Resource 1: PersistentVolumeClaim
- Name: dump-storage-pvc
- Namespace: memory-leak-demo
- Access mode: ReadWriteOnce
- Storage: 10Gi
- StorageClass: default (uses cluster's default storage class)
- Purpose: Provide dedicated storage for heap dumps

#### Resource 2: PriorityClass
- Name: dump-volume-critical
- Value: 1000000 (high priority)
- GlobalDefault: false
- Purpose: Ensure StatefulSet is scheduled before application pods

#### Resource 3: StatefulSet
- Name: dump-volume-manager
- Namespace: memory-leak-demo
- PriorityClass: dump-volume-critical (priority: 1,000,000)
- Purpose: Mount PVC to host path `/mnt/dump` on every node
- Container: busybox
- Privileged: true (required for bind mount)
- Volume mounts:
  1. PVC → `/pv-storage` (PersistentVolume)
  2. `/mnt` → `/host/mnt` (Bidirectional propagation)
- Actions:
  - Creates `/host/mnt/dump` directory
  - Bind mounts `/pv-storage` to `/host/mnt/dump`
  - Sets permissions to 777
  - Creates `/host/mnt/dump/.ready` marker file
  - Displays disk space information
- Readiness probe: Checks for `.ready` marker file
- Tolerations: Runs on all nodes including control plane

### 6.2 Create `deployment.yaml`
**File:** `deployment.yaml`

Contains 3 Kubernetes resources:

#### Resource 1: Namespace
- Name: memory-leak-demo
- Purpose: Isolate application resources

#### Resource 2: Deployment
- Name: memory-leak-app
- Namespace: memory-leak-demo
- Replicas: 1
- Init container:
  - Name: wait-for-volume-manager
  - Image: busybox
  - Purpose: Wait for StatefulSet to be ready
  - Checks for `/mnt/dump/.ready` marker file
  - Loops every 2 seconds until ready
  - Only after init completes, main container starts
- Container configuration:
  - Image: memory-leak-demo:1.0.0
  - ImagePullPolicy: IfNotPresent
  - Port: 8080
  - Environment variables: JAVA_OPTS
  - Resource requests:
    - Memory: 256Mi
    - CPU: 250m
  - Resource limits:
    - Memory: 512Mi
    - CPU: 500m
  - Volume mount: /dumps → /mnt/dump/memory-leak-demo (hostPath)
  - Liveness probe:
    - Path: /health
    - Initial delay: 30s
    - Period: 10s
    - Timeout: 5s
    - Failure threshold: 3
  - Readiness probe:
    - Path: /health
    - Initial delay: 10s
    - Period: 5s
    - Timeout: 3s
    - Failure threshold: 3

#### Resource 3: Service
- Name: memory-leak-service
- Namespace: memory-leak-demo
- Type: ClusterIP
- Port: 8080
- Target port: 8080
- Selector: app=memory-leak-app

---

## Step 7: Create Documentation Files

### 7.1 Create README.md
**File:** `README.md`

Contents:
- Project overview
- Features list
- How it works explanation
- Build instructions
- Docker build instructions
- Kubernetes deployment instructions
- Heap dump retrieval instructions
- Analysis tools list
- Cleanup instructions
- Configuration reference

### 7.2 Create .gitignore
**File:** `.gitignore`

Excludes:
- target/ (Maven build output)
- *.hprof (heap dump files)
- *.log (log files)
- IDE files
- dumps/ directory

---

## Step 8: Build the Application

### 8.1 Build with Maven (Local)
```bash
cd /home/ozgur/workspace/ai/javadumpmngmt/apps/memoryleak
mvn clean package
```

Expected output:
- target/memory-leak-demo-1.0.0.jar

### 8.2 Test Run Locally (Optional)
```bash
java -Xmx256m -Xms128m \
  -XX:+HeapDumpOnOutOfMemoryError \
  -XX:HeapDumpPath=./heap_dump.hprof \
  -jar target/memory-leak-demo-1.0.0.jar
```

Expected behavior:
- Application starts on port 8080
- Every 5 seconds: "Iteration X: Leaked Y MB | Used Memory: ..."
- Crashes after ~2-3 minutes with OutOfMemoryError
- Generates heap_dump.hprof in current directory

---

## Step 9: Build Docker Image

### 9.1 Build the Docker Image
```bash
cd /home/ozgur/workspace/ai/javadumpmngmt/apps/memoryleak
docker build -t memory-leak-demo:1.0.0 .
```

Process:
1. Download Maven base image
2. Copy pom.xml and src
3. Run Maven build
4. Download JRE base image
5. Create /dumps directory
6. Copy JAR file
7. Set environment variables
8. Create final image

### 9.2 Verify Image
```bash
docker images | grep memory-leak-demo
```

Expected output:
```
memory-leak-demo   1.0.0   <image-id>   <time>   <size>
```

### 9.3 Test Docker Image (Optional)
```bash
docker run -p 8080:8080 memory-leak-demo:1.0.0
```

Test endpoint:
```bash
curl http://localhost:8080/health
```

---

## Step 10: Deploy to Kubernetes

### 10.1 Ensure Kubernetes Cluster is Running
```bash
kubectl cluster-info
```

### 10.2 Apply StatefulSet First (Creates PVC and Volume Manager)
```bash
kubectl apply -f statefulset-volume.yaml
```

Expected output:
```
persistentvolumeclaim/dump-storage-pvc created
priorityclass.scheduling.k8s.io/dump-volume-critical created
statefulset.apps/dump-volume-manager created
```

### 10.3 Verify StatefulSet Deployment
```bash
# Check PriorityClass
kubectl get priorityclass dump-volume-critical

# Check PVC status (should be Bound)
kubectl get pvc -n memory-leak-demo

# Check StatefulSet
kubectl get statefulset -n memory-leak-demo

# Check StatefulSet pods (one per node, should be READY 1/1)
kubectl get pods -n memory-leak-demo -l app=dump-volume-manager

# Verify pod priority
kubectl get pod -n memory-leak-demo -l app=dump-volume-manager \
  -o jsonpath='{.items[0].spec.priorityClassName}'

# View StatefulSet logs
kubectl logs -n memory-leak-demo statefulset/dump-volume-manager

# Verify .ready marker file
kubectl exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  cat /host/mnt/dump/.ready
```

Expected StatefulSet log output:
```
Starting dump volume manager...
Mounting PV to host /mnt/dump...
PV is mounted at /pv-storage
Creating bind mount to /host/mnt/dump...
Bind mount created successfully
Permissions set to 777
Available space on /mnt/dump:
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb        10G   0     10G   0% /host/mnt/dump
Mount information:
/dev/sdb on /host/mnt/dump type ext4 (rw,relatime)
Volume manager running. Keeping pod alive...
```

Expected .ready file content:
```
ready
```

### 10.4 Apply Application Deployment
```bash
kubectl apply -f deployment.yaml
```

Expected output:
```
namespace/memory-leak-demo configured (or created)
deployment.apps/memory-leak-app created
service/memory-leak-service created
```

### 10.5 Verify Application Deployment
```bash
# Check namespace
kubectl get namespace memory-leak-demo

# Check all PVCs
kubectl get pvc -n memory-leak-demo

# Check all resources (including PriorityClass)
kubectl get all -n memory-leak-demo
kubectl get priorityclass

# Check deployment
kubectl get deployment -n memory-leak-demo

# Check application pods (may show Init:0/1 briefly while waiting)
kubectl get pods -n memory-leak-demo -l app=memory-leak-app

# Check init container logs (should show waiting then success)
kubectl logs -n memory-leak-demo -l app=memory-leak-app -c wait-for-volume-manager

# Check service
kubectl get service -n memory-leak-demo

# Verify pod priorities
kubectl get pods -n memory-leak-demo -o custom-columns=NAME:.metadata.name,PRIORITY:.spec.priority
```

Expected init container output:
```
Waiting for dump volume manager to be ready...
Volume manager is ready, proceeding with application startup
```

---

## Step 11: Monitor the Application

### 11.1 Watch Pod Status
```bash
kubectl get pods -n memory-leak-demo -w
```

### 11.2 Stream Application Logs
```bash
kubectl logs -f -n memory-leak-demo deployment/memory-leak-app
```

Expected log output:
```
Iteration 1: Leaked 10 MB | Used Memory: 45 MB / 241 MB (18.67%)
Iteration 2: Leaked 20 MB | Used Memory: 55 MB / 241 MB (22.82%)
Iteration 3: Leaked 30 MB | Used Memory: 65 MB / 241 MB (26.97%)
...
Iteration 20: Leaked 200 MB | Used Memory: 225 MB / 241 MB (93.36%)
Iteration 21: Leaked 210 MB | Used Memory: 235 MB / 241 MB (97.51%)
java.lang.OutOfMemoryError: Java heap space
```

### 11.3 Check Pod Events
```bash
kubectl describe pod -n memory-leak-demo -l app=memory-leak-app
```

Look for:
- OOMKilled status
- Container restart events

### 11.4 Port Forward to Test Endpoint (Before OOM)
```bash
kubectl port-forward -n memory-leak-demo service/memory-leak-service 8080:8080
```

In another terminal:
```bash
# Check home endpoint
curl http://localhost:8080/

# Check health endpoint
curl http://localhost:8080/health
```

Expected health response:
```json
{
  "status": "UP",
  "usedMemoryMB": 150,
  "maxMemoryMB": 241,
  "usagePercent": "62.24"
}
```

---

## Step 12: Retrieve Heap Dump

### 12.1 Wait for OOM to Occur
Monitor logs until you see OutOfMemoryError (approximately 2-3 minutes).

### 12.2 Get Pod Name
```bash
POD_NAME=$(kubectl get pod -n memory-leak-demo -l app=memory-leak-app -o jsonpath='{.items[0].metadata.name}')
echo $POD_NAME
```

### 12.3 List Files in /dumps Directory
```bash
kubectl exec -n memory-leak-demo $POD_NAME -- ls -lh /dumps/
```

Expected output:
```
total 250M
-rw-------    1 root     root      245M Dec  7 18:45 heap_dump.hprof
-rw-r--r--    1 root     root        5M Dec  7 18:45 gc.log
```

### 12.3b Verify Files on Host (Alternative)
```bash
# Check via StatefulSet
kubectl exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  ls -lh /host/mnt/dump/memory-leak-demo/

# If you have SSH access to the node
ssh node-hostname
ls -lh /mnt/dump/memory-leak-demo/
```

### 12.4 Copy Heap Dump to Local Machine
```bash
kubectl cp -n memory-leak-demo $POD_NAME:/dumps/heap_dump.hprof ./heap_dump.hprof
```

### 12.5 Copy GC Log (Optional)
```bash
kubectl cp -n memory-leak-demo $POD_NAME:/dumps/gc.log ./gc.log
```

### 12.6 Verify Local Files
```bash
ls -lh heap_dump.hprof
```

---

## Step 13: Analyze Heap Dump

### 13.1 Using Eclipse Memory Analyzer (MAT)
1. Download MAT: https://www.eclipse.org/mat/downloads.php
2. Open MAT
3. File → Open Heap Dump
4. Select heap_dump.hprof
5. Choose "Leak Suspects Report"
6. Review:
   - Dominator Tree (largest objects)
   - Histogram (object counts)
   - Leak suspects

### 13.2 Using VisualVM
```bash
visualvm
```
1. File → Load → Select heap_dump.hprof
2. View Classes tab
3. Look for byte[] arrays
4. Check references

### 13.3 Using jhat (Command Line)
```bash
jhat heap_dump.hprof
```
Open browser: http://localhost:7000

### 13.4 What to Look For
- Large number of byte[] objects
- MemoryLeakService$memoryLeakList holding references
- Static List preventing garbage collection

---

## Step 14: Troubleshooting

### 14.1 Pod Not Starting (Stuck in Init:0/1)
```bash
# Check init container logs
kubectl logs -n memory-leak-demo -l app=memory-leak-app -c wait-for-volume-manager

# Check if StatefulSet is ready
kubectl get pods -n memory-leak-demo -l app=dump-volume-manager

# Check if .ready file exists
kubectl exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  ls -la /host/mnt/dump/.ready

# Describe pod for events
kubectl describe pod -n memory-leak-demo -l app=memory-leak-app
```

Common issues:
- Init container waiting: StatefulSet not ready yet (check StatefulSet logs)
- StatefulSet failed: Check bind mount creation (privileged mode required)
- .ready file missing: StatefulSet script didn't complete
- Image not found: Build and tag image correctly
- ImagePullBackOff: Check imagePullPolicy
- PVC pending: Check storage class availability

### 14.2 No Heap Dump Generated
Check:
1. JAVA_OPTS configured correctly
2. /dumps directory is writable
3. HostPath is mounted correctly
4. StatefulSet is running and bind mount is successful
5. Sufficient disk space on PV

Verify:
```bash
# Check application pod
kubectl exec -n memory-leak-demo $POD_NAME -- ls -la /dumps/
kubectl exec -n memory-leak-demo $POD_NAME -- df -h /dumps/

# Check StatefulSet
kubectl logs -n memory-leak-demo statefulset/dump-volume-manager

# Check PVC status
kubectl get pvc -n memory-leak-demo dump-storage-pvc

# Check available space on PV
kubectl exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  df -h /host/mnt/dump
```

### 14.3 Application Not Crashing
- Check heap size: Should be 256MB
- Verify scheduled task is running
- Check logs for "Iteration" messages

### 14.4 Cannot Access Pod After Crash
If pod restarts before you can copy heap dump:
```bash
# Method 1: Access via StatefulSet (always running)
kubectl exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  ls -lh /host/mnt/dump/memory-leak-demo/

kubectl exec -n memory-leak-demo statefulset/dump-volume-manager -- \
  cat /host/mnt/dump/memory-leak-demo/heap_dump.hprof > heap_dump.hprof

# Method 2: Copy from PV via new debug pod
kubectl run -it --rm copy-dump \
  --image=busybox \
  --restart=Never \
  -n memory-leak-demo \
  --overrides='{"spec":{"volumes":[{"name":"pv","persistentVolumeClaim":{"claimName":"dump-storage-pvc"}}],"containers":[{"name":"copy","image":"busybox","stdin":true,"tty":true,"volumeMounts":[{"name":"pv","mountPath":"/pv"}]}]}}' \
  -- ls -lh /pv/memory-leak-demo/

# Method 3: SSH to node if available
ssh node-hostname
ls -lh /mnt/dump/memory-leak-demo/
cp /mnt/dump/memory-leak-demo/heap_dump.hprof /tmp/
```

---

## Step 15: Cleanup

### 15.1 Delete Kubernetes Resources
```bash
# Delete application deployment first
kubectl delete -f deployment.yaml

# Delete StatefulSet and PVC
kubectl delete -f statefulset-volume.yaml

# Or delete entire namespace (deletes everything)
kubectl delete namespace memory-leak-demo
```

This deletes:
- Namespace
- Deployment
- StatefulSet
- Service
- Pods
- PVC (PersistentVolumeClaim)
- PV (if dynamic provisioning with Delete reclaim policy)

### 15.2 Verify Cleanup
```bash
kubectl get namespace memory-leak-demo  # Should show "not found"
```

### Step 3: Clean Local Files (Optional)
```bash
cd /home/ozgur/workspace/ai/javadumpmngmt/apps/memoryleak
rm -f heap_dump.hprof gc.log
rm -rf target/
```

### 15.4 Remove Docker Image (Optional)
```bash
docker rmi memory-leak-demo:1.0.0
```

---

## Step 16: Advanced Configurations (Optional)

### 16.1 Adjust Memory Leak Speed
Edit `MemoryLeakService.java`:
```java
@Scheduled(fixedRate = 3000)  // Faster: 3 seconds
// or
@Scheduled(fixedRate = 10000) // Slower: 10 seconds

int size = 20 * 1024 * 1024;  // Larger: 20 MB per iteration
// or
int size = 5 * 1024 * 1024;   // Smaller: 5 MB per iteration
```

### 16.2 Change Heap Size
Edit `deployment.yaml`:
```yaml
env:
- name: JAVA_OPTS
  value: "-Xmx512m -Xms256m ..."  # Larger heap, takes longer to crash
```

### 16.3 Add NodePort Service (External Access)
Add to `deployment.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: memory-leak-nodeport
  namespace: memory-leak-demo
spec:
  type: NodePort
  ports:
  - port: 8080
    targetPort: 8080
    nodePort: 30080
  selector:
    app: memory-leak-app
```

Access via: http://<node-ip>:30080/health

### 16.4 Enable Prometheus Metrics
Add to `pom.xml`:
```xml
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

Add to `application.properties`:
```properties
management.endpoints.web.exposure.include=health,info,metrics,prometheus
management.metrics.export.prometheus.enabled=true
```

---

## Step 17: Timeline Summary

**Expected Application Lifecycle:**

- **T+0s**: Application starts
- **T+5s**: Iteration 1 - 10 MB leaked
- **T+10s**: Iteration 2 - 20 MB leaked
- **T+15s**: Iteration 3 - 30 MB leaked
- **T+60s**: Iteration 12 - 120 MB leaked (~50% memory used)
- **T+90s**: Iteration 18 - 180 MB leaked (~75% memory used)
- **T+120s**: Iteration 24 - 240 MB leaked (~95% memory used)
- **T+125s**: **OutOfMemoryError occurs**
- **T+126s**: Heap dump generated to /dumps/heap_dump.hprof
- **T+127s**: Application crashes
- **T+130s**: Kubernetes restarts pod (if not disabled)

---

## Step 18: Key Files Summary

| File | Purpose | Lines |
|------|---------|-------|
| apps/memoryleak/pom.xml | Maven configuration | 47 |
| apps/memoryleak/MemoryLeakApplication.java | Main application entry point | 15 |
| apps/memoryleak/MemoryLeakService.java | Memory leak logic | 44 |
| apps/memoryleak/HealthController.java | REST endpoints | 35 |
| apps/memoryleak/application.properties | Spring Boot configuration | 7 |
| apps/memoryleak/Dockerfile | Container image definition | 22 |
| openshift-rbac.yaml | SCC, ServiceAccount, RBAC | 76 |
| statefulset-volume.yaml | PriorityClass, PVC, Volume Manager StatefulSet | 140 |
| s3-uploader-statefulset.yaml | ConfigMap, Secret, S3 Uploader StatefulSet | 317 |
| deployment.yaml | Kubernetes deployment with init container | 107 |
| openshift-route.yaml | OpenShift Route with TLS | 22 |
| README.md | Quick start documentation | 150+ |
| OPENSHIFT.md | OpenShift-specific deployment guide | 343 |
| bidirectional-mount.md | Volume architecture explanation | 413 |
| pod-priority.md | Pod priority and startup order | 309 |
| mount-recovery.md | Bind mount recovery guide | 384 |
| s3-uploader.md | S3 uploader configuration guide | 550 |
| ocp-updates-summary.md | OpenShift migration summary | 543 |
| session-summary.md | Complete session features summary | 723 |
| SETUP_STEPS.md | Complete step-by-step guide | 900+ |
| apps/memoryleak/.dockerignore | Docker build exclusions | 10 |
| .gitignore | Git exclusions | 9 |

---

## Conclusion

## Step 19: Summary

This completes all steps from project creation through deployment, monitoring, heap dump retrieval, and cleanup. The application demonstrates:
- Spring Boot scheduled tasks
- Memory leak patterns
- OutOfMemoryError handling
- Heap dump generation
- OpenShift deployment with SCC and RBAC
- StatefulSet with privileged operations
- PersistentVolume (10Gi) with default StorageClass
- Bidirectional mount propagation for host path access
- Pod priority classes (1,000,000) for scheduling control
- Init containers for dependency management
- Readiness and liveness probes
- Bind mount recovery and monitoring
- **Automatic S3 backup with file stability detection**
- Health monitoring
- Container resource management
- Advanced volume management techniques

**Storage Architecture:**
- PersistentVolumeClaim: 10Gi using default storage class
- Volume Manager StatefulSet: Mounts PVC and binds to host `/mnt/dump`
- Application: Writes to `/dumps` → backed by PV via host path
- S3 Uploader StatefulSet: Monitors `/mnt/dump` and uploads to S3
- Access: Via kubectl/oc, host SSH, StatefulSet, or S3

**Startup Order Guarantee:**
- PriorityClass: 1,000,000 for StatefulSets (vs default 0 for app)
- Readiness marker: Volume manager creates `.ready` file
- Init containers: Application and S3 uploader wait for `.ready` file
- Result: StatefulSets always ready before application starts

**Automatic Features:**
- Mount recovery: Remounts within 30 seconds if lost
- S3 backup: Uploads completed heap dumps with metadata
- File stability: Waits until files stop growing before upload
- Duplicate prevention: Tracks uploaded files

**Created:** 2025-12-07T18:59:36.826Z  
**Updated:** 2025-12-08T07:33:29.954Z
