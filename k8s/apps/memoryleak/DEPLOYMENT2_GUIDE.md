# Quick Deployment Guide - deployment2.yaml

## Prerequisites

1. **Volume Mount Controller** must be deployed:
   ```bash
   oc apply -f k8s/apps/mount-access-controller/secret.yaml
   oc apply -f k8s/apps/mount-access-controller/statefulset.yaml
   oc apply -f k8s/apps/mount-access-controller/service.yaml
   ```

2. **Verify controller is running**:
   ```bash
   oc get pods -l app=mount-access-controller -n heapdump
   oc logs -l app=mount-access-controller -n heapdump
   ```

3. **Test controller API**:
   ```bash
   oc exec -it mount-access-controller-0 -n heapdump -- \
     curl -H "X-API-Key: change-this-to-a-secure-random-key" \
     http://localhost:8080/api/v1/health
   ```

## Deploy Memory Leak App (v2)

```bash
# Deploy using new approach
oc apply -f k8s/apps/memoryleak/deployment2.yaml

# Watch pod startup
oc get pods -l app=memory-leak-app -w

# Check init container logs
oc logs <pod-name> -c register-mount -n heapdump

# Check application logs
oc logs <pod-name> -c memory-leak-app -n heapdump
```

## Verify Mount Registration

```bash
# Check controller logs for registration
oc logs -l app=mount-access-controller -n heapdump | grep "Registering mount"

# Verify directory was created
oc exec -it mount-access-controller-0 -n heapdump -- \
  ls -la /mnt/dump/memory-leak-demo/heap

# Check ownership
oc exec -it mount-access-controller-0 -n heapdump -- \
  stat /mnt/dump/memory-leak-demo/heap
```

## Troubleshooting

### Init Container Fails
```bash
# Check init container logs
oc logs <pod-name> -c register-mount -n heapdump

# Common issues:
# - Controller not running: Check controller pods
# - Wrong API key: Verify secret matches
# - DNS not resolving: Check service exists
```

### Mount Not Ready
```bash
# Manually test ready endpoint
oc exec -it mount-access-controller-0 -n heapdump -- \
  curl -X POST -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"appName":"memory-leak-demo","userId":"185"}' \
  http://localhost:8080/api/v1/app/mount/ready
```

### Check API Key Secret
```bash
oc get secret mount-access-api-key -n heapdump -o yaml
oc get secret mount-access-api-key -n heapdump -o jsonpath='{.data.api-key}' | base64 -d
```

## Rollback

If issues occur, rollback to original deployment:
```bash
oc delete -f k8s/apps/memoryleak/deployment2.yaml
oc apply -f k8s/apps/memoryleak/deployment.yaml
```

## Migration Steps

1. Test deployment2.yaml in dev/staging environment
2. Verify heap dumps are created correctly
3. Monitor for any permission issues
4. Once validated, replace deployment.yaml in production
5. Update documentation to reference deployment2.yaml as primary

## Benefits Checklist

After migration, verify:
- ✅ Application pods run without privileged security context
- ✅ Init container runs without root privileges
- ✅ Heap dumps are created with correct ownership
- ✅ Application can write to /dumps directory
- ✅ S3 uploader can read heap dumps (if applicable)

---

**Ready to deploy!** Follow the prerequisites and deployment steps above.
