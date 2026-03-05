# Runbook: IaC Drift & Fragile Automation

## When to use
- Terraform plan differs unexpectedly between environments.
- EKS/Kubernetes resources drift from the declared state.
- “It worked in staging” but production behaves differently.

## Objective
Make changes reviewable and repeatable: **pin**, **lock**, **plan**, and **apply with gates**.

## Triage checklist (10 minutes)
1) Confirm the change is coming from version drift:
   - Terraform CLI version and provider versions.
   - Presence of `.terraform.lock.hcl`.
2) Confirm the state backend is remote + locked:
   - Avoid local state for shared environments.
3) Confirm the Kubernetes manifests include safety rails:
   - `readinessProbe`, `livenessProbe`
   - resource `requests`/`limits`
   - `securityContext` with non-root defaults

## Stabilization steps
1) Re-run a plan with the pinned toolchain.
2) If drift is detected:
   - Stop automated applies.
   - Generate a fresh plan and attach it to the change review.
3) If drift is *not* expected (e.g., manual changes):
   - Reconcile by applying the desired state via the normal pipeline (don’t “click-ops”).

## Follow-ups (post-incident)
- Add a drift detection job (plan + diff) on a schedule.
- Require PR review for infra changes.
- Expand policy checks to enforce minimum Kubernetes safety controls.

