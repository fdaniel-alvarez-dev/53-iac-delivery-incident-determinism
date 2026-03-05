# 53-iac-delivery-incident-determinism

Portfolio repo demonstrating deterministic guardrails for:

1) **Infrastructure drift & fragile automation** (Terraform/EKS/Kubernetes)
2) **Delivery friction** (CI/CD + safe rollouts)
3) **Reliability under real on-call pressure** (Prometheus/Grafana + runbook-first alerts)

## Problem statement (what breaks in real orgs)

- **Drift**: infra changes aren’t fully reviewable; versions aren’t pinned; state isn’t locked; environments diverge.
- **Delivery friction**: pipelines are slow/flaky; deploys collide; “latest” ships; rollbacks are guesswork.
- **On-call pain**: alerts page without context; no runbooks; dashboards aren’t ready; MTTR balloons.

## Architecture overview

Inputs → checks → outputs → runbooks:

- Inputs: `examples/good/` and `examples/bad/`
- Checks: `python -m portfolio_proof validate`
- Outputs: `artifacts/report.md` (gitignored)
- Runbooks: `docs/runbooks/` (drift, delivery, incident response)

See `docs/architecture.md` for details.

## Quick start

```bash
make setup
make demo
```

Open `artifacts/report.md` to see a report that maps detections to the three pain points.

## Operating model (how this runs in a real team)

When presenting any DevOps project, start from the failure mode it prevents (drift, risky releases, slow incident response), then show the smallest repeatable demo that proves the guardrails work end-to-end.

## Security

- No secrets are committed. Inputs are sanitized.
- `.gitignore` blocks `.env*`, keys, `*credentials*`, `*.tfstate`, and `artifacts/`.
- The validator flags common secret markers in the input bundle.

See `docs/security.md`.

## Intentionally out of scope

- Real AWS/EKS access in the demo (no credentials required).
- Full Terraform/YAML parsing (the tool uses deterministic heuristics to keep it dependency-free).
