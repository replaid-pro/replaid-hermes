"""Expose qualified plugin skills when a user explicitly requests Replaid."""

import re

SKILLS = [
    "replaid:social-inbox",
    "replaid:channel-management",
    "replaid:team-and-webhooks",
]

GUIDANCE = (
    'Replaid plugin: for inbox requests load skill_view(name="replaid:social-inbox"). '
    'For channel management use "replaid:channel-management"; for team or webhook '
    'management use "replaid:team-and-webhooks". Bare skill names do not load these plugin skills. '
    'Use tool_search for the configured Replaid MCP tools, including '
    'mcp__replaid__list_conversations, mcp__replaid__get_conversation_context, and '
    'mcp__replaid__execute_action. For a saved draft, use execute_action with action=draft_reply; '
    'do not send it. If Replaid tools are unavailable, call replaid_connection_status and '
    'report its recovery steps. For inbox operations, do not replace missing tools with '
    'Python scripts, direct HTTP requests, local source-file searches, or another inbox provider. '
    'A successful terminal connection test does not add tools to the current chat. '
    'These instructions do not authorize sending or any other user-unrequested change.'
)


def guide_replaid_request(user_message="", **kwargs):
    if isinstance(user_message, str) and re.search(r"\breplaid\b", user_message, re.IGNORECASE):
        return {"context": GUIDANCE}
    return None
