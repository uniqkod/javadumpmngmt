# Documentation

Complete project documentation organized by category. **Last Updated:** 2026-01-05

## 📚 Navigation

### Quick Start
- **[Root README.md](../README.md)** - Main project overview and quick start guide

### 📋 Implementation & Planning
- **[Implementation Plan](./plan.md)** - Full project roadmap and milestones
- **[Project Structure Status](./project-structure-status.md)** - Current project status and progress
- **[Project Reevaluation Summary](./project-reevaluation-summary.md)** - Architecture changes and decisions

---

## 📁 Folder Structure

```
docs/
├── README.md                           # This file
├── plan.md                             # Implementation plan
├── project-structure-status.md         # Project status report
├── project-reevaluation-summary.md     # Architecture summary
├── commits/                            # Detailed commit documentation
│   ├── features/                       # Feature implementations
│   ├── fixes/                          # Bug fixes and corrections
│   └── refactors/                      # Refactoring changes
├── deployments/                        # Deployment guides
└── development/                        # Development setup & guides
```

---

## 🎯 Commits Documentation

### Features (`commits/features/`)

Features implemented and documented:

1. **[Bidirectional Mount](./commits/features/bidirectional-mount.md)** (413 lines)
   - Kubernetes volume mounting strategy
   - Host path access via bidirectional propagation
   - StatefulSet configuration for persistent volumes
   - Init container patterns

2. **[Pod Priority & Startup Order](./commits/features/pod-priority.md)** (309 lines)
   - Priority classes for guaranteed pod scheduling
   - Init containers for dependency management
   - Startup order enforcement (StatefulSet before Application)
   - Readiness marker files

3. **[Bind Mount Recovery](./commits/features/mount-recovery.md)** (384 lines)
   - Automatic remount detection and recovery
   - Health checks for volume manager
   - Recovery mechanisms for lost bind mounts
   - Monitoring and alerts

4. **[S3 Heap Dump Uploader](./commits/features/s3-uploader.md)** (550 lines)
   - Automatic backup to AWS S3
   - File stability detection
   - Duplicate prevention via tracking
   - Metadata enrichment (node info, timestamps)
   - Consumer pattern for async processing

5. **[OpenShift BuildConfig](./commits/features/buildconfig.md)** (403 lines)
   - Container image build automation
   - Git webhook integration
   - ImageStream management
   - Build history and versioning
   - Multi-stage Docker builds

6. **[OpenShift Updates Summary](./commits/features/ocp-updates-summary.md)** (543 lines)
   - SCC (Security Context Constraints) configuration
   - OpenShift-specific deployment changes
   - Route and service discovery setup
   - RBAC policies and roles

7. **[OCP Branch Creation Summary](./commits/features/opc-branch-creation-summary.md)**
   - OpenShift Container Platform branch setup
   - Feature enhancements and additions
   - Session-based changes documentation

### Fixes (`commits/fixes/`)

Currently empty - ready for bug fix documentation

**When documenting fixes, include:**
- Problem statement
- Root cause analysis
- Solution implemented
- Testing verification
- Impact assessment

### Refactors (`commits/refactors/`)

1. **[Folder Refactoring Summary](./commits/refactors/folder-refatoring-summary.md)**
   - Project folder reorganization
   - Documentation consolidation
   - Multi-environment deployment structure
   - Kubernetes, Helm, and OpenShift folder creation

---

## 🚀 Deployments

Documentation for deploying to different platforms:

Folder: `docs/deployments/`

### Available Deployment Options

1. **Kubernetes Deployment** - Native K8s manifests
   - See: [k8s/README.md](../k8s/README.md)
   - Features: namespaces, deployments, services, storage, monitoring

2. **Helm Deployment** - Templated multi-environment deployments
   - See: [helm/README.md](../helm/README.md)
   - Features: charts, values overrides, sub-charts, dependency management

3. **OpenShift Deployment** - OCP-specific configurations
   - See: [openshift/README.md](../openshift/README.md)
   - Features: SCC, Routes, BuildConfigs, ImageStreams

### Key Deployment Files

**Kubernetes** (`k8s/`)
- Namespaces and storage
- App-specific manifests (Deployment, Service, HPA, NetworkPolicy)
- Monitoring (Prometheus, Grafana, Loki)
- Databases (PostgreSQL, MySQL, Redis, MongoDB)
- Message queues (Kafka, RabbitMQ)

**Helm** (`helm/`)
- Main chart: `Chart.yaml`, `values.yaml`
- Environment values: `values-dev.yaml`, `values-prod.yaml`
- Sub-charts: memoryleak app, infrastructure components

**OpenShift** (`openshift/`)
- RBAC and SCC definitions
- Routes for external access
- BuildConfigs for automated builds

---

## 💻 Development

Documentation for local development and setup:

### Setup & Installation

**[Complete Setup Steps](./development/SETUP_STEPS.md)** (900+ lines)

Step-by-step guide including:
- Project structure creation
- Maven configuration (pom.xml)
  - Spring Boot 3.2.0
  - Java 17
  - Web and Actuator starters
  
- Java application classes
  - `MemoryLeakApplication.java` - Main Spring Boot app with @EnableScheduling
  - `MemoryLeakService.java` - Memory leak logic (10MB/5sec allocation)
  - `HealthController.java` - REST endpoints (/health, /)
  
- Docker configuration
  - Multi-stage Dockerfile (Maven build → JRE runtime)
  - .dockerignore setup (excludes target/, *.hprof, *.log)
  - JAVA_OPTS configuration for heap dumps and GC logging
  
- Kubernetes deployment manifests
  - Namespace setup
  - StatefulSet (volume manager with host path binding)
  - Deployment (application with init containers)
  - Service and Ingress configuration
  - HPA (Horizontal Pod Autoscaler)
  - NetworkPolicy for security
  
- Local testing and troubleshooting
  - Maven build commands
  - Docker image creation
  - Local Java execution with heap dump settings
  - K8s deployment and verification
  
- Heap dump analysis and cleanup
  - Tools: Eclipse MAT, VisualVM, JProfiler
  - Heap dump retrieval via kubectl cp
  - Analysis techniques

### Project Applications

Currently configured:
- **memoryleak** (`apps/memoryleak/`) - Spring Boot memory leak demo
  - Scheduled memory leak (10MB every 5 seconds)
  - Heap dump generation on OutOfMemoryError
  - Health check endpoints returning memory stats
  - Configurable heap size (256MB default)
  - GC logging enabled
  - Ready for Docker and Kubernetes deployment

### Environment Setup

**Development** (`helm/values-dev.yaml`)
- 1 replica
- Low resource limits (100m CPU, 128Mi memory)
- Image tag: `latest`
- 3-day metrics retention
- Disabled auto-scaling

**Production** (`helm/values-prod.yaml`)
- 3+ replicas
- Full resource limits (500m-1000m CPU, 512Mi-1Gi memory)
- Image tag: semantic versioning (e.g., v1.0.0)
- 90-day metrics retention
- Auto-scaling enabled (up to 10 replicas)
- Kafka messaging enabled
- Large PostgreSQL volume (100Gi)

---

## 📊 Documentation Statistics

| Category | Count | Details |
|----------|-------|---------|
| Features | 7 | Architecture, deployment, automation |
| Fixes | 0 | Ready for documentation |
| Refactors | 1 | Folder reorganization |
| Development | 1 | Complete setup guide (900+ lines) |
| Total Docs | 10 | Markdown documentation files |

---

## 🔗 Cross References

### From Root README.md
- [README.md](../README.md) - Links to all deployment guides and documentation

### From Deployment Folders
- [k8s/README.md](../k8s/README.md) - Kubernetes deployment instructions
- [helm/README.md](../helm/README.md) - Helm chart usage and customization
- [openshift/README.md](../openshift/README.md) - OpenShift-specific guide

### From Application Folder
- [apps/memoryleak/README.md](../apps/memoryleak/README.md) - Memory leak app details

---

## 📝 How to Use This Documentation

1. **Getting Started?**
   - Start with [Root README.md](../README.md)
   - Follow [Complete Setup Steps](./development/SETUP_STEPS.md)

2. **Deploying to Kubernetes?**
   - Read [Kubernetes Manifests](../k8s/README.md)
   - Review feature docs: [Pod Priority](./commits/features/pod-priority.md), [Bidirectional Mount](./commits/features/bidirectional-mount.md)

3. **Using Helm?**
   - Read [Helm Charts Guide](../helm/README.md)
   - Review environment-specific values files

4. **Deploying to OpenShift?**
   - Read [OpenShift Guide](../openshift/README.md)
   - Study [OpenShift Updates](./commits/features/ocp-updates-summary.md)
   - Review [BuildConfig Documentation](./commits/features/buildconfig.md)

5. **Understanding Architecture?**
   - Review [Pod Priority](./commits/features/pod-priority.md)
   - Study [Bidirectional Mount](./commits/features/bidirectional-mount.md)
   - Check [Mount Recovery](./commits/features/mount-recovery.md)
   - Review [S3 Uploader](./commits/features/s3-uploader.md)

6. **Troubleshooting?**
   - Check [Mount Recovery](./commits/features/mount-recovery.md) troubleshooting section
   - Review [Setup Steps](./development/SETUP_STEPS.md) troubleshooting section
   - Check [OpenShift Guide](../openshift/README.md) troubleshooting section

7. **Setting up CI/CD?**
   - Review [BuildConfig Documentation](./commits/features/buildconfig.md)
   - Check [OpenShift Updates](./commits/features/ocp-updates-summary.md)

---

## 📆 Latest Updates

- **2026-01-05** - Created comprehensive docs/README.md with detailed content summaries
- **2025-12-08** - Folder restructuring and documentation consolidation
- **2025-12-07** - OpenShift integration and S3 uploader features

---

## 📞 Quick Reference

| Need | Link | Lines |
|------|------|-------|
| Quick Start | [Root README](../README.md) | ~140 |
| Local Setup | [SETUP_STEPS.md](./development/SETUP_STEPS.md) | ~900 |
| K8s Deploy | [k8s/README.md](../k8s/README.md) | ~100 |
| Helm Deploy | [helm/README.md](../helm/README.md) | ~100 |
| OpenShift Deploy | [openshift/README.md](../openshift/README.md) | ~110 |
| Bidirectional Mounts | [features/bidirectional-mount.md](./commits/features/bidirectional-mount.md) | 413 |
| Pod Priority | [features/pod-priority.md](./commits/features/pod-priority.md) | 309 |
| Mount Recovery | [features/mount-recovery.md](./commits/features/mount-recovery.md) | 384 |
| S3 Uploader | [features/s3-uploader.md](./commits/features/s3-uploader.md) | 550 |
| BuildConfig | [features/buildconfig.md](./commits/features/buildconfig.md) | 403 |

---

## ✅ Documentation Checklist

Use this checklist when adding new documentation:

- [ ] Clear title and overview section
- [ ] Problem statement (for fixes/features)
- [ ] Solution or implementation details
- [ ] Code examples where applicable
- [ ] Configuration options
- [ ] Troubleshooting section
- [ ] Related links to other docs
- [ ] Commands and step-by-step instructions
- [ ] Verification/testing steps
- [ ] Cleanup procedures (if applicable)
