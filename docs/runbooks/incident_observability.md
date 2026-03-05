# Runbook: Reliability Under On-Call (Prometheus/Grafana + Runbook-First Alerts)

## When to use
- You’re paged for high error rate, latency, or availability loss.
- Alerts don’t have enough context (no runbook, unclear ownership).
- A Kubernetes rollout causes elevated errors or a database failover event occurs.

## Objective
Shorten MTTR by ensuring every alert has:
- **severity**
- **owner/team**
- **runbook URL**
- a minimal set of dashboards and SLO context

## First 5 minutes
1) Identify the service and severity from the alert labels/annotations.
2) Open the linked runbook (`runbook_url`).
3) Check dashboards:
   - request rate, error rate, latency
   - saturation (CPU/memory), pod restarts
4) If deployment-related:
   - check `kubectl rollout status` and recent changes.

## Common actions
- If errors spike after a deploy: roll back to the last known good SHA-tagged version.
- If pods restart: check OOM kills, missing limits, probe failures.
- If database is impacted: activate the documented failover procedure and validate connection pools/timeouts.

## Post-incident
- Add missing `runbook_url` to the alert rule and link to the correct procedure.
- Adjust alert thresholds to reduce noise (align to SLOs).
- Record what would have made the incident easier: one change, one owner.

