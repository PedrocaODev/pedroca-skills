"""Role routing resolver for Herdr subagents conforming to Spec 0003."""

from dataclasses import dataclass
from typing import ClassVar


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
            model="gemini-3.8-flash-low",
            effort="low",
            tier="Routine Execution",
            is_frontier=False,
        ),
        "librarian": RoleConfig(
            name="librarian",
            model="gemini-3.8-flash-low",
            effort="low",
            tier="Routine Execution",
            is_frontier=False,
        ),
        "fixer": RoleConfig(
            name="fixer",
            model="gemini-3.8-flash-medium",
            effort="medium",
            tier="Balanced Implementation & Delivery",
            is_frontier=False,
        ),
        "integrator": RoleConfig(
            name="integrator",
            model="gemini-3.8-flash-medium",
            effort="medium",
            tier="Balanced Implementation & Delivery",
            is_frontier=False,
        ),
        "craftsman": RoleConfig(
            name="craftsman",
            model="gemini-3.8-flash-high",
            effort="high",
            tier="Advanced Implementation & Routing",
            is_frontier=False,
        ),
        "evaluator": RoleConfig(
            name="evaluator",
            model="gemini-3.8-flash-high",
            effort="high",
            tier="Advanced Implementation & Routing",
            is_frontier=False,
        ),
        "council": RoleConfig(
            name="council",
            model="gemini-4-argon-high",
            effort="high",
            tier="Exceptional Frontier Reasoning",
            is_frontier=True,
        ),
        "oracle": RoleConfig(
            name="oracle",
            model="gemini-4-argon-high",
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
