"""Replaid native Hermes plugin. Registration does not change settings or connect."""

from pathlib import Path

from .connection import configure_parser, connection_status, run_command
from .guidance import guide_replaid_request


def register(ctx):
    ctx.register_hook("pre_llm_call", guide_replaid_request)
    for skill in sorted((Path(__file__).parent / "skills").glob("*/SKILL.md")):
        ctx.register_skill(skill.parent.name, skill)
    ctx.register_cli_command(
        name="replaid", help="Set up and check Replaid in this Hermes profile",
        setup_fn=configure_parser, handler_fn=run_command,
    )
    ctx.register_tool(
        name="replaid_connection_status", toolset="replaid-setup",
        schema={"name": "replaid_connection_status", "description": "Check Replaid connection settings and runtime tool availability. For inbox tasks load skill_view with replaid:social-inbox, not social-inbox. Use this check if Replaid MCP tools are missing; it returns recovery steps. Do not use scripts to replace missing inbox tools. Does not connect or change settings.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}},
        handler=connection_status,
    )
