   Summary of Changes

   📂 Folder Organization

     - ✅ All markdown documents moved to /docs folder
     - ✅ Only README.md remains in root (main entry point)
     - ✅ Created organized structure:
       - docs/commits/ (features, fixes, refactors)
       - docs/deployments/ (deployment guides)
       - docs/development/ (dev setup)

   🔄 README.md Updates

   Updated root README.md with:

     - ✅ New documentation links pointing to /docs
       - [docs/plan.md](docs/plan.md) - Implementation plan
       - [docs/project-structure-status.md](docs/project-structure-status.md) - Status
       - [docs/deployments/](docs/deployments/) - Deployment guides
       - [docs/development/](docs/development/) - Dev setup
     - ✅ Simplified deployment sections with references to:
       - [k8s/README.md](k8s/README.md) - Kubernetes guide
       - [helm/README.md](helm/README.md) - Helm guide
       - [openshift/README.md](openshift/README.md) - OpenShift guide
     - ✅ Removed outdated internal file references (openshift-rbac.yaml, statefulset-volume.yaml, etc.)
     - ✅ Simplified Architecture section with links to detailed docs

   📦 Created Deployment Folders

     - ✅ k8s/ - Kubernetes manifests with README
     - ✅ helm/ - Helm charts with Chart.yaml and values files
     - ✅ openshift/ - OpenShift configs (RBAC, Routes, BuildConfigs)

   All references are now clean and properly organized! 🎉