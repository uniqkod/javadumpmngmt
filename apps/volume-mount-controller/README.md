# Volume Mount Controller

A Python-based Kubernetes controller for managing and monitoring volume mounts, bind mount health, and automatic recovery in Kubernetes clusters.

## Overview

The Volume Mount Controller is a l1ightweight Python application that runs as a DaemonSet in Kubernetes. It monitors volume mounts, detects mount failures, and automatically attempts recovery. This is essential for maintaining persistent storage accessibility across cluster nodes.

## Features

- **Volume Mount Monitoring** - Continuous monitoring of mounted volumes
- **Mount Point Health Checks** - Periodic verification that mounts are accessible
- **Automatic Recovery** - Remount volumes if mounts become unavailable
- **Event Logging** - Detailed logs of mount operations and failures
- **Kubernetes Integration** - Native K8s client for status updates
- **Configurable Intervals** - Adjustable monitoring and recovery intervals
- **Multi-Path Support** - Monitor multiple mount paths per node
- **Graceful Shutdown** - Clean resource cleanup on termination

## Project Structure

```
volume-mount-controller/
├── src/
│   ├── __init__.py
│   ├── main.py                      # Application entry point
│   ├── controller.py                # Main controller logic
│   ├── monitor.py                   # Volume mount monitoring
│   ├── recovery.py                  # Recovery mechanisms
│   ├── kubernetes_client.py          # K8s API interactions
│   └── logger.py                    # Logging configuration
├── config/
│   ├── logging_config.yaml          # Logging configuration
│   └── controller_config.yaml       # Controller settings
├── tests/
│   ├── __init__.py
│   ├── test_monitor.py
│   ├── test_recovery.py
│   └── test_controller.py
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Container image
├── .dockerignore                    # Docker build exclusions
├── setup.py                         # Package setup
├── README.md                        # This file
└── .gitignore                       # Git exclusions
```

## Requirements

- Python 3.9+
- Kubernetes 1.20+
- Access to Kubernetes API (via ServiceAccount)

## Installation

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
python src/main.py
```

### Docker Build

```bash
cd apps/volume-mount-controller
docker build -t volume-mount-controller:1.0.0 .
```

### Kubernetes Deployment

See deployment manifests in `k8s/apps/volume-mount-controller/`

```bash
kubectl apply -f k8s/apps/volume-mount-controller/
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

# Mount paths to monitor (comma-separated)
MOUNT_PATHS=/mnt/dump,/mnt/data

# Log level (default: INFO)
LOG_LEVEL=INFO
```

### Configuration File

See `config/controller_config.yaml` for detailed configuration options:
- Monitor intervals
- Recovery settings
- Mount paths
- Health check parameters

## Usage

### As a DaemonSet

The controller is designed to run as a Kubernetes DaemonSet on every cluster node:

```bash
# Deploy as DaemonSet
kubectl apply -f k8s/apps/volume-mount-controller/daemonset.yaml

# View controller logs
kubectl logs -f -n memory-leak-demo -l app=volume-mount-controller

# Check node status
kubectl get nodes -L volume-mounts=ready
```

### Standalone Execution

```bash
# Set environment variables
export NAMESPACE=memory-leak-demo
export MOUNT_PATHS=/mnt/dump
export LOG_LEVEL=DEBUG

# Run controller
python src/main.py
```

## How It Works

### 1. Initialization
- Loads configuration from environment and config files
- Initializes Kubernetes client
- Sets up logging
- Discovers mount paths to monitor

### 2. Monitoring Loop
- Checks each mount path accessibility
- Verifies read/write permissions
- Logs mount status
- Triggers recovery if mount is inaccessible

### 3. Health Checks
- Attempts to read from mount point
- Checks filesystem space
- Verifies mount propagation mode
- Updates status annotations on node

### 4. Recovery
- Unmounts problematic mount
- Retries mount operation
- Validates recovery success
- Updates event log

### 5. Status Reporting
- Reports mount status via node annotations
- Logs events to Kubernetes events API
- Maintains metrics for monitoring

## Key Components

### `controller.py`
Main controller orchestrating the monitoring and recovery workflow.

**Methods:**
- `start()` - Start the monitoring loop
- `stop()` - Graceful shutdown
- `monitor_mounts()` - Check mount health
- `recover_mounts()` - Attempt recovery

### `monitor.py`
Volume mount health monitoring.

**Methods:**
- `check_mount(path)` - Verify mount accessibility
- `check_permissions(path)` - Verify read/write access
- `check_filesystem(path)` - Check filesystem health
- `check_propagation(path)` - Verify mount propagation

### `recovery.py`
Recovery and remediation logic.

**Methods:**
- `recover_mount(path)` - Attempt to recover mount
- `unmount(path)` - Safely unmount volume
- `remount(path)` - Remount volume
- `validate_recovery(path)` - Verify recovery success

### `kubernetes_client.py`
Kubernetes API interactions.

**Methods:**
- `get_node_name()` - Get current node name
- `update_node_status(status)` - Update node annotations
- `create_event(message)` - Log events
- `get_pod_mounts()` - Discover expected mounts

### `logger.py`
Structured logging configuration.

**Features:**
- JSON formatted logs
- Multiple log levels
- Console and file output
- Request correlation

## Troubleshooting

### Mount Detection Issues

```bash
# Check mount points
mount | grep /mnt/dump

# Verify from container
kubectl exec -it <pod-name> -n memory-leak-demo -- mount
```

### Recovery Failures

Check logs:
```bash
kubectl logs -f -n memory-leak-demo -l app=volume-mount-controller
```

Common causes:
- Permission denied (check SecurityContext/SCC)
- Device busy (mount in use by other pods)
- Device not found (physical mount unavailable)

### Kubernetes API Access

Verify ServiceAccount permissions:
```bash
kubectl auth can-i get nodes --as=system:serviceaccount:memory-leak-demo:volume-mount-controller
kubectl auth can-i patch nodes --as=system:serviceaccount:memory-leak-demo:volume-mount-controller
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_monitor.py::test_check_mount
```

### Code Style

```bash
# Format code
black src/

# Lint code
pylint src/

# Type checking
mypy src/
```

## Metrics & Monitoring

The controller exposes metrics in Prometheus format on port 8000:

```bash
# Get metrics
curl http://localhost:8000/metrics
```

**Key Metrics:**
- `volume_mount_checks_total` - Total mount checks performed
- `volume_mount_failures_total` - Total failed mount checks
- `volume_mount_recoveries_total` - Total recovery attempts
- `volume_mount_recovery_success_total` - Successful recoveries
- `mount_check_duration_seconds` - Duration of mount checks

## Integration with Memory Leak Demo

The Volume Mount Controller is part of the memory leak demo solution:

1. **Ensures Volume Accessibility** - Monitors `/mnt/dump` mount point
2. **Detects Mount Failures** - Early detection of bind mount issues
3. **Automatic Recovery** - Remounts volumes if lost
4. **Complements StatefulSet** - Works alongside volume manager StatefulSet
5. **Provides Observability** - Logs and metrics for volume health

See [docs/commits/features/mount-recovery.md](../../docs/commits/features/mount-recovery.md) for detailed architecture.

## Related Components

- **Volume Manager StatefulSet** - Creates and maintains bind mounts
- **Memory Leak App** - Writes heap dumps to mounted volumes
- **S3 Uploader** - Backs up heap dumps from mounted storage
- **Pod Priority** - Ensures volume manager runs before application

## License

This project is part of the javadumpmngmt solution.

## Support

For issues or questions:
- Check [troubleshooting section](#troubleshooting)
- Review [mount-recovery.md](../../docs/commits/features/mount-recovery.md)
- Check controller logs: `kubectl logs -f -l app=volume-mount-controller`
