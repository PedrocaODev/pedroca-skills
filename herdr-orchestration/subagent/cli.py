"""Command-line interface for the Herdr Subagent Model Routing Dispatcher."""

import argparse
import sys
from .dispatcher import SubagentDispatcher
from .guard import EscalationRequiredError, InvalidEscalationReceiptError
from .resolver import RoleResolver, UnknownRoleError


def _print_roles_table() -> None:
    roles = RoleResolver.list_roles()
    header = f"{'Role':<12} {'Model':<26} {'Effort':<8} {'Tier':<42} {'Frontier'}"
    print(header)
    print("-" * len(header))
    for r in roles:
        print(
            f"{r.name:<12} {r.model:<26} {r.effort:<8} {r.tier:<42} {str(r.is_frontier)}"
        )


def main(argv: list[str] | None = None) -> int:
    """Entry point for the herdr-subagent CLI."""
    parser = argparse.ArgumentParser(
        description="Herdr Subagent Model Routing Dispatcher"
    )
    parser.add_argument(
        "--list-roles",
        action="store_true",
        help="Print table of all roles, their models, efforts, tiers, and whether they are frontier.",
    )
    parser.add_argument(
        "role",
        nargs="?",
        default=None,
        help="Functional role name (e.g. runner, fixer, craftsman, oracle).",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Prompt / task instructions for the subagent.",
    )
    parser.add_argument(
        "--escalation-receipt",
        type=str,
        default=None,
        help="Path to evaluator escalation receipt.",
    )
    parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="Custom session identifier.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Integer timeout in seconds (default: 300).",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Keep terminal pane open on exit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without spawning processes.",
    )
    parser.add_argument(
        "--cwd",
        type=str,
        default=None,
        help="Target working directory.",
    )

    raw_args = sys.argv[1:] if argv is None else list(argv)
    extra_args: list[str] | None = None
    if "--" in raw_args:
        idx = raw_args.index("--")
        cli_args = raw_args[:idx]
        extra_args = raw_args[idx + 1 :]
    else:
        cli_args = raw_args

    try:
        args = parser.parse_args(cli_args)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1

    if args.list_roles:
        _print_roles_table()
        return 0

    if not args.role:
        sys.stderr.write("Error: 'role' is required unless --list-roles is specified.\n")
        return 2

    if not args.prompt:
        sys.stderr.write("Error: 'prompt' is required unless --list-roles is specified.\n")
        return 1

    try:
        dispatcher = SubagentDispatcher()
        result = dispatcher.dispatch(
            role=args.role,
            prompt=args.prompt,
            session_id=args.session_id,
            escalation_receipt=args.escalation_receipt,
            timeout_seconds=args.timeout,
            cleanup=not args.no_cleanup,
            cwd=args.cwd,
            dry_run=args.dry_run,
            extra_args=extra_args if extra_args else None,
        )

        if args.dry_run:
            print(f"Role: {result.role.name}")
            print(f"Model: {result.role.model}")
            print(f"Effort: {result.role.effort}")
            print(f"Tier: {result.role.tier}")
            print(f"Frontier: {result.role.is_frontier}")
            print("Planned commands:")
            for cmd in result.planned_commands:
                print(" ".join(cmd))
            return 0

        if result.receipt_content:
            print(result.receipt_content)
        return result.exit_code

    except UnknownRoleError as err:
        sys.stderr.write(f"UnknownRoleError: {err}\n")
        return 2
    except (EscalationRequiredError, InvalidEscalationReceiptError) as err:
        sys.stderr.write(f"EscalationError: {err}\n")
        return 3
    except Exception as err:
        sys.stderr.write(f"Error: {err}\n")
        return 1
