"""Profile-scoped Replaid setup. OAuth and config persistence belong to Hermes."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

SERVER = "replaid"
ENDPOINT = "https://mcp.replaid.pro"
REQUIRED_TOOLS = {"list_conversations", "get_conversation_context"}


class SetupError(Exception):
    """A connection is not ready for inbox use."""


class HermesHost:
    """Isolate Hermes integration points so host changes fail explicitly."""

    def __init__(self):
        from hermes_cli import mcp_config
        from hermes_constants import get_hermes_home

        self.api = mcp_config
        self.home = get_hermes_home()

    def read(self):
        return self.api._get_mcp_servers().get(SERVER)

    def runtime(self):
        from tools.mcp_tool_discovery import get_mcp_status

        entries = get_mcp_status()
        entry = next((item for item in entries if item.get("name") == SERVER), {})
        return {"status": entry.get("status", "unavailable"), "tools": entry.get("tools", 0)}

    def save(self, config):
        if not self.api._save_mcp_server(SERVER, config):
            raise SetupError("Hermes did not save the Replaid connection.")

    def probe(self, config, interactive=False):
        if interactive:
            from tools.mcp_oauth import force_interactive_oauth

            with force_interactive_oauth():
                return self.api._probe_single_server(SERVER, config, connect_timeout=315)
        return self.api._probe_single_server(SERVER, config, connect_timeout=30)


def profile_name(home):
    home = Path(home)
    return home.name if home.parent.name == "profiles" else "default"


def setup_command(home):
    # Pin the exact home; a command pasted into another terminal must not switch profiles.
    return f"HERMES_HOME={shlex.quote(str(home))} hermes replaid setup"


def validate_config(config):
    if not isinstance(config, dict):
        raise SetupError("The Replaid connection is not configured in this profile.")
    if config.get("url", "").rstrip("/") != ENDPOINT or config.get("auth") != "oauth":
        raise SetupError("The name replaid is used by another connection. It was not changed.")
    if config.get("command") or config.get("headers"):
        raise SetupError("The existing Replaid connection has custom settings. It was not changed.")
    if config.get("enabled", True) in (False, "false", "False", 0):
        raise SetupError("The Replaid connection is disabled in this profile.")
    filters = config.get("tools") or {}
    include = filters.get("include")
    exclude = filters.get("exclude") or []
    if (isinstance(include, list) and not REQUIRED_TOOLS.issubset(include)) or REQUIRED_TOOLS.intersection(exclude):
        raise SetupError("The current tool selection blocks inbox reading. Enable list_conversations and get_conversation_context in Hermes MCP settings.")


def status(host):
    try:
        validate_config(host.read())
    except SetupError as exc:
        return {"configured": False, "profile": profile_name(host.home), "message": str(exc), "setup_command": setup_command(host.home)}
    return {"configured": True, "profile": profile_name(host.home), "message": "Connection settings are saved. This does not verify OAuth or network access."}


def check(host, interactive=False):
    config = host.read()
    validate_config(config)
    try:
        tools = host.probe(config, interactive=interactive)
    except Exception as exc:
        # Do not echo host exceptions: they may contain OAuth URLs or credentials.
        raise SetupError("Replaid could not connect. Check network access and complete browser sign-in. The saved settings were kept.") from exc
    names = {name for name, _description in tools}
    if not REQUIRED_TOOLS.issubset(names):
        raise SetupError("Replaid connected, but the required inbox tools are unavailable.")
    return len(names)


def setup(host):
    existing = host.read()
    if existing is None:
        host.save({"url": ENDPOINT, "auth": "oauth", "enabled": True})
    else:
        validate_config(existing)
    # Read from disk before connecting. A token alone must never count as completed setup.
    validate_config(host.read())
    return check(host, interactive=True)


def runtime_status(host):
    result = status(host)
    result["skills"] = ["replaid:social-inbox", "replaid:channel-management", "replaid:team-and-webhooks"]
    result["runtime_tools_available"] = False
    if not result["configured"]:
        return result
    try:
        runtime = host.runtime()
        count = int(runtime.get("tools", 0))
        result["runtime_tools_available"] = runtime.get("status") in {"connected", "lazy"} and count > 0
        result["runtime_tool_count"] = count
    except Exception:
        result["runtime_tool_count"] = 0
    if result["runtime_tools_available"]:
        result["next_step"] = "Load replaid:social-inbox and search for the Replaid MCP tools. If tool_search cannot find them in this chat, start a new session in the same profile."
    else:
        result["next_step"] = "Settings are saved, but Replaid tools are not available in this runtime. Restart the Hermes backend for this profile, then start a new session. If tools are still absent, run hermes replaid check in the same profile. Do not write scripts or access OAuth files to replace missing tools."
    return result


def connection_status(args, **kwargs):
    try:
        result = runtime_status(HermesHost())
    except Exception:
        result = {"configured": False, "runtime_tools_available": False, "message": "Replaid setup could not be checked. Run hermes replaid status in the same profile."}
    return json.dumps(result)


def configure_parser(parser):
    parser.add_argument("operation", choices=["setup", "status", "check"], nargs="?", default="status")


def run_command(args):
    try:
        host = HermesHost()
        print(f"Replaid — profile: {profile_name(host.home)}")
        if args.operation == "status":
            result = status(host)
            print(result["message"])
            if not result["configured"]:
                print(result["setup_command"])
                raise SystemExit(1)
            return
        if args.operation == "setup":
            print("Connecting Replaid. Complete sign-in in your browser if requested.")
            count = setup(host)
        else:
            count = check(host)
        print(f"Connected. {count} Replaid tools found; inbox tools are available.")
        if args.operation == "setup":
            print('Start a new session in this profile and ask: "Show messages in Replaid that need a reply."')
    except SetupError as exc:
        print(str(exc))
        raise SystemExit(1) from None
    except (ImportError, AttributeError):
        print("This Hermes version does not support Replaid setup. Update Hermes and try again.")
        raise SystemExit(1) from None
