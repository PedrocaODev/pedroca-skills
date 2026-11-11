"""Role routing resolver for Herdr subagents conforming to Spec 0003."""

import os
from dataclasses import dataclass
from typing import ClassVar

ROUTINE_MODEL = os.getenv("HERDR_MODEL_ROUTINE", "routine")
BALANCED_MODEL = os.getenv("HERDR_MODEL_BALANCED", "balanced")
ADVANCED_MODEL = os.getenv("HERDR_MODEL_ADVANCED", "advanced")
FRONTIER_MODEL = os.getenv("HERDR_MODEL_FRONTIER", "frontier")


class UnknownRoleError(Exception):
    """Raised when an unknown subagent role is specified."""
    pass


@dataclass(frozen=True)
class RoleConfig:
    name: str
    model: str
    effort: str
    tier: str
    is_frontier: bool


class RoleResolver:
    """Resolves functional agent roles to deterministic model configurations."""

    _ROLES: ClassVar[dict[str, RoleConfig]] = {
        "runner": RoleConfig(
            name="runner",
            model=ROUTINE_MODEL,
            effort="low",
            tier="Routine Execution",
            is_frontier=False,
        ),
        "librarian": RoleConfig(
            name="librarian",
            model=ROUTINE_MODEL,
            effort="low",
            tier="Routine Execution",
            is_frontier=False,
        ),
        "fixer": RoleConfig(
            name="fixer",
            model=BALANCED_MODEL,
            effort="medium",
            tier="Balanced Implementation & Delivery",
            is_frontier=False,
        ),
        "integrator": RoleConfig(
            name="integrator",
            model=BALANCED_MODEL,
            effort="medium",
            tier="Balanced Implementation & Delivery",
            is_frontier=False,
        ),
        "craftsman": RoleConfig(
            name="craftsman",
            model=ADVANCED_MODEL,
            effort="high",
            tier="Advanced Implementation & Routing",
            is_frontier=False,
        ),
        "evaluator": RoleConfig(
            name="evaluator",
            model=ADVANCED_MODEL,
            effort="high",
            tier="Advanced Implementation & Routing",
            is_frontier=False,
        ),
        "council": RoleConfig(
            name="council",
            model=FRONTIER_MODEL,
            effort="high",
            tier="Exceptional Frontier Reasoning",
            is_frontier=True,
        ),
        "oracle": RoleConfig(
            name="oracle",
            model=FRONTIER_MODEL,
            effort="high",
            tier="Exceptional Frontier Reasoning",
            is_frontier=True,
        ),
    }

    @classmethod
    def _normalize_role(cls, role: str) -> str:
        if not isinstance(role, str):
            raise UnknownRoleError(f"Unknown subagent role: '{role}'")
        normalized = role.strip()
        if normalized.startswith("@"):
            normalized = normalized[1:].strip()
        return normalized.lower()

    @classmethod
    def resolve(cls, role: str) -> RoleConfig:
        normalized = cls._normalize_role(role)
        if normalized not in cls._ROLES:
            raise UnknownRoleError(f"Unknown subagent role: '{role}'")
        return cls._ROLES[normalized]

    @classmethod
    def list_roles(cls) -> list[RoleConfig]:
        return list(cls._ROLES.values())

    @classmethod
    def is_valid_role(cls, role: str) -> bool:
        try:
            normalized = cls._normalize_role(role)
            return normalized in cls._ROLES
        except UnknownRoleError:
            return False
