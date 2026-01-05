# Volume Mount Controller

**Feature Branch:** `feature/volume-mount-controller`  
**Commit SHA:** `77c97e0`  
**Date:** 2026-01-05T18:46:42.573Z  
**Status:** ✅ Completed

## Overview

A Python-based Kubernetes controller for managing and monitoring volume mounts, detecting bind mount failures, and automatically recovering unhealthy mounts. This component complements the existing StatefulSet volume manager and ensures reliable persistent storage accessibility across cluster nodes.

## Problem Statement

Volume mounts in Kubernetes can fail due to:
- Container or node restarts
- Underlying storage issues
- Network-related mount problems
- Improper unmounting

Without monitoring and automatic recovery:
- Lost mount accessibility causes pod failures
- Heap dumps cannot be written to persistent storage
- Manual intervention required for recovery
- Cluster reliability decreases

## Solution

The Volume Mount Controller provides:
1. **Continuous Monitoring** - Periodic health checks of all configured mounts
2. **Automatic Detection** - Identifies mount failures immediately
3. **Self-Healing** - Automatically remounts failed volumes
4. **Kubernetes Integration** - Updates node status and logs events
5. **Observability** - Structured logging and metrics

## Architecture

### Design Pattern: DaemonSet Controller

Runs on every cluster node as a DaemonSet:
- One controller pod per node
- Monitors node-local mount points
- Updates node annotations with status
- Logs events for troubleshooting

### Component Diagram

```
┌─────────────────────────────────────────┐
│         Kubernetes Cluster              │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Node 1 (volume-mount-controller)  │  │
│  ├──────────────────────────────────┤  │
│  │ Monitor → /mnt/dump              │  │
│  │ Detect failures                  │  │
│  │ Auto-recover                     │  │
│  │ Update node status               │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Node 2 (volume-mount-controller)  │  │
│  ├──────────────────────────────────┤  │
│  │ Monitor → /mnt/dump              │  │
│  │ Detect failures                  │  │
│  │ Auto-recover                     │  │
│  │ Update node status               │  │
│  └──────────────────────────────────┘  │
│                                         │
│           ... more nodes ...            │
│                                         │
└─────────────────────────────────────────┘
```

## Features

### Volume Mount Monitoring

Continuous health checks for configured mount points:
- **Path Existence** - Verify mount point exists
- **Directory Type** - Confirm it's a directory
- **Read/Write Access** - Test permission levels
- **Directory Listing** - Verify accessibility
- **Test File Creation** - Validate write capability

```python
# Example: Check mount health
monitor.check_mount('/mnt/dump')  # Returns True if healthy
```

### Filesystem Health

Monitor storage capacity and usage:
- Total disk space
- Used space
- Available space
- Usage percentage

```python
# Example: Get filesystem stats
stats = monitor.check_filesystem('/mnt/dump')
# Returns: {'total': X, 'used': Y, 'free': Z, 'percent': N}
```

### Mount Propagation Detection

Verify mount propagation mode:
- Detect: `shared`, `slave`, `private`, `rslave`, `rprivate`, `rshared`
- Ensures correct mount behavior across containers

### Automatic Recovery

Complete recovery workflow:

1. **Detection** - Mount health check fails
2. **Unmounting** - Gracefully unmount the volume
   - Try normal unmount first
   - Force unmount if needed
3. **Remounting** - Remount with original settings
   - Get original device, filesystem, options from `/proc/mounts`
   - Remount with same configuration
4. **Validation** - Verify recovery success
   - Check mount exists
   - Verify read/write access

```python
# Example: Recover failed mount
success = recovery.recover_mount('/mnt/dump')
```

### Kubernetes Integration

#### Node Status Updates

Updates node labels with controller status:
```
mount-controller/status: ready|unhealthy
mount-controller/checked-at: timestamp
```

#### Event Logging

Creates Kubernetes events for important operations:
- Mount check failures
- Recovery attempts
- Successful recoveries
- Configuration changes

```bash
# View events
kubectl describe node <node-name>
# Shows controller events in the event list
```

## Implementation

### File Structure

```
apps/volume-mount-controller/
├── src/
│   ├── main.py              # Entry point (51 lines)
│   ├── controller.py        # Main orchestrator (169 lines)
│   ├── monitor.py           # Mount monitoring (126 lines)
│   ├── recovery.py          # Recovery logic (213 lines)
│   ├── kubernetes_client.py # K8s integration (192 lines)
│   ├── logger.py            # Logging setup (56 lines)
│   └── __init__.py
├── config/
│   └── controller_config.yaml  # Configuration template
├── tests/
│   ├── test_monitor.py      # Unit tests
│   └── __init__.py
├── Dockerfile               # Alpine-based Python image
├── requirements.txt         # Python dependencies
├── setup.py                 # Package setup
└── README.md                # Documentation
```

### Core Classes

#### VolumeMountController

Main orchestrator managing the monitoring loop:

```python
class VolumeMountController:
    def start(self) -> None:
        """Start monitoring loop"""
    
    def stop(self) -> None:
        """Stop gracefully"""
    
    def monitor_mounts(self) -> Dict[str, bool]:
        """Check all configured mounts"""
    
    def recover_mounts(self, mount_status: Dict[str, bool]) -> None:
        """Attempt recovery on failed mounts"""
```

**Key Behaviors:**
- Loads configuration from environment variables
- Initializes Kubernetes client
- Runs continuous monitoring loop
- Handles SIGTERM and SIGINT signals for graceful shutdown
- Updates node status after each iteration

#### VolumeMonitor

Checks mount health and accessibility:

```python
class VolumeMonitor:
    def check_mount(self, mount_path: str) -> bool:
        """Verify mount is healthy"""
    
    def check_filesystem(self, mount_path: str) -> Optional[dict]:
        """Get filesystem statistics"""
    
    def check_propagation(self, mount_path: str) -> Optional[str]:
        """Determine mount propagation mode"""
```

#### VolumeRecovery

Handles mount recovery operations:

```python
class VolumeRecovery:
    def recover_mount(self, mount_path: str) -> bool:
        """Full recovery workflow"""
    
    def unmount(self, mount_path: str, force: bool = False) -> bool:
        """Unmount volume"""
    
    def remount(self, mount_path: str) -> bool:
        """Remount with original settings"""
    
    def validate_recovery(self, mount_path: str) -> bool:
        """Verify recovery success"""
```

#### KubernetesClient

Kubernetes API interactions:

```python
class KubernetesClient:
    def get_node_name(self) -> Optional[str]:
        """Get current node name"""
    
    def update_node_status(self, labels: Dict[str, str]) -> bool:
        """Update node annotations"""
    
    def create_event(self, message: str, event_type: str = 'Normal') -> bool:
        """Log event to K8s API"""
    
    def get_pod_mounts(self) -> Dict[str, list]:
        """Discover expected mounts from pods"""
```

## Configuration

### Environment Variables

```bash
# Kubernetes namespace (default: default)
NAMESPACE=memory-leak-demo

# Monitoring interval in seconds (default: 30)
MONITOR_INTERVAL=30

# Recovery timeout in seconds (default: 60)
RECOVERY_TIMEOUT=60

# Mount paths to monitor (comma-separated, default: /mnt/dump)
MOUNT_PATHS=/mnt/dump,/mnt/data

# Log level (default: INFO)
LOG_LEVEL=INFO
```

### Configuration File

Edit `config/controller_config.yaml`:

```yaml
monitoring:
  check_interval: 30
  mount_paths:
    - /mnt/dump
  health_checks:
    check_exists: true
    check_permissions: true
    check_filesystem: true

recovery:
  timeout: 60
  max_attempts: 3
  retry_delay: 5

kubernetes:
  namespace: default
  update_node_status: true
  create_events: true

logging:
  level: INFO
  format: json
```

## Deployment

### Docker Image

**Base:** `python:3.11-alpine`  
**Size:** ~500MB (optimized)  
**User:** Non-root (`controller:1000`)  
**Health Check:** Included

**Build:**
```bash
cd apps/volume-mount-controller
docker build -t volume-mount-controller:1.0.0 .
```

### Kubernetes DaemonSet

Designed to run as a DaemonSet on every cluster node:

```bash
kubectl apply -f k8s/apps/volume-mount-controller/daemonset.yaml
```

**Features:**
- Runs on every node
- Mounts host filesystem for access to `/mnt/dump`
- Requires elevated privileges for mount operations
- Uses ServiceAccount with appropriate RBAC
- Health checks for pod readiness

### Local Development

```bash
cd apps/volume-mount-controller

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run application
export MOUNT_PATHS=/tmp/test-mount
python src/main.py
```

## Logging

Structured JSON logging for easy parsing:

```json
{
  "timestamp": "2026-01-05T18:46:42.123Z",
  "level": "INFO",
  "logger": "controller",
  "message": "Mount /mnt/dump is healthy",
  "module": "monitor",
  "function": "check_mount",
  "line": 42
}
```

**Log Levels:**
- `DEBUG` - Detailed monitoring information
- `INFO` - Normal operations (mount checks, recovery attempts)
- `WARNING` - Mount failures, recovery actions
- `ERROR` - Operation failures

## Metrics

Prometheus-format metrics (future enhancement):

```
volume_mount_checks_total{mount="/mnt/dump"} 150
volume_mount_failures_total{mount="/mnt/dump"} 2
volume_mount_recoveries_total{mount="/mnt/dump"} 2
volume_mount_recovery_success_total{mount="/mnt/dump"} 2
mount_check_duration_seconds{mount="/mnt/dump"} 0.145
```

## Integration with Memory Leak Demo

### Complements Existing Architecture

Works seamlessly with:
- **Volume Manager StatefulSet** - Creates and maintains bind mounts
- **Memory Leak App** - Writes heap dumps to mounted volumes
- **S3 Uploader** - Backs up heap dumps from mounted storage
- **Pod Priority** - Ensures correct startup order

### Reliability Chain

```
Pod Priority (ensures startup order)
    ↓
Volume Manager StatefulSet (creates mounts)
    ↓
Volume Mount Controller (monitors & recovers) ← NEW
    ↓
Memory Leak App (writes heap dumps)
    ↓
S3 Uploader (backs up dumps)
```

### Monitoring Strategy

1. **Prevention** - Detects mount issues early
2. **Detection** - Immediate notification of failures
3. **Recovery** - Automatic remediation
4. **Observability** - Logs and node annotations

## Testing

### Unit Tests

Located in `tests/test_monitor.py`:

```python
def test_check_mount_healthy(monitor, tmp_path):
    """Test checking a healthy mount"""
    result = monitor.check_mount(str(tmp_path))
    assert result is True

def test_check_mount_nonexistent(monitor):
    """Test checking a non-existent mount"""
    result = monitor.check_mount('/nonexistent/path')
    assert result is False
```

**Run Tests:**
```bash
pytest tests/

# With coverage
pytest --cov=src tests/
```

### Integration Testing

Future enhancements:
- Mount point lifecycle testing
- Recovery scenario simulation
- Kubernetes API interaction testing
- Event logging verification

## Dependencies

### Core

- `kubernetes==26.1.0` - Kubernetes Python client
- `pyyaml==6.0` - YAML configuration parsing
- `python-dateutil==2.8.2` - Date utilities
- `requests==2.31.0` - HTTP client

### Development

- `pytest==7.4.0` - Testing framework
- `pytest-cov==4.1.0` - Code coverage
- `black==23.7.0` - Code formatting
- `pylint==2.17.5` - Linting
- `mypy==1.4.1` - Type checking

## Git Commit

**Branch:** `feature/volume-mount-controller`  
**Commit:** `77c97e0`  
**Files:** 16 new files, 1,394 insertions

**Commit Message:**
```
feat: add volume-mount-controller Python application

- Kubernetes controller for volume mount monitoring and recovery
- Automatic detection and remediation of failed mounts
- Features: health checks, filesystem monitoring, automatic recovery
- Components: controller, monitor, recovery, K8s client, logging
- Configuration via environment variables and YAML
- Alpine Docker image, DaemonSet deployment
- Unit tests and comprehensive documentation
```

## Future Enhancements

1. **Metrics Export** - Prometheus metrics endpoint
2. **Advanced Recovery** - Multiple recovery strategies
3. **Alerting** - Integration with alerting systems
4. **WebUI** - Dashboard for monitoring status
5. **Configuration API** - Dynamic configuration updates
6. **Distributed Tracing** - OpenTelemetry integration
7. **Performance Optimization** - Reduce resource usage
8. **Extended Validation** - Additional health checks

## Troubleshooting

### Mount Detection Issues

```bash
# Check mount points on node
mount | grep /mnt/dump

# Verify from controller pod
kubectl exec -it <pod> -- mount | grep /mnt/dump
```

### Recovery Failures

Check controller logs:
```bash
kubectl logs -f -n memory-leak-demo -l app=volume-mount-controller
```

Common causes:
- Permission denied → Check SecurityContext/SCC
- Device busy → Mount in use by other pods
- Device not found → Physical mount unavailable

### Kubernetes API Access

Verify ServiceAccount permissions:
```bash
kubectl auth can-i get nodes \
  --as=system:serviceaccount:memory-leak-demo:volume-mount-controller
```

## Related Documentation

- [Mount Recovery Feature](mount-recovery.md) - Detailed recovery mechanisms
- [Pod Priority](pod-priority.md) - Startup order management
- [Bidirectional Mount](bidirectional-mount.md) - Volume architecture
- [Root README](../../../README.md) - Project overview
- [Development Setup](../../development/SETUP_STEPS.md) - Complete setup guide

## Summary

The Volume Mount Controller is a critical addition to the javadumpmngmt solution, providing:

✅ **Reliability** - Automatic detection and recovery of mount failures  
✅ **Observability** - Structured logging and Kubernetes event integration  
✅ **Production-Ready** - Error handling, health checks, graceful shutdown  
✅ **Scalability** - Runs on every node via DaemonSet  
✅ **Integration** - Works seamlessly with existing components  

This component transforms volume management from reactive (manual recovery) to proactive (automatic), significantly improving cluster reliability and reducing operational overhead.
