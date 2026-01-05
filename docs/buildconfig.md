# OpenShift BuildConfig Documentation

## Overview

This document describes the OpenShift BuildConfig setup for the `memory-leak-demo` Java application. The BuildConfig automates the container image build process using Docker strategy and manages the built images through an ImageStream.

## Architecture

The build configuration consists of two main components:

1. **BuildConfig**: Defines how to build the container image
2. **ImageStream**: Stores and manages the built container images

## BuildConfig Details

### Metadata

- **Name**: `memory-leak-demo`
- **Namespace**: `heapdump`
- **Labels**: 
  - `app: memory-leak-demo`
  - `app.kubernetes.io/name: memory-leak-demo`

### Source Configuration

The BuildConfig uses Git as the source repository:

```yaml
source:
  type: Git
  git:
    uri: https://github.com/your-org/javadumpmngmt.git
    ref: main
  contextDir: apps/memoryleak
```

**Configuration Details:**
- **Type**: Git repository
- **URI**: Repository URL (must be updated with your actual repository)
- **Ref**: Branch name (default: `main`)
- **Context Directory**: `apps/memoryleak` - where the Dockerfile is located

### Build Strategy

Uses Docker strategy for building container images:

```yaml
strategy:
  type: Docker
  dockerStrategy:
    dockerfilePath: Dockerfile
    noCache: false
    forcePull: false
```

**Strategy Details:**
- **Type**: Docker - uses the Dockerfile to build the image
- **Dockerfile Path**: `Dockerfile` in the `apps/memoryleak` directory
- **No Cache**: `false` - enables layer caching for faster builds
- **Force Pull**: `false` - reuses cached base images when possible

### Output Configuration

The built image is pushed to an ImageStreamTag:

```yaml
output:
  to:
    kind: ImageStreamTag
    name: memory-leak-demo:latest
```

**Output Details:**
- **Kind**: ImageStreamTag
- **Name**: `memory-leak-demo:latest`
- **Location**: Stored in the internal OpenShift registry within the `heapdump` namespace

### Build Triggers

The BuildConfig includes four types of automatic triggers:

#### 1. ConfigChange Trigger
```yaml
- type: ConfigChange
```
Automatically starts a new build when the BuildConfig itself is modified.

#### 2. ImageChange Trigger
```yaml
- type: ImageChange
```
Automatically starts a new build when any base image used in the Dockerfile is updated.

#### 3. GitHub Webhook Trigger
```yaml
- type: GitHub
  github:
    secret: github-webhook-secret
```
Allows GitHub to trigger builds on code push events. Requires webhook configuration in GitHub repository settings.

#### 4. Generic Webhook Trigger
```yaml
- type: Generic
  generic:
    secret: generic-webhook-secret
```
Provides a generic webhook URL for triggering builds from external systems or CI/CD pipelines.

### Build Policy

```yaml
runPolicy: Serial
successfulBuildsHistoryLimit: 3
failedBuildsHistoryLimit: 3
```

**Policy Details:**
- **Run Policy**: `Serial` - ensures only one build runs at a time
- **Successful Builds History**: Keeps the last 3 successful builds
- **Failed Builds History**: Keeps the last 3 failed builds for debugging

## ImageStream Details

The ImageStream acts as a container image repository within OpenShift:

```yaml
apiVersion: image.openshift.io/v1
kind: ImageStream
metadata:
  name: memory-leak-demo
  namespace: heapdump
spec:
  lookupPolicy:
    local: false
```

**ImageStream Features:**
- Stores built container images with tags
- Enables automatic deployment updates when new images are pushed
- Integrates with OpenShift's internal registry
- Provides image versioning and rollback capabilities

## Dockerfile Build Process

The Dockerfile uses a multi-stage build approach:

### Stage 1: Build (Maven)
- Base image: `maven:3.9-eclipse-temurin-17`
- Compiles the Spring Boot application
- Packages as JAR file: `memory-leak-demo-1.0.0.jar`
- Skips tests during build (`-DskipTests`)

### Stage 2: Runtime (JRE)
- Base image: `eclipse-temurin:17-jre-alpine`
- Lightweight Alpine Linux-based image
- Creates `/dumps` directory for heap dumps
- Configures JVM options for memory diagnostics
- Exposes port 8080 for HTTP traffic

### JVM Configuration
```bash
JAVA_OPTS="-Xmx256m -Xms128m -XX:+HeapDumpOnOutOfMemoryError 
-XX:HeapDumpPath=/dumps/heap_dump.hprof -XX:+PrintGCDetails 
-XX:+PrintGCDateStamps -Xloggc:/dumps/gc.log"
```

**Memory Settings:**
- Initial heap: 128MB
- Maximum heap: 256MB
- Heap dump on OOM enabled
- GC logging enabled

## Prerequisites

Before deploying the BuildConfig, ensure:

1. **OpenShift CLI**: `oc` command-line tool installed and configured
2. **Namespace**: `heapdump` namespace exists or will be created
3. **Permissions**: Sufficient permissions to create BuildConfig and ImageStream resources
4. **Git Repository**: Repository URL is accessible from OpenShift cluster
5. **Webhook Secrets**: Generate secrets for GitHub and Generic webhooks

## Deployment Steps

### Step 1: Create Namespace
```bash
oc create namespace heapdump
```

### Step 2: Update Git Repository URL
Edit `buildconfig.yaml` and update the Git URI:
```yaml
git:
  uri: https://github.com/YOUR-ORG/javadumpmngmt.git
```

### Step 3: Generate Webhook Secrets (Optional)
```bash
# Generate GitHub webhook secret
oc create secret generic github-webhook-secret \
  --from-literal=WebHookSecretKey=$(openssl rand -hex 20) \
  -n heapdump

# Generate Generic webhook secret
oc create secret generic generic-webhook-secret \
  --from-literal=WebHookSecretKey=$(openssl rand -hex 20) \
  -n heapdump
```

### Step 4: Apply BuildConfig
```bash
oc apply -f buildconfig.yaml -n heapdump
```

### Step 5: Start Initial Build
```bash
oc start-build memory-leak-demo -n heapdump
```

## Build Management Commands

### View Build Status
```bash
# List all builds
oc get builds -n heapdump

# Watch build logs
oc logs -f bc/memory-leak-demo -n heapdump
```

### Manual Build Trigger
```bash
# Start a new build
oc start-build memory-leak-demo -n heapdump

# Start build from local directory
oc start-build memory-leak-demo --from-dir=. -n heapdump

# Start build and follow logs
oc start-build memory-leak-demo --follow -n heapdump
```

### Build Cancellation
```bash
# Cancel running build
oc cancel-build <build-name> -n heapdump
```

### Build History
```bash
# View build history
oc get builds -n heapdump

# Describe specific build
oc describe build <build-name> -n heapdump

# Get build logs
oc logs build/<build-name> -n heapdump
```

## ImageStream Management

### View ImageStream
```bash
# List image streams
oc get imagestream -n heapdump

# Describe image stream
oc describe is/memory-leak-demo -n heapdump

# View image tags
oc get istag -n heapdump
```

### Image Information
```bash
# Get image details
oc describe istag/memory-leak-demo:latest -n heapdump

# View image digest
oc get istag/memory-leak-demo:latest -o jsonpath='{.image.dockerImageReference}'
```

## Webhook Configuration

### GitHub Webhook Setup

1. Get the webhook URL:
```bash
oc describe bc/memory-leak-demo -n heapdump | grep -A 1 "GitHub"
```

2. In GitHub repository settings:
   - Navigate to Settings → Webhooks → Add webhook
   - Paste the webhook URL
   - Content type: `application/json`
   - Select "Just the push event"
   - Enable "Active"
   - Click "Add webhook"

### Generic Webhook Usage

Get the webhook URL:
```bash
oc describe bc/memory-leak-demo -n heapdump | grep -A 1 "Generic"
```

Trigger build via curl:
```bash
curl -X POST <generic-webhook-url>
```

## Troubleshooting

### Build Failures

**Check build logs:**
```bash
oc logs -f bc/memory-leak-demo -n heapdump
```

**Common issues:**
1. **Git clone failure**: Check repository URL and network connectivity
2. **Docker build failure**: Review Dockerfile syntax and base image availability
3. **Maven build failure**: Check pom.xml and dependency accessibility
4. **Resource limits**: Ensure sufficient CPU/memory for build pods

### Image Push Failures

**Check registry credentials:**
```bash
oc get secret -n heapdump | grep builder
```

**Verify ImageStream:**
```bash
oc describe is/memory-leak-demo -n heapdump
```

### Webhook Issues

**Test webhook connectivity:**
- Check firewall rules
- Verify secret matches configuration
- Review webhook delivery in GitHub settings
- Check OpenShift event logs: `oc get events -n heapdump`

## Integration with Deployment

Once the image is built, it can be deployed using:

1. **DeploymentConfig** (OpenShift-native)
2. **Deployment** (Kubernetes-standard)
3. **Manual deployment** from ImageStreamTag

Example deployment reference:
```yaml
containers:
- name: memory-leak-demo
  image: image-registry.openshift-image-registry.svc:5000/heapdump/memory-leak-demo:latest
```

## Security Considerations

1. **Secrets Management**: Store webhook secrets securely in OpenShift secrets
2. **Image Scanning**: Enable image scanning in ImageStream for vulnerability detection
3. **RBAC**: Limit BuildConfig access to authorized users only
4. **Network Policies**: Restrict build pod network access if needed
5. **Source Authentication**: Use SSH keys for private Git repositories

## Best Practices

1. **Version Tags**: Tag images with version numbers, not just `latest`
2. **Build Resources**: Set resource limits for build pods to prevent resource exhaustion
3. **Layer Caching**: Organize Dockerfile to maximize layer reuse
4. **Multi-stage Builds**: Keep runtime images small by separating build and runtime stages
5. **Build Pruning**: Regularly clean old builds to save storage
6. **Webhook Security**: Rotate webhook secrets periodically
7. **Build Notifications**: Configure notifications for build failures

## Related Resources

- `apps/memoryleak/Dockerfile`: Multi-stage build definition
- `apps/memoryleak/pom.xml`: Maven project configuration
- `deployment.yaml`: Kubernetes Deployment configuration
- `openshift-route.yaml`: Route for external access
- `openshift-rbac.yaml`: RBAC configuration

## Additional Notes

- The BuildConfig is designed for the `heapdump` namespace
- Built images are stored in OpenShift's internal registry
- The application is a Spring Boot-based memory leak demonstration tool
- Heap dumps are generated in `/dumps` directory on OOM errors
- GC logs are written to `/dumps/gc.log` for analysis

## References

- [OpenShift BuildConfig Documentation](https://docs.openshift.com/container-platform/latest/cicd/builds/understanding-buildconfigs.html)
- [Docker Build Strategy](https://docs.openshift.com/container-platform/latest/cicd/builds/build-strategies.html#build-strategy-docker_build-strategies)
- [ImageStream Documentation](https://docs.openshift.com/container-platform/latest/openshift_images/image-streams-manage.html)
