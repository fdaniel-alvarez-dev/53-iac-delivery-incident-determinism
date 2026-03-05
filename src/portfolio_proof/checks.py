from __future__ import annotations

import re
from pathlib import Path

from .fs import file_exists, load_text_files
from .model import Finding


_SECRET_MARKERS = (
    "BEGIN PRIVATE KEY",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_ACCESS_KEY_ID",
    "client_secret",
    "xoxb-",
    "ghp_",
    "-----BEGIN RSA PRIVATE KEY-----",
)


def _finding(
    id: str,
    title: str,
    *,
    severity: str,
    pain_point: str,
    remediation: str,
    evidence: list[str] | None = None,
) -> Finding:
    return Finding(
        id=id,
        title=title,
        severity=severity,
        pain_point=pain_point,
        remediation=remediation,
        evidence=tuple(evidence or []),
    )


def run_all_checks(*, inputs: Path, repo_root: Path) -> list[Finding]:
    inputs = inputs.resolve()
    repo_root = repo_root.resolve()

    findings: list[Finding] = []
    findings.extend(_check_secret_hygiene(inputs))

    findings.extend(_check_terraform_determinism(inputs))
    findings.extend(_check_kubernetes_safety(inputs))

    findings.extend(_check_delivery_guardrails(inputs))
    findings.extend(_check_reliability_observability(inputs, repo_root=repo_root))
    findings.extend(_check_runbooks_present(repo_root))

    return sorted(findings, key=lambda f: (f.severity, f.pain_point, f.id, f.title))


def _check_secret_hygiene(inputs: Path) -> list[Finding]:
    extensions = {".tf", ".yaml", ".yml", ".json", ".md", ".txt"}
    files = load_text_files(inputs, extensions=extensions)

    evidence: list[str] = []
    for f in files:
        for marker in _SECRET_MARKERS:
            if marker in f.text:
                evidence.append(f"{f.relpath}: contains '{marker}'")
                break

    if evidence:
        return [
            _finding(
                "SEC001",
                "Potential secret markers found in inputs",
                severity="ERROR",
                pain_point="security",
                remediation=(
                    "Remove secrets from repo inputs. Use environment variables or secret stores "
                    "(e.g., AWS Secrets Manager / Kubernetes Secrets / Vault) and never commit them."
                ),
                evidence=evidence,
            )
        ]
    return []


def _check_terraform_determinism(inputs: Path) -> list[Finding]:
    extensions = {".tf", ".tfvars", ".hcl", ".lock.hcl", ".terraform.lock.hcl"}
    files = load_text_files(inputs, extensions=extensions)
    tf_text = "\n".join(f.text for f in files if f.path.suffix in {".tf", ".hcl"})

    findings: list[Finding] = []

    if "terraform {" not in tf_text:
        findings.append(
            _finding(
                "IAC001",
                "Terraform root module not detected",
                severity="WARN",
                pain_point="iac_drift",
                remediation="Ensure the input bundle includes Terraform configuration (*.tf) with a terraform{} block.",
                evidence=["No 'terraform {' block found across *.tf/*.hcl inputs."],
            )
        )
        return findings

    if not re.search(r"required_version\s*=\s*\"[^\"]+\"", tf_text):
        findings.append(
            _finding(
                "IAC002",
                "Terraform required_version is not pinned",
                severity="ERROR",
                pain_point="iac_drift",
                remediation=(
                    "Pin the Terraform CLI version range (e.g., terraform { required_version = \">= 1.5.0, < 2.0.0\" }). "
                    "This reduces drift between developer machines and CI."
                ),
                evidence=["No terraform.required_version found."],
            )
        )

    if "required_providers" not in tf_text or not re.search(r"version\s*=\s*\"[^\"]+\"", tf_text):
        findings.append(
            _finding(
                "IAC003",
                "Terraform provider versions are not pinned",
                severity="ERROR",
                pain_point="iac_drift",
                remediation=(
                    "Pin provider versions under required_providers and commit the lockfile. "
                    "This prevents surprises from upstream provider changes."
                ),
                evidence=["No required_providers.version entries found."],
            )
        )

    backend_match = re.search(r"backend\s+\"([^\"]+)\"", tf_text)
    if not backend_match:
        findings.append(
            _finding(
                "IAC004",
                "Terraform backend not defined (risk of local state drift)",
                severity="ERROR",
                pain_point="iac_drift",
                remediation=(
                    "Use a remote backend with locking (e.g., S3 + DynamoDB) so teams share a single source of truth."
                ),
                evidence=["No terraform backend block found."],
            )
        )
    else:
        backend = backend_match.group(1).strip().lower()
        if backend == "local":
            findings.append(
                _finding(
                    "IAC005",
                    "Terraform backend is local (not safe for shared environments)",
                    severity="ERROR",
                    pain_point="iac_drift",
                    remediation="Switch to a remote backend with locking for shared environments.",
                    evidence=[f"Detected backend \"{backend}\"."],
                )
            )

    if not any(f.path.name == ".terraform.lock.hcl" for f in files):
        findings.append(
            _finding(
                "IAC006",
                "Terraform lockfile missing",
                severity="ERROR",
                pain_point="iac_drift",
                remediation="Commit .terraform.lock.hcl for deterministic provider resolution.",
                evidence=[".terraform.lock.hcl not present in input bundle."],
            )
        )

    return findings


def _check_kubernetes_safety(inputs: Path) -> list[Finding]:
    files = load_text_files(inputs, extensions={".yaml", ".yml"})
    kube_text = "\n".join(f.text for f in files)
    findings: list[Finding] = []

    if not re.search(r"kind:\\s*(Deployment|StatefulSet|DaemonSet)", kube_text):
        return [
            _finding(
                "K8S001",
                "Kubernetes workload manifests not detected",
                severity="WARN",
                pain_point="iac_drift",
                remediation="Include Kubernetes workload manifests (Deployment/StatefulSet) in the input bundle.",
                evidence=["No kind: Deployment/StatefulSet/DaemonSet found in *.yml/*.yaml inputs."],
            )
        ]

    required = {
        "readinessProbe": "Add a readinessProbe to prevent traffic before the app is ready.",
        "livenessProbe": "Add a livenessProbe to enable self-healing on deadlocks/hangs.",
        "resources:": "Define CPU/memory requests and limits for predictable scheduling and stability.",
        "securityContext:": "Use a securityContext (non-root, drop capabilities) for safer defaults.",
    }
    for token, remediation in required.items():
        if token not in kube_text:
            findings.append(
                _finding(
                    f"K8S{len(findings)+2:03d}",
                    f"Missing Kubernetes safety control: {token}",
                    severity="ERROR",
                    pain_point="iac_drift",
                    remediation=remediation,
                    evidence=[f"Token '{token}' not found in Kubernetes manifests."],
                )
            )

    if "progressDeadlineSeconds" not in kube_text:
        findings.append(
            _finding(
                "K8S090",
                "Deployment progress deadline not set",
                severity="WARN",
                pain_point="delivery",
                remediation=(
                    "Set progressDeadlineSeconds so stuck rollouts fail fast and trigger an actionable alert/runbook."
                ),
                evidence=["No progressDeadlineSeconds found in workload manifests."],
            )
        )

    return findings


def _check_delivery_guardrails(inputs: Path) -> list[Finding]:
    pipeline_files = load_text_files(inputs, extensions={".yaml", ".yml"})
    pipeline_text = "\n".join(f.text for f in pipeline_files)
    if not pipeline_text:
        return [
            _finding(
                "DEL001",
                "No pipeline configuration detected in inputs",
                severity="WARN",
                pain_point="delivery",
                remediation="Include a pipeline example (e.g., GitHub Actions workflow yaml) in the input bundle.",
                evidence=["No *.yml/*.yaml files found (or empty)."],
            )
        ]

    findings: list[Finding] = []

    if "concurrency:" not in pipeline_text:
        findings.append(
            _finding(
                "DEL002",
                "Pipeline concurrency control missing (risk of deploy collisions)",
                severity="ERROR",
                pain_point="delivery",
                remediation="Add a concurrency group to prevent overlapping deploys (especially to production).",
                evidence=["No 'concurrency:' found."],
            )
        )

    if "make lint" not in pipeline_text or "make test" not in pipeline_text:
        findings.append(
            _finding(
                "DEL003",
                "Pipeline does not run lint+test deterministically",
                severity="ERROR",
                pain_point="delivery",
                remediation="Run make lint and make test on every push/PR to catch drift and regressions early.",
                evidence=["Missing 'make lint' and/or 'make test' in pipeline yaml."],
            )
        )

    if re.search(r"actions/checkout@(?:main|master)", pipeline_text) or re.search(
        r"actions/setup-python@(?:main|master)", pipeline_text
    ):
        findings.append(
            _finding(
                "DEL004",
                "Pipeline pins actions to floating branches (risk of breaking changes)",
                severity="ERROR",
                pain_point="delivery",
                remediation="Pin GitHub Actions to version tags (v4, v5) or commit SHAs for determinism.",
                evidence=["Detected checkout/setup-python pinned to main/master."],
            )
        )

    if "GITHUB_SHA" not in pipeline_text:
        findings.append(
            _finding(
                "DEL005",
                "Immutable versioning signal missing (e.g., commit SHA)",
                severity="WARN",
                pain_point="delivery",
                remediation="Use immutable artifact versioning (e.g., image tag = $GITHUB_SHA) for safe rollbacks and traceability.",
                evidence=["No 'GITHUB_SHA' reference found."],
            )
        )

    if "kubectl rollout status" not in pipeline_text:
        findings.append(
            _finding(
                "DEL006",
                "Deploy step does not wait for rollout completion",
                severity="WARN",
                pain_point="delivery",
                remediation="Use 'kubectl rollout status --timeout=...' to fail fast and surface actionable errors.",
                evidence=["No 'kubectl rollout status' found."],
            )
        )

    if not re.search(r"refs/heads/main", pipeline_text) and "environment:" not in pipeline_text:
        findings.append(
            _finding(
                "DEL007",
                "Deploy gating not detected (risk of deploying from arbitrary branches)",
                severity="WARN",
                pain_point="delivery",
                remediation="Gate deploys to main branch and/or protected environments with approvals.",
                evidence=["No 'refs/heads/main' or 'environment:' found."],
            )
        )

    return findings


def _check_reliability_observability(inputs: Path, *, repo_root: Path) -> list[Finding]:
    files = load_text_files(inputs, extensions={".yaml", ".yml", ".json"})
    text = "\n".join(f.text for f in files)

    findings: list[Finding] = []
    if "PrometheusRule" not in text and "groups:" not in text:
        findings.append(
            _finding(
                "REL001",
                "Prometheus alert rules not detected",
                severity="WARN",
                pain_point="reliability",
                remediation="Include PrometheusRule-style alert rules that carry runbook links and ownership metadata.",
                evidence=["No PrometheusRule/groups found in inputs."],
            )
        )
    else:
        if "runbook_url" not in text:
            findings.append(
                _finding(
                    "REL002",
                    "Alerts missing runbook_url (slows on-call response)",
                    severity="ERROR",
                    pain_point="reliability",
                    remediation="Add a runbook_url annotation/label to every alert, pointing to a concrete procedure.",
                    evidence=["No 'runbook_url' found in alert definitions."],
                )
            )
        if "severity" not in text:
            findings.append(
                _finding(
                    "REL003",
                    "Alerts missing severity",
                    severity="ERROR",
                    pain_point="reliability",
                    remediation="Add severity labels (page/ticket) to reduce noise and drive correct response.",
                    evidence=["No 'severity' found in alert definitions."],
                )
            )
        if "team" not in text and "owner" not in text:
            findings.append(
                _finding(
                    "REL004",
                    "Alerts missing explicit ownership",
                    severity="WARN",
                    pain_point="reliability",
                    remediation="Add team/owner labels so alerts route to the right responders.",
                    evidence=["No 'team' or 'owner' found in alert definitions."],
                )
            )

    if not any("grafana" in f.relpath.lower() and f.path.suffix == ".json" for f in files):
        findings.append(
            _finding(
                "REL005",
                "Grafana dashboard JSON not detected",
                severity="WARN",
                pain_point="reliability",
                remediation="Include at least one dashboard (JSON) that responders can open immediately.",
                evidence=["No grafana*.json found in inputs."],
            )
        )

    if not re.search(r"availability_target", text) and not re.search(r"slo", text, re.IGNORECASE):
        findings.append(
            _finding(
                "REL006",
                "SLO definition not detected",
                severity="WARN",
                pain_point="reliability",
                remediation="Define an SLO target and error budget policy to align alerts and release risk decisions.",
                evidence=["No availability_target / slo found in inputs."],
            )
        )

    if not file_exists(repo_root, "docs/runbooks/incident_observability.md"):
        findings.append(
            _finding(
                "REL007",
                "On-call runbook missing from docs",
                severity="ERROR",
                pain_point="reliability",
                remediation="Add an incident runbook and link it from alerts via runbook_url.",
                evidence=["docs/runbooks/incident_observability.md not found."],
            )
        )

    return findings


def _check_runbooks_present(repo_root: Path) -> list[Finding]:
    runbooks_dir = repo_root / "docs" / "runbooks"
    if not runbooks_dir.is_dir():
        return [
            _finding(
                "DOC001",
                "Runbooks directory missing",
                severity="ERROR",
                pain_point="reliability",
                remediation="Add docs/runbooks with at least three concrete runbooks tied to drift, delivery, and incidents.",
                evidence=["docs/runbooks/ does not exist."],
            )
        ]

    md = sorted(p for p in runbooks_dir.glob("*.md") if p.is_file())
    if len(md) < 3:
        return [
            _finding(
                "DOC002",
                "Insufficient runbooks",
                severity="ERROR",
                pain_point="reliability",
                remediation="Add at least three runbooks tied to the three pain points (drift, delivery, incidents).",
                evidence=[f"Found {len(md)} runbook(s) in docs/runbooks/."],
            )
        ]
    return []
