# S3 Heap Dump Uploader

## Overview

The S3 Uploader DaemonSet automatically monitors the `/mnt/dump` shared folder and uploads completed heap dump files to an S3 bucket. It runs on every node alongside the volume manager DaemonSet.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Kubernetes Node                          │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  DaemonSet: dump-volume-manager (Priority: High)           │ │
│  │  - Mounts PVC to /mnt/dump                                  │ │
│  │  - Creates .ready marker                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│                              │ Creates mount                      │
│                              ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    /mnt/dump/ (Host)                        │ │
│  │                    └── memory-leak-demo/                    │ │
│  │                        └── heap_dump.hprof                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│         │                                    ▲                    │
│         │ Watches                            │ Writes             │
│         ▼                                    │                    │
│  ┌─────────────────────┐         ┌─────────────────────────┐   │
│  │  DaemonSet:         │         │  Deployment:            │   │
│  │  s3-uploader        │         │  memory-leak-app        │   │
│  │                     │         │                         │   │
│  │  - Wait for .ready  │         │  - Wait for .ready      │   │
│  │  - Scan for .hprof  │         │  - Write heap dumps     │   │
│  │  - Upload to S3     │         │                         │   │
│  └─────────────────────┘         └─────────────────────────┘   │
│            │                                                      │
│            │ Uploads                                             │
│            ▼                                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    AWS S3 Bucket                            │ │
│  │    s3://heap-dumps/memory-leak-demo/                       │ │
│  │    └── node-01/heap_dump_20251208.hprof                   │ │
│  │    └── node-02/heap_dump_20251208.hprof                   │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Features

✅ **Automatic Upload** - Monitors for new `.hprof` files and uploads them  
✅ **File Stability Detection** - Waits until files stop growing before upload  
✅ **Node Identification** - Adds node name as metadata to uploaded files  
✅ **Idempotent** - Tracks uploaded files to prevent duplicates  
✅ **Dependency Management** - Waits for volume manager via init container  
✅ **S3 Compatible** - Works with AWS S3, MinIO, Ceph, etc.  
✅ **Resource Efficient** - Low CPU/memory footprint  
✅ **Configurable** - All settings via ConfigMap

## Configuration

### ConfigMap: `s3-uploader-config`

```yaml
S3_BUCKET: "heap-dumps"              # S3 bucket name
S3_PREFIX: "memory-leak-demo/"       # Prefix/folder in bucket
WATCH_INTERVAL: "60"                 # Scan interval in seconds
FILE_STABLE_TIME: "120"              # Wait time after file stops growing (seconds)
```

### Secret: `s3-credentials`

```yaml
AWS_ACCESS_KEY_ID: "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY: "wJalrXUtnFEMI/K7MDENG/..."
AWS_DEFAULT_REGION: "us-east-1"
S3_ENDPOINT_URL: ""  # For S3-compatible storage (MinIO, etc.)
```

## Deployment

### Prerequisites

1. **Volume Manager** must be running:
   ```bash
   oc get daemonset -n memory-leak-demo dump-volume-manager
   # Should show DESIRED = CURRENT = READY
   ```

2. **S3 Bucket** must exist:
   ```bash
   aws s3 mb s3://heap-dumps
   ```

3. **IAM Permissions** (if using AWS):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:PutObjectAcl",
           "s3:GetObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::heap-dumps/*",
           "arn:aws:s3:::heap-dumps"
         ]
       }
     ]
   }
   ```

### Step 1: Configure S3 Credentials

**Option A: Edit the YAML file**
```bash
# Edit s3-uploader-daemonset.yaml
vi s3-uploader-daemonset.yaml

# Update the Secret section with real credentials
```

**Option B: Create Secret separately**
```bash
oc create secret generic s3-credentials \
  -n memory-leak-demo \
  --from-literal=AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY" \
  --from-literal=AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY" \
  --from-literal=AWS_DEFAULT_REGION="us-east-1" \
  --from-literal=S3_ENDPOINT_URL=""
```

**Option C: Use IRSA (AWS) or Workload Identity (GCP)**
```yaml
# Add to DaemonSet spec
serviceAccountName: s3-uploader-sa
annotations:
  eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT:role/s3-uploader-role
```

### Step 2: Deploy the DaemonSet

```bash
# Deploy ConfigMap, Secret, and DaemonSet
oc apply -f s3-uploader-daemonset.yaml

# Verify deployment
oc get daemonset -n memory-leak-demo heap-dump-s3-uploader
oc get pods -n memory-leak-demo -l app=s3-uploader
```

### Step 3: Verify Operation

```bash
# Check logs
oc logs -n memory-leak-demo -l app=s3-uploader -f

# Should see output like:
# =========================================
# S3 Heap Dump Uploader Starting
# =========================================
# Bucket: heap-dumps
# Prefix: memory-leak-demo/
# Watch Interval: 60s
# File Stable Time: 120s
# Node: worker-node-01
# =========================================
# Testing S3 connection...
# S3 bucket accessible
# Starting monitoring loop...
```

## How It Works

### 1. Init Container: Wait for Volume Manager

```bash
while [ ! -f /mnt/dump/.ready ]; do
  echo "Volume manager not ready yet, waiting..."
  sleep 5
done

if ! mountpoint -q /mnt/dump; then
  echo "ERROR: /mnt/dump is not a mount point!"
  exit 1
fi
```

**Purpose:** Ensures the volume manager has successfully created the bind mount before the uploader starts.

### 2. File Discovery

```bash
find /mnt/dump -type f -name "*.hprof"
```

Recursively searches all subdirectories for heap dump files.

### 3. File Stability Check

```bash
is_file_stable() {
  # Check 1: Is it a .hprof file?
  # Check 2: Has it already been uploaded?
  # Check 3: Has the file size changed since last check?
  # Check 4: Has it been stable for FILE_STABLE_TIME seconds?
}
```

**Why:** Heap dumps can take several minutes to write. We must wait until the file is complete before uploading.

**Stability Criteria:**
- File size hasn't changed for 2 consecutive scans
- File has been stable for at least 120 seconds (configurable)

### 4. Upload to S3

```bash
aws s3 cp /mnt/dump/memory-leak-demo/heap_dump.hprof \
  s3://heap-dumps/memory-leak-demo/heap_dump.hprof \
  --metadata "node=worker-01,upload-time=2025-12-08T06:45:00Z" \
  --storage-class STANDARD_IA
```

**Features:**
- Adds node name and upload time as metadata
- Uses STANDARD_IA storage class (cheaper for infrequent access)
- Preserves directory structure

### 5. State Tracking

```bash
/tmp/s3-uploader-state/
└── _mnt_dump_memory-leak-demo_heap_dump.hprof.uploaded
```

Tracks uploaded files to prevent duplicate uploads.

### 6. Cleanup

```bash
find /tmp/s3-uploader-state -type f -mtime +7 -delete
```

Cleans up state files older than 7 days.

## Monitoring

### Check DaemonSet Status

```bash
# View all S3 uploader pods
oc get pods -n memory-leak-demo -l app=s3-uploader -o wide

# Check which nodes have the uploader
oc get daemonset -n memory-leak-demo heap-dump-s3-uploader
```

### View Logs

```bash
# Follow logs from all uploader pods
oc logs -n memory-leak-demo -l app=s3-uploader -f

# View logs from specific node
oc logs -n memory-leak-demo -l app=s3-uploader \
  --field-selector spec.nodeName=worker-01
```

### Check Upload Status

```bash
# List files in S3
aws s3 ls s3://heap-dumps/memory-leak-demo/ --recursive --human-readable

# Check file metadata
aws s3api head-object \
  --bucket heap-dumps \
  --key memory-leak-demo/heap_dump.hprof
```

## Configuration Options

### Adjust Scan Interval

```bash
# Edit ConfigMap
oc edit configmap -n memory-leak-demo s3-uploader-config

# Change WATCH_INTERVAL
WATCH_INTERVAL: "30"  # Scan every 30 seconds

# Pods will automatically use new value on next scan
```

### Adjust Stability Time

```bash
# For faster uploads (risky - may upload incomplete files)
FILE_STABLE_TIME: "60"  # 1 minute

# For safer uploads (slower - waits longer)
FILE_STABLE_TIME: "300"  # 5 minutes
```

### Change S3 Bucket

```bash
oc edit configmap -n memory-leak-demo s3-uploader-config

# Update S3_BUCKET and/or S3_PREFIX
S3_BUCKET: "production-heap-dumps"
S3_PREFIX: "app-name/environment/"
```

### Enable File Deletion After Upload

Uncomment in the script to save disk space:

```bash
# After successful upload
echo "Removing local file..."
rm -f "${file}"
```

**Warning:** Only enable if you're confident in S3 reliability and have backups.

## Troubleshooting

### Issue: Init Container Stuck

**Symptom:** Pods show `Init:0/1`

**Check:**
```bash
# Check init container logs
oc logs -n memory-leak-demo -l app=s3-uploader -c wait-for-volume-manager

# Check if volume manager is ready
oc exec -n memory-leak-demo daemonset/dump-volume-manager -- \
  cat /host/mnt/dump/.ready
```

**Solution:** Ensure volume manager DaemonSet is running and healthy.

### Issue: S3 Connection Failed

**Symptom:** Logs show "Cannot access S3 bucket"

**Check:**
```bash
# Verify credentials
oc get secret -n memory-leak-demo s3-credentials -o yaml

# Test S3 access from pod
oc exec -n memory-leak-demo -l app=s3-uploader -- \
  aws s3 ls s3://heap-dumps/
```

**Solutions:**
- Verify AWS credentials are correct
- Check IAM permissions
- Verify S3 endpoint URL (if using S3-compatible storage)
- Check network connectivity

### Issue: Files Not Uploading

**Symptom:** Heap dumps exist but aren't uploaded

**Check:**
```bash
# Check logs for file detection
oc logs -n memory-leak-demo -l app=s3-uploader | grep "Scanning"

# Check file stability status
oc logs -n memory-leak-demo -l app=s3-uploader | grep "File stable"

# List files in mount
oc exec -n memory-leak-demo daemonset/heap-dump-s3-uploader -- \
  find /mnt/dump -name "*.hprof" -ls
```

**Solutions:**
- Files may still be growing (wait for FILE_STABLE_TIME)
- Files may already be uploaded (check state directory)
- Permissions issue (check pod can read files)

### Issue: Duplicate Uploads

**Symptom:** Same file uploaded multiple times

**Check:**
```bash
# Check state directory
oc exec -n memory-leak-demo -l app=s3-uploader -- \
  ls -la /tmp/s3-uploader-state/
```

**Solution:** State directory may have been cleared. This is expected after pod restart. Files will be re-uploaded once.

## Performance Considerations

### Resource Usage

**Per Node:**
- CPU: ~5-10% during scan, 20-50% during upload
- Memory: 128-256 MB
- Network: Varies with heap dump size (typically 100-500 MB per upload)

### Upload Time

**Typical heap dump (256 MB):**
- Local network: ~5-10 seconds
- AWS S3 (same region): ~30-60 seconds
- AWS S3 (different region): ~60-120 seconds

### Scalability

- **Many nodes:** Each node runs its own uploader independently
- **Large files:** Upload time increases linearly with file size
- **Many files:** Scans are sequential, so many files = longer scan time

**Optimization:**
- Increase `WATCH_INTERVAL` if you have many small files
- Use S3 Transfer Acceleration for faster uploads
- Consider using S3 Multipart Upload for files > 100 MB

## S3 Bucket Structure

```
s3://heap-dumps/
└── memory-leak-demo/          # S3_PREFIX
    ├── memory-leak-demo/      # App subdirectory
    │   ├── heap_dump_20251208_064500.hprof
    │   └── heap_dump_20251208_070000.hprof
    └── other-app/
        └── heap_dump.hprof
```

**Metadata on each object:**
```json
{
  "node": "worker-node-01",
  "upload-time": "2025-12-08T06:45:00Z"
}
```

## Integration with Other Services

### Lifecycle Policy

Create S3 lifecycle policy to manage old dumps:

```json
{
  "Rules": [
    {
      "Id": "DeleteOldHeapDumps",
      "Status": "Enabled",
      "Prefix": "memory-leak-demo/",
      "Expiration": {
        "Days": 30
      },
      "Transitions": [
        {
          "Days": 7,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

### SNS Notification

Configure S3 to send SNS notification on upload:

```json
{
  "Event": "s3:ObjectCreated:*",
  "Filter": {
    "Key": {
      "FilterRules": [
        {"Name": "suffix", "Value": ".hprof"}
      ]
    }
  }
}
```

### Lambda Function

Trigger Lambda to analyze heap dumps automatically:

```python
def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Download heap dump
    # Run analysis
    # Send report
```

## Security Best Practices

1. **Use IRSA/Workload Identity** instead of static credentials
2. **Encrypt S3 bucket** with KMS
3. **Enable S3 bucket versioning** for recovery
4. **Use least-privilege IAM policy**
5. **Rotate credentials** regularly
6. **Enable S3 access logging**
7. **Use VPC endpoints** for S3 access (avoid internet egress costs)

## Cleanup

```bash
# Delete DaemonSet
oc delete -f s3-uploader-daemonset.yaml

# Or delete individual resources
oc delete daemonset -n memory-leak-demo heap-dump-s3-uploader
oc delete configmap -n memory-leak-demo s3-uploader-config
oc delete secret -n memory-leak-demo s3-credentials
```

## Summary

The S3 Uploader DaemonSet provides:

✅ **Automatic backup** - All heap dumps automatically uploaded to S3  
✅ **Zero configuration** - Works out of the box with default settings  
✅ **Node-aware** - Tracks which node generated each dump  
✅ **Resilient** - Survives restarts and network issues  
✅ **Efficient** - Low resource usage, smart file stability detection  
✅ **Harmonious** - Works seamlessly with volume manager DaemonSet  

---

**Created:** 2025-12-08T06:45:56.773Z  
**Branch:** ocp  
**Related Files:**
- `s3-uploader-daemonset.yaml` - DaemonSet, ConfigMap, Secret
- `daemonset-volume.yaml` - Volume manager DaemonSet (dependency)
