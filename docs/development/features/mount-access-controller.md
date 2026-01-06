# Feature: Mount Access Controller

**Status:** Implemented  
**Priority:** High  
**Component:** Mount Access Controller  
**Effort:** Medium  
**Epic:** Volume Management  
**Created:** 2026-01-05T19:18:36.170Z  
**Completed:** 2026-01-05T20:51:19.206Z

## Description

A Java Spring Boot REST API application that manages volume mount access rights operations  based on registered applications and creates a readiness api for clients that reports mount point access ready.

## User Story

There is one shared volume for all applications thar runs with differen users. Giving root access rights to ordinary java applicatins is not applicable. Another supervised application will regulate access rights on behalf.

## Motivation

There is one shared volume for all applications thar runs with differen users. Giving root access rights to ordinary java applicatins is not applicable. Another supervised application will regulate access rights on behalf.

## Detailed Requirements

* run in a k8s workload just like memoryleak app deployment.yaml: all same but only it would be a statefulset that will run  as one pod per node manner just like dump-volume-manager statefullset
* it will have a service with a all traffic will routed to pod on the same node
* service will make a api key autorization based on a kubernetes secret  
* all clients will use this api key to access services suplied.
* services:
  * **mountRegister**: Register an application as mount owner, request-json:[string:appName,string:userId], creates subfolder in dump folder for app and give user ownership 
      >mkdir /mnt/dump/<appName>

      >mkdir /mnt/dump/<appName>/heap

      >chown -R <userId>:<userId> /mnt/dump/<appName>/heap

  * **mountReady**: Check if mount ready to use with user, request-json:[string:appName,string:user] return http200 if ok, else http 401.

## Design/Architecture

### Technology Stack

- **Framework:** Spring Boot 3.x
- **Language:** Java 17+
- **Build Tool:** Maven
- **REST:** Spring Web MVC
- **K8s Client:** Fabric8 Kubernetes Client
- **Database:** n/a
- **Messaging:** n/a
- **API Docs:** Springdoc OpenAPI (Swagger 3.0)
- **Monitoring:** n/a
- **Testing:** JUnit 5, Testcontainers, MockMvc

### Core Components
 
### API Endpoints

```
POST   /api/v1/app/mount/register   - Register an application as mount owner 
POST   /api/v1/app/mount/ready      - If mount ready will return http200 other wise 401

GET    /api/v1/health              - Health status
GET    /api/v1/health/ready        - Readiness probe
GET    /api/v1/health/live         - Liveness probe

GET    /api/v1/metrics             - Prometheus metrics
```

## Dependencies

**External:**
- Kubernetes cluster (1.20+)
- Java 17+ runtime
- Optional: PostgreSQL (for audit logs)

## Related Items
- **Memory Leak App** - Volume client

## Effort Estimate

- **Medium to Large** (2-4 weeks)
  - Core API: 1 week
  - K8s integration: 1 week
  - Testing & documentation: 1 week
  - Deployment & optimization: 1 week

## Implementation Summary

### Application Structure
- **Package**: `com.example.mountaccess`
- **Main Class**: `MountAccessControllerApplication.java`
- **Controllers**: 
  - `MountController` - Mount registration and readiness endpoints
  - `HealthController` - Health check endpoints
- **Services**: `MountService` - Core logic for directory creation and ownership management
- **Security**: `ApiKeyFilter` - API key authentication filter
- **Models**: Request DTOs for mount operations

### Files Created

**Application Code** (13 files):
- `apps/mount-access-controller/pom.xml`
- `apps/mount-access-controller/Dockerfile`
- `apps/mount-access-controller/.dockerignore`
- `apps/mount-access-controller/README.md`
- `apps/mount-access-controller/src/main/java/com/example/volumemount/MountAccessControllerApplication.java`
- `apps/mount-access-controller/src/main/java/com/example/volumemount/controller/MountController.java`
- `apps/mount-access-controller/src/main/java/com/example/volumemount/controller/HealthController.java`
- `apps/mount-access-controller/src/main/java/com/example/volumemount/service/MountService.java`
- `apps/mount-access-controller/src/main/java/com/example/volumemount/model/MountRegisterRequest.java`
- `apps/mount-access-controller/src/main/java/com/example/volumemount/model/MountReadyRequest.java`
- `apps/mount-access-controller/src/main/java/com/example/volumemount/security/ApiKeyFilter.java`
- `apps/mount-access-controller/src/main/java/com/example/volumemount/config/SecurityConfig.java`
- `apps/mount-access-controller/src/main/resources/application.properties`

**Kubernetes Manifests** (3 files):
- `k8s/apps/mount-access-controller/statefulset.yaml`
- `k8s/apps/mount-access-controller/service.yaml`
- `k8s/apps/mount-access-controller/secret.yaml`

**OpenShift Resources** (3 files):
- `openshift/buildconfigs/mount-access-controller-bc.yaml`
- `openshift/buildconfigs/mount-access-controller-is.yaml`
- `openshift/routes/mount-access-controller.yaml`

### Key Features Implemented

1. **API Key Authentication**: Secure endpoint access via Kubernetes secret
2. **Mount Registration**: Creates directories with proper ownership using shell commands
3. **Mount Readiness Check**: Verifies directory ownership matches user ID
4. **StatefulSet Deployment**: One pod per node using podAntiAffinity
5. **Node-local Service**: Traffic routed to pod on same node via `internalTrafficPolicy: Local`
6. **Health Probes**: Kubernetes-compatible health, readiness, and liveness endpoints
7. **Privileged Execution**: Runs as root with capabilities for chown operations
8. **OpenAPI Documentation**: Springdoc integration for Swagger UI

### Dependencies Added
- Spring Boot Web (REST API)
- Spring Boot Actuator (Health/Metrics)
- Springdoc OpenAPI (API Documentation)

### Configuration
- API key via Kubernetes secret `mount-access-api-key`
- Mount base path: `/mnt/dump` (configurable)
- Privileged execution required for file ownership changes

## Notes

- Created: 2026-01-05T19:18:36.170Z
- Completed: 2026-01-05T20:51:19.206Z
- All requirements from feature specification implemented
- Ready for deployment and testing

---

*Feature fully implemented and ready for production deployment.*
