# Memory Leak App Deployment Comparison

## Overview

This document compares two deployment approaches for the memory-leak-app:
- **deployment.yaml**: Original approach with privileged init container
- **deployment2.yaml**: New approach using mount-access-controller API

## Key Differences

### Init Container

#### deployment.yaml (Old Approach)
```yaml
initContainers:
  - name: wait-for-volume-manager
    command:
      - sh
      - '-c'
      - |
        echo "Waiting for dump volume manager to be ready..."
        while [ ! -f /mnt/dump/.ready ]; do
          echo "Volume manager not ready yet, waiting..."
          ls -al /mnt/dump
          sleep 3
        done
        mkdir /dumps/heap
        chown -R 185:185 /dumps/heap
        echo "Volume manager is ready, proceeding with application startup"
    securityContext:
      privileged: true
      runAsUser: 0
    volumeMounts:
      - name: heap-dumps
        mountPath: /dumps
      - name: host-dumps
        readOnly: true
        mountPath: /mnt/dump
```

**Issues:**
- Requires privileged execution
- Runs as root
- Needs access to both host and container mounts
- Manual directory creation and ownership management

#### deployment2.yaml (New Approach)
```yaml
initContainers:
  - name: register-mount
    command:
      - sh
      - '-c'
      - |
        echo "Registering mount with mount-access-controller..."
        
        # Register mount
        RESPONSE=$(curl -s -X POST \
          -H "X-API-Key: ${API_KEY}" \
          -H "Content-Type: application/json" \
          -d '{"appName":"memory-leak-demo","userId":"185"}' \
          http://mount-access-controller.heapdump.svc.cluster.local:8080/api/v1/app/mount/register)
        
        echo "Register response: $RESPONSE"
        
        # Wait for mount to be ready
        echo "Checking if mount is ready..."
        MAX_RETRIES=30
        RETRY_COUNT=0
        
        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
          HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
            -H "X-API-Key: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d '{"appName":"memory-leak-demo","userId":"185"}' \
            http://mount-access-controller.heapdump.svc.cluster.local:8080/api/v1/app/mount/ready)
          
          if [ "$HTTP_CODE" = "200" ]; then
            echo "Mount is ready!"
            exit 0
          fi
          
          echo "Mount not ready yet (HTTP $HTTP_CODE), waiting... ($RETRY_COUNT/$MAX_RETRIES)"
          RETRY_COUNT=$((RETRY_COUNT + 1))
          sleep 3
        done
        
        echo "ERROR: Mount did not become ready in time"
        exit 1
    env:
      - name: API_KEY
        valueFrom:
          secretKeyRef:
            name: mount-access-api-key
            key: api-key
```

**Benefits:**
- No privileged execution required
- Uses API-based approach
- Centralized permission management
- Better security model
- No volume mounts needed in init container

### Main Container Security

#### deployment.yaml
```yaml
securityContext:
  privileged: true
```

#### deployment2.yaml
```yaml
# No privileged security context needed
```

**Benefit:** Application runs with standard permissions, reducing security risk.

### Volume Configuration

#### deployment.yaml
```yaml
volumes:
  - name: heap-dumps
    hostPath:
      path: /mnt/dump/memory-leak-demo
      type: DirectoryOrCreate
  - name: host-dumps
    hostPath:
      path: /mnt/dump
      type: Directory

# Container mounts both volumes
volumeMounts:
  - name: heap-dumps
    mountPath: /dumps
  - name: host-dumps
    readOnly: true
    mountPath: /mnt/dump
```

#### deployment2.yaml
```yaml
volumes:
  - name: heap-dumps
    hostPath:
      path: /mnt/dump/memory-leak-demo/heap
      type: Directory

# Container mounts only heap-dumps
volumeMounts:
  - name: heap-dumps
    mountPath: /dumps
```

**Benefits:**
- Single volume mount
- Directory type ensures it exists (created by controller)
- Simpler configuration

### Heap Dump Path

#### deployment.yaml
```yaml
JAVA_OPTS: '-Xmx256m -Xms128m -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/dumps/heap/$(POD_NAME).hprof'
```

#### deployment2.yaml
```yaml
JAVA_OPTS: '-Xmx256m -Xms128m -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/dumps/$(POD_NAME).hprof'
```

**Reason:** Controller creates `/mnt/dump/memory-leak-demo/heap` which is mounted at `/dumps`

## Security Comparison

| Aspect | deployment.yaml | deployment2.yaml |
|--------|----------------|------------------|
| Init Container Privilege | ✗ Root required | ✓ No privilege |
| Main Container Privilege | ✗ Privileged | ✓ Standard |
| Authentication | File-based (.ready) | API Key based |
| Authorization | Filesystem | Centralized API |
| Attack Surface | Larger | Smaller |

## Architecture Comparison

### deployment.yaml Flow
```
Init Container (privileged) 
  ↓
Check .ready file on host
  ↓
Create directories
  ↓
Change ownership
  ↓
Start application (privileged)
```

### deployment2.yaml Flow
```
Init Container (unprivileged)
  ↓
Call mount-access-controller API (register)
  ↓
Call mount-access-controller API (ready check)
  ↓
Start application (unprivileged)
  ↓
mount-access-controller (privileged, centralized)
  ↓
Creates directories with proper ownership
```

## Benefits of New Approach (deployment2.yaml)

1. **Security**: Application pods run without elevated privileges
2. **Separation of Concerns**: Volume management centralized in controller
3. **API-based**: RESTful interface for mount management
4. **Auditability**: All mount operations logged in controller
5. **Scalability**: Multiple apps can use same controller
6. **Maintainability**: Single place to update mount logic
7. **Authentication**: API key-based security model
8. **Error Handling**: HTTP status codes and retry logic

## Prerequisites for deployment2.yaml

1. **mount-access-controller** must be deployed and running
2. **mount-access-api-key** secret must exist in namespace
3. **Service DNS** must be resolvable: `mount-access-controller.heapdump.svc.cluster.local`

## Migration Path

1. Deploy mount-access-controller
2. Create mount-access-api-key secret
3. Test with deployment2.yaml
4. Once validated, replace deployment.yaml with deployment2.yaml
5. Remove privileged SCC requirements from application

## Conclusion

**deployment2.yaml** represents a more secure, maintainable, and scalable approach to managing volume permissions in a shared multi-tenant environment. It follows the principle of least privilege by delegating elevated operations to a dedicated, centralized controller.

---

**Recommendation**: Use deployment2.yaml for production deployments.
