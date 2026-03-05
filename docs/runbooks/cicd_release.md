# Runbook: CI/CD Delivery Friction & Risky Releases

## When to use
- CI is flaky, slow, or blocks releases.
- Deployments roll back unexpectedly or hang.
- Multiple deploys collide and cause instability.

## Objective
Make deployments boring: **deterministic pipelines**, **gated deploys**, **immutable versions**, **safe rollouts**.

## Triage checklist
1) Confirm pipeline health:
   - Do `lint` and `test` run on every PR?
   - Is there concurrency control to prevent overlapping deploys?
2) Confirm immutable artifact versioning:
   - Image tags based on commit SHA (or equivalent), not `latest`.
3) Confirm deploy is gated:
   - Deploy steps run only on main branch (or with explicit approvals/environments).
4) Confirm rollout safety:
   - `kubectl rollout status` is used with a timeout.
   - Deployments use probes and have reasonable `progressDeadlineSeconds`.

## Stabilization steps
1) Freeze deploys (pause CD) if incident impact is active.
2) Re-run pipeline with a single, known commit SHA.
3) If rollback is needed:
   - Roll back to the last known good SHA-tagged artifact.
4) Reduce flake:
   - Pin action versions.
   - Use concurrency groups.
   - Keep pipelines minimal and deterministic.

## Follow-ups
- Add a “release readiness” gate: validate + report as a CI artifact.
- Add canary/blue-green strategy in production (tooling choice is org-specific).

