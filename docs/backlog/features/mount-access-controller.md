# Feature: Mount Access Controller

**Status:** Proposed  
**Priority:** TBD  
**Component:** TBD  
**Effort:** TBD  
**Epic:** TBD  
**Created:** 2026-01-05T19:18:36.170Z

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

## Notes

- Created: 2026-01-05T19:18:36.170Z
- Awaiting detailed requirements and design discussion

---

*This is a placeholder feature proposal. Further details will be provided in future updates.*
