"""Escalation guard enforcing evaluator approval receipts for frontier subagents."""

from pathlib import Path

from .resolver import RoleConfig


class EscalationRequiredError(Exception):
    """Raised when a frontier role is invoked without an escalation receipt."""
    pass


class InvalidEscalationReceiptError(Exception):
    """Raised when an escalation receipt is invalid or missing."""
    pass


class EscalationGuard:
    """Guards invocation of frontier-tier models behind evaluator receipts."""

    @classmethod
    def check(cls, role_config: RoleConfig, receipt_path: str | Path | None) -> None:
        """Validate escalation requirements for a role configuration.

        Args:
            role_config: The resolved subagent role configuration.
            receipt_path: Path to the evaluator escalation receipt file.

        Raises:
            EscalationRequiredError: If role is frontier and no receipt path is provided.
            InvalidEscalationReceiptError: If the receipt path is non-existent or lacks approval.
        """
        if not role_config.is_frontier:
            return

        if receipt_path is None:
            raise EscalationRequiredError(
                f"Frontier role '{role_config.name}' ({role_config.model}) requires an evaluator escalation receipt."
            )

        if isinstance(receipt_path, str):
            stripped = receipt_path.strip()
            if not stripped:
                raise EscalationRequiredError(
                    f"Frontier role '{role_config.name}' ({role_config.model}) requires an evaluator escalation receipt."
                )
            path = Path(stripped)
        elif isinstance(receipt_path, Path):
            path = receipt_path
        else:
            raise EscalationRequiredError(
                f"Frontier role '{role_config.name}' ({role_config.model}) requires an evaluator escalation receipt."
            )

        if not path.is_file():
            raise InvalidEscalationReceiptError(f"Escalation receipt not found at {receipt_path}")

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            raise InvalidEscalationReceiptError(f"Failed to read escalation receipt at {receipt_path}: {e}") from e

        if "DECISION: ESCALATE" not in content:
            raise InvalidEscalationReceiptError("Escalation receipt does not contain 'DECISION: ESCALATE'")
