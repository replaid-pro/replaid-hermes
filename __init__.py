"""Replaid native Hermes plugin. Registration does not change settings or connect."""

from pathlib import Path

from .connection import configure_parser, connection_status, run_command


def register(ctx):
    for skill in sorted((Path(__file__).parent / "skills").glob("*/SKILL.md")):
        ctx.register_skill(skill.parent.name, skill)
    ctx.register_cli_command(
        name="replaid", help="Set up and check Replaid in this Hermes profile",
        setup_fn=configure_parser, handler_fn=run_command,
    )
    ctx.register_tool(
        name="replaid_connection_status", toolset="replaid",
        schema={"name": "replaid_connection_status", "description": "Check whether Replaid is configured in the current Hermes profile. Use when Replaid inbox tools are missing. Returns setup guidance; does not connect, send messages, or change settings.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}},
        handler=connection_status,
    )
