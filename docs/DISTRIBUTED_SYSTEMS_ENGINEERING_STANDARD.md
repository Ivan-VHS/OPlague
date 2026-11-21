# Distributed resilience and trust

This repository is a local diagnostic workbench; the policy is a contract, not proof of distributed runtime implementation.

| Control | Requirement |
|---|---|
| Trust | default deny; authenticate and validate external inputs |
| Network | offline-capable; allowlisted verified artifacts only |
| Work | bounded timeout, queues, retries and payload sizes |
| Retry | exponential backoff + jitter; max 10 attempts |
| Breaker | bounded threshold/window/cooldown |
| Failure | fail closed or safe read-only fallback |
| Policy | no hidden bypass; privileged actions need human approval |
| Continuity | backups, migration notes and tested rollback |
| Supply chain | pinned dependencies, signatures and provenance |
| Audit | ownership, runbooks and incident evidence |

This local application does not require a cluster, consensus system or always-on coordinator.
