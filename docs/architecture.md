# Architecture (inputs → checks → outputs → runbooks)

This repository is a portfolio-grade, deterministic demo of how to reduce risk in three common DevOps failure modes:

1) **Infrastructure drift & fragile automation** (Terraform/EKS/Kubernetes patterns that diverge across environments).
2) **Delivery friction** (slow/flaky pipelines and risky releases).
3) **Reliability under real on-call pressure** (alerts without context, no runbooks, noisy failures).

## Data flow

**Inputs**
- `examples/good/`: sanitized “known-good” configurations representing repeatable infrastructure and delivery patterns.
- `examples/bad/`: intentionally risky anti-patterns used by tests to prove the validator catches what matters.
- `docs/runbooks/`: operational playbooks that connect detections to real incident actions.

**Checks**
- `src/portfolio_proof/` implements a fast, deterministic validator using **only Python’s standard library**.
- The validator uses conservative text-based checks (regex + structural heuristics) so it runs anywhere without dependencies.

**Outputs**
- `artifacts/report.md`: a human-readable report that:
  - maps findings to the three pain points,
  - recommends guardrails you can implement immediately,
  - links directly to runbooks for incident-time execution.

## Determinism principles

- No network calls.
- No timestamps in outputs.
- Stable ordering (paths and findings are sorted).
- Standard-library only (works on a clean machine with Python 3.11+).

## Threat model notes (portfolio scope)

This repo demonstrates controls and “secure defaults”, not a full production security program.

### Primary threats addressed (by design)
- **Accidental secret leakage**: examples are sanitized; validator flags common secret markers.
- **Unreviewable infrastructure changes**: guardrails enforce pinning/locking patterns and “plan before apply” workflows.
- **Risky releases**: CI/CD checks validate gating, concurrency, and immutable versioning patterns.
- **Alert fatigue / missing context**: observability checks require `runbook_url`, severity and ownership metadata.

### Out of scope (intentionally)
- Full Terraform/Kubernetes parsing (we use deterministic heuristics to keep the demo dependency-free).
- Real AWS/EKS access during demo (the goal is to validate the *shape* of the repo and patterns without credentials).
- End-to-end deployment automation.

