"""Immutable, non-applying driver-operation plans with precondition checks."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Mapping

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
_OPERATIONS = {"install", "update", "rollback"}
_SIGNATURE_STATES = {"trusted", "unsigned", "invalid", "unknown"}
_AUDIT_STATES = {"passed", "warning", "failed", "not-run"}


class DryRunError(ValueError):
    """Invalid dry-run input or policy."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise DryRunError(f"{label} must be a 64-character SHA-256 digest")
    return value.lower()


def build_dry_run_plan(*, device: Mapping[str, Any], package: Mapping[str, Any], match: Mapping[str, Any],
                       operation: str = "install", audit_status: str = "not-run",
                       signature_status: str = "unknown", allow_unsigned: bool = False,
                       require_trusted_signature: bool = True, inventory_revision: str | int | None = None,
                       created_at: str | None = None) -> dict[str, Any]:
    """Build a plan document only. This function never performs system actions."""
    if not isinstance(operation, str) or operation not in _OPERATIONS:
        raise DryRunError(f"operation must be one of {sorted(_OPERATIONS)}")
    if not isinstance(audit_status, str) or audit_status not in _AUDIT_STATES:
        raise DryRunError(f"audit_status must be one of {sorted(_AUDIT_STATES)}")
    if not isinstance(signature_status, str) or signature_status not in _SIGNATURE_STATES:
        raise DryRunError(f"signature_status must be one of {sorted(_SIGNATURE_STATES)}")
    if not isinstance(device, Mapping) or not isinstance(package, Mapping) or not isinstance(match, Mapping):
        raise TypeError("device, package, and match must be JSON objects")
    if not isinstance(allow_unsigned, bool) or not isinstance(require_trusted_signature, bool):
        raise TypeError("signature policy flags must be booleans")

    instance_id = str(device.get("instance_id") or device.get("pnp_id") or "").strip()
    if not instance_id or len(instance_id) > 2048:
        raise DryRunError("device must include a stable instance_id / pnp_id")
    digest = _sha(package.get("sha256"), "package.sha256")
    package_name = str(package.get("package_id") or package.get("file_name") or "").strip()
    if not package_name:
        raise DryRunError("package must include package_id or file_name")

    match_type = match.get("match_type")
    if not isinstance(match_type, str) or match_type not in {"hardware-id", "compatible-id"} or match.get("matched") is not True:
        raise DryRunError("a confirmed direct Hardware ID or Compatible ID match is required")
    matched_id = match.get("matched_device_id")
    matched_inf_id = match.get("matched_inf_id")
    ids = device.get("hardware_ids", []) if match_type == "hardware-id" else device.get("compatible_ids", [])
    if (not isinstance(ids, (list, tuple)) or not isinstance(matched_id, str) or not matched_id.strip()
            or matched_id.casefold() not in {x.casefold() for x in ids if isinstance(x, str)}):
        raise DryRunError("match evidence does not belong to the selected device")
    declared_ids = package.get("device_ids")
    if not isinstance(declared_ids, (list, tuple)) or not declared_ids or not all(isinstance(x, str) for x in declared_ids):
        raise DryRunError("package must include device_ids extracted from the selected INF")
    if not isinstance(matched_inf_id, str) or matched_inf_id.casefold() not in {x.casefold() for x in declared_ids}:
        raise DryRunError("matched INF ID is not declared by the selected package")
    if matched_id.casefold() != matched_inf_id.casefold():
        raise DryRunError("device and INF match IDs must be exactly equal")

    blockers: list[str] = []
    warnings: list[str] = []
    if audit_status in {"not-run", "failed"}:
        blockers.append(f"package audit state is {audit_status}")
    elif audit_status == "warning":
        warnings.append("package audit contains warnings and requires operator review")
    if signature_status == "invalid":
        blockers.append("package signature evidence is invalid")
    elif signature_status == "unsigned":
        if not allow_unsigned:
            blockers.append("unsigned package is denied by the active policy")
        else:
            warnings.append("unsigned package explicitly allowed by policy; operator review required")
    elif signature_status == "unknown":
        if require_trusted_signature:
            blockers.append("trusted signature has not been established")
        else:
            warnings.append("signature status is unknown; authenticity has not been established")
    if match_type == "compatible-id":
        warnings.append("candidate matched only a Compatible ID; verify the exact device model and vendor guidance")
    if inventory_revision is not None and not (
        isinstance(inventory_revision, str) or (isinstance(inventory_revision, int) and not isinstance(inventory_revision, bool) and inventory_revision >= 0)
    ):
        raise DryRunError("inventory_revision must be a non-negative integer, string, or null")

    status = "blocked" if blockers else "ready-for-review"
    plan = {
        "schema": "oplage.driver-operation-plan.v1",
        "created_at": created_at or _now(),
        "operation": operation,
        "status": status,
        "will_modify_system": False,
        "execution_supported": False,
        "target": {
            "device_instance_id": instance_id,
            "device_name": str(device.get("name") or "")[:1024],
            "package_id": package_name,
            "package_sha256": digest,
            "package_version": str(package.get("version") or ""),
        },
        "compatibility_evidence": dict(match),
        "security_evidence": {
            "audit_status": audit_status,
            "signature_status": signature_status,
            "policy": {"allow_unsigned": allow_unsigned, "require_trusted_signature": require_trusted_signature},
        },
        "preconditions": {
            "package_sha256": digest,
            "device_instance_id": instance_id,
            "inventory_revision": inventory_revision,
            "revalidate_before_any_future_apply": True,
        },
        "actions": [
            {"stage": "validate-target", "description": "Verify target device identity and current PnP state", "mutates_system": False},
            {"stage": "verify-package", "description": "Recompute SHA-256 and re-check package audit/signature evidence", "mutates_system": False},
            {"stage": "review", "description": "Require explicit human approval in a future deployment implementation", "mutates_system": False},
        ],
        "warnings": warnings,
        "blockers": blockers,
        "limitations": [
            "This is a planning document, not an installer",
            "No SetupAPI, pnputil, DISM, service, registry, or kernel operation is invoked",
            "Direct ID equality is not a Windows SetupAPI rank or compatibility guarantee",
        ],
    }
    plan["plan_sha256"] = hashlib.sha256(_canonical(plan)).hexdigest()
    return plan


def check_plan_freshness(plan: Mapping[str, Any], *, current_package_sha256: str,
                          current_device_instance_id: str, current_inventory_revision: str | int | None = None) -> dict[str, Any]:
    """Detect stale package/device/inventory evidence before any future apply stage."""
    if not isinstance(plan, Mapping) or plan.get("schema") != "oplage.driver-operation-plan.v1":
        raise DryRunError("unsupported operation plan")
    preconditions = plan.get("preconditions")
    if not isinstance(preconditions, Mapping):
        raise DryRunError("operation plan has no preconditions")
    supplied_plan_digest = plan.get("plan_sha256")
    unsigned_plan = {key: value for key, value in plan.items() if key != "plan_sha256"}
    expected_plan_digest = hashlib.sha256(_canonical(unsigned_plan)).hexdigest()
    current_digest = _sha(current_package_sha256, "current_package_sha256")
    reasons = []
    if supplied_plan_digest != expected_plan_digest:
        reasons.append("operation plan content digest is invalid or the plan was modified")
    if plan.get("status") != "ready-for-review":
        reasons.append("operation plan is blocked or has not passed review gates")
    if plan.get("will_modify_system") is not False or plan.get("execution_supported") is not False:
        reasons.append("operation plan violates the non-applying dry-run contract")
    if not isinstance(plan.get("blockers"), list) or plan.get("blockers"):
        reasons.append("operation plan contains blocking policy findings")
    if not isinstance(current_device_instance_id, str) or not current_device_instance_id.strip():
        raise DryRunError("current_device_instance_id must be a non-empty string")
    if current_digest != preconditions.get("package_sha256"):
        reasons.append("package SHA-256 changed since plan creation")
    if current_device_instance_id.casefold() != str(preconditions.get("device_instance_id", "")).casefold():
        reasons.append("target device instance ID changed")
    planned_revision = preconditions.get("inventory_revision")
    if planned_revision is not None and current_inventory_revision != planned_revision:
        reasons.append("device inventory revision changed")
    return {"schema": "oplage.plan-freshness.v1", "fresh": not reasons,
            "status": "fresh" if not reasons else "stale", "reasons": reasons}
