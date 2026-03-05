from __future__ import annotations

from pathlib import Path

from .model import Finding


def _group(findings: list[Finding], pain_point: str) -> list[Finding]:
    return [f for f in findings if f.pain_point == pain_point]


def generate_report_markdown(
    *,
    inputs: Path,
    repo_root: Path,
    findings: list[Finding],
    negative_example: tuple[Path, list[Finding]] | None,
) -> str:
    errors = [f for f in findings if f.severity == "ERROR"]
    warns = [f for f in findings if f.severity == "WARN"]
    infos = [f for f in findings if f.severity == "INFO"]

    lines: list[str] = []
    lines.append("# Deterministic Guardrails Report")
    lines.append("")
    lines.append("This report is generated deterministically (no network, no timestamps).")
    lines.append("")
    lines.append("## What this proves (interview framing)")
    lines.append("")
    lines.append("- IaC drift is reduced via version pinning, remote state patterns, and Kubernetes safety rails.")
    lines.append("- Delivery friction is reduced via deterministic CI gates, concurrency control, and safe rollout signals.")
    lines.append("- Reliability improves when alerts carry ownership + runbook URLs and responders have ready-to-use runbooks.")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- Input bundle: `{inputs}`")
    lines.append(f"- Repo root: `{repo_root}`")
    lines.append("")
    lines.append("## Validation results")
    lines.append("")
    lines.append(f"- Errors: **{len(errors)}**")
    lines.append(f"- Warnings: **{len(warns)}**")
    lines.append(f"- Info: **{len(infos)}**")
    lines.append("")
    lines.append("`validate` exits non-zero when **Errors > 0**.")
    lines.append("")

    def section(title: str, items: list[Finding]) -> None:
        lines.append(f"## {title}")
        lines.append("")
        if not items:
            lines.append("- ✅ No findings.")
            lines.append("")
            return
        for f in items:
            lines.append(f"- **[{f.severity}] {f.id} — {f.title}**")
            lines.append(f"  - Remediation: {f.remediation}")
            if f.evidence:
                lines.append("  - Evidence:")
                for ev in f.evidence:
                    lines.append(f"    - {ev}")
        lines.append("")

    section("Pain Point 1: Infrastructure drift & fragile automation", _group(findings, "iac_drift"))
    section("Pain Point 2: Delivery friction (CI/CD & releases)", _group(findings, "delivery"))
    section("Pain Point 3: Reliability under on-call pressure", _group(findings, "reliability"))
    section("Security guardrails (no secrets)", _group(findings, "security"))

    lines.append("## Runbooks (what to do during an incident)")
    lines.append("")
    lines.append("- `docs/runbooks/iac_drift.md`")
    lines.append("- `docs/runbooks/cicd_release.md`")
    lines.append("- `docs/runbooks/incident_observability.md`")
    lines.append("")

    if negative_example is not None:
        bad_path, bad_findings = negative_example
        bad_errors = [f for f in bad_findings if f.severity == "ERROR"]
        lines.append("## Negative example (what would fail)")
        lines.append("")
        lines.append(f"- Scanned: `{bad_path}`")
        lines.append(f"- Errors: **{len(bad_errors)}**")
        lines.append("")
        if bad_errors:
            lines.append("Top errors:")
            for f in bad_errors[:8]:
                lines.append(f"- {f.id}: {f.title}")
            lines.append("")

    lines.append("## Next steps (portfolio expansion)")
    lines.append("")
    lines.append("- Replace heuristics with real parsers (Terraform/HCL, YAML) in production codebases.")
    lines.append("- Add policy-as-code integration (OPA/Conftest) and artifact signing (SLSA provenance).")
    lines.append("- Wire these checks into CI as required status checks for infra and deploy PRs.")
    lines.append("")
    return "\n".join(lines)


def write_report(path: Path, markdown: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")

