# codex k8s/OpenShift deployment options and production-readiness audit

**Date:** 2026-02-17  
**Type:** Deep repository audit  
**Scope:** Kubernetes (CNCF), OpenShift, production deployability

## Verdict

1. `CNCF Kubernetes`: **Yes, but partial**
2. `OpenShift`: **Yes, but partial**
3. `Production-ready on k8s/OpenShift as-is`: **No**

## Evidence

- Kubernetes manifests exist via Kustomize: `k8s/base/kustomization.yml:1`, `k8s/overlays/dev/kustomization.yml:1`, `k8s/overlays/prod/kustomization.yml:1`.
- The k8s base covers mainly API + JanusGraph, not full platform services: `k8s/base/kustomization.yml:6`, `k8s/base/api-deployment.yml:4`, `k8s/base/janusgraph-deployment.yml:4`.
- OpenShift support exists in Helm with Route resource: `helm/janusgraph-banking/templates/route.yaml:2`.
- OpenShift/Tekton CI artifact exists: `tekton/pipelines/ci-pipeline.yaml:14`.
- Active supported deployment path is Podman Compose (not k8s): `README.md:7`, `AGENTS.md:161`, `scripts/deployment/deploy_full_stack.sh:43`.
- Full runtime stack in compose is much broader (HCD, Pulsar, Vault, OpenSearch, consumers): `config/compose/docker-compose.full.yml:37`, `config/compose/docker-compose.full.yml:75`, `config/compose/docker-compose.full.yml:226`, `config/compose/docker-compose.full.yml:434`, `config/compose/docker-compose.full.yml:604`, `config/compose/docker-compose.full.yml:643`, `config/compose/docker-compose.full.yml:671`.
- k8s secrets/config still include non-prod placeholders/defaults: `k8s/base/secrets.yml:10`, `k8s/base/secrets.yml:11`, `k8s/base/configmaps.yml:23`.
- Docs claim “Production Ready” for OpenShift, but another repo doc flags critical gaps/partial conversion: `docs/architecture/openshift-migration-operations.md:5`, `docs/architecture/openshift-deployment-manifests.md:5`, `docs/architecture/openshift-review-and-improvements.md:14`, `docs/architecture/openshift-review-and-improvements.md:643`, `docs/architecture/openshift-review-and-improvements.md:689`.

## Conclusion

The repository contains k8s/OpenShift artifacts and architecture documentation, but the currently enforced and operational runtime path is Podman Compose. k8s/OpenShift is presently design + partial implementation, not a fully production-executable stack from this repository alone.
