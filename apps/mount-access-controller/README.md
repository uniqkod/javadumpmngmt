# Mount Access Controller

A Spring Boot REST API application that manages volume mount access rights operations based on registered applications and provides a readiness API for clients.

## Overview

The Mount Access Controller runs as a privileged StatefulSet in Kubernetes/OpenShift, managing access permissions for shared volume mounts across multiple applications running with different user IDs.

## Features

- **Mount Registration**: Register applications as mount owners with specific user IDs
- **Mount Readiness Check**: Verify mount point access for applications
- **API Key Authentication**: Secure access using Kubernetes secrets
- **Health Endpoints**: Kubernetes-compatible health, readiness, and liveness probes
- **OpenAPI Documentation**: Swagger UI for API exploration
- **Node-local Routing**: Traffic routed to pod on the same node for performance

## API Endpoints

### Mount Management
- `POST /api/v1/app/mount/register` - Register an application as mount owner
  - Request: `{"appName": "string", "userId": "string"}`
  - Creates directories and sets ownership

- `POST /api/v1/app/mount/ready` - Check if mount is ready
  - Request: `{"appName": "string", "userId": "string"}`
  - Returns: HTTP 200 if ready, HTTP 401 otherwise

### Health Checks
- `GET /api/v1/health` - Health status
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe

### Monitoring
- `GET /actuator/health` - Spring Actuator health
- `GET /actuator/metrics` - Prometheus metrics

## Configuration

### Environment Variables
- `API_KEY` - API key for authentication (from Kubernetes secret)
- `MOUNT_BASE_PATH` - Base path for volume mounts (default: `/mnt/dump`)

### Kubernetes Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mount-access-api-key
  namespace: heapdump
type: Opaque
stringData:
  api-key: "your-secure-api-key-here"
```

## Deployment

### Prerequisites
- Kubernetes/OpenShift cluster
- Privileged SCC (SecurityContextConstraints) in OpenShift
- ServiceAccount with appropriate RBAC permissions
- Priority class for critical workloads

### Deploy to Kubernetes
```bash
# Create secret
kubectl apply -f k8s/apps/mount-access-controller/secret.yaml

# Deploy StatefulSet and Service
kubectl apply -f k8s/apps/mount-access-controller/statefulset.yaml
kubectl apply -f k8s/apps/mount-access-controller/service.yaml
```

### Deploy to OpenShift
```bash
# Create ImageStream and BuildConfig
oc apply -f openshift/buildconfigs/mount-access-controller-is.yaml
oc apply -f openshift/buildconfigs/mount-access-controller-bc.yaml

# Start build
oc start-build mount-access-controller

# Create secret
oc apply -f k8s/apps/mount-access-controller/secret.yaml

# Deploy StatefulSet and Service
oc apply -f k8s/apps/mount-access-controller/statefulset.yaml
oc apply -f k8s/apps/mount-access-controller/service.yaml

# Create Route
oc apply -f openshift/routes/mount-access-controller.yaml
```

## Architecture

### Deployment Pattern
- **StatefulSet**: Ensures one pod per node (using podAntiAffinity)
- **Service**: ClusterIP with `internalTrafficPolicy: Local` for node-local routing
- **Privileged**: Runs as root with SYS_ADMIN capabilities for chown operations
- **Priority**: Uses `dump-volume-critical` priority class

### Security
- API Key authentication via HTTP header `X-API-Key`
- Kubernetes secret injection for API key
- Health endpoints exempt from authentication
- Privileged execution required for file ownership changes

## Usage Example

### Register a Mount
```bash
curl -X POST https://mount-access-controller.apps.example.com/api/v1/app/mount/register \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "appName": "my-app",
    "userId": "1000"
  }'
```

### Check Mount Readiness
```bash
curl -X POST https://mount-access-controller.apps.example.com/api/v1/app/mount/ready \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "appName": "my-app",
    "userId": "1000"
  }'
```

## Build Locally

```bash
cd apps/mount-access-controller
mvn clean package
```

## Run Locally

```bash
java -jar target/mount-access-controller-1.0.0.jar \
  --api.key=test-key \
  --mount.base.path=/tmp/test-mounts
```

## Technology Stack
- **Framework**: Spring Boot 3.2.0
- **Language**: Java 17
- **Build Tool**: Maven
- **API Documentation**: Springdoc OpenAPI (Swagger)
- **Container**: Red Hat UBI 8 with OpenJDK 17

## Related Components
- **Memory Leak App**: Uses this controller to manage dump volume access
- **Dump Volume Manager**: Provides the shared volume mount point

## Troubleshooting

### Check Pod Status
```bash
kubectl get pods -l app=mount-access-controller -n heapdump
kubectl logs -l app=mount-access-controller -n heapdump
```

### Verify API Key
```bash
kubectl get secret mount-access-api-key -n heapdump -o yaml
```

### Test Health Endpoints
```bash
kubectl exec -it mount-access-controller-0 -n heapdump -- curl localhost:8080/api/v1/health
```

## License

Same as parent project.
