# Security & Secrets Handling

## Goals
- Keep the demo **safe by default**: no secrets in repo, no secret printing, and guardrails that detect obvious leaks.
- Encourage least privilege and auditability patterns used in modern DevOps teams.

## Controls demonstrated

### 1) Secret hygiene
- `.gitignore` blocks common sensitive file patterns (`.env*`, keys, `*credentials*`, `*.tfstate`).
- `portfolio_proof validate` scans inputs for high-signal secret markers (e.g., private key headers, common token prefixes).
- Examples under `examples/` are **sanitized** and use obviously fake identifiers.

### 2) Least privilege patterns (conceptual)
- Infrastructure guardrails encourage remote state backends (auditability + locking) and provider/version pinning.
- Delivery guardrails encourage immutable artifact tagging (e.g., commit SHA) and gated deployments.

### 3) Auditability
- The report is written to `artifacts/report.md` (gitignored) and is deterministic, making it suitable for attaching to PRs or CI artifacts.

## What this repo will not do
- It will not call cloud APIs.
- It will not manage credentials.
- It will not attempt secret scanning beyond high-signal heuristics (use dedicated scanners in production).

