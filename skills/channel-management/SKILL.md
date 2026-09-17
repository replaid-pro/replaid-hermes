---
name: channel-management
description: List, connect, check, and disconnect Replaid social channels. Use for account connection status, Instagram or Messenger approval links, and Instagram, Messenger, Telegram, or WhatsApp disconnection; not for replying to conversations.
---

# Replaid Channel Management

Use the existing Hermes MCP connection named `replaid`. The plugin provides `hermes replaid setup` to save and verify an OAuth connection in the active profile. Discover the available tools from that connection; Hermes can prefix the tool names shown below. Keep all operations in the environment requested by the user. If the connection or tools are unavailable, call `replaid_connection_status` and show its setup instruction. Stop there; do not search the web, local source files, a Replaid CLI, or another inbox provider to replace the missing connection. If settings exist but tools are absent, ask the user to run `hermes replaid check` in this profile and start a new session. Never request tokens or passwords in chat. Do not switch to another connection without the user's instruction.

Use Replaid MCP tools for channel data and changes. Management tools require an owner or administrator connected through OAuth. Work with the team bound to that OAuth grant; changing the selected team in the web app does not change this grant.

## Inspect and connect

- Use `list_channels` to identify the provider, account, and current status. Use returned identities to resolve a named account; clarify if the requested account does not match.
- For an Instagram or Messenger connection request, call `create_channel_connection` with the requested provider. Return its approval URL so the user can authorize access in their browser. Never request passwords, access tokens, or bot tokens in chat.
- After browser approval, call `get_channel_connection` with the returned `connection_request_id`. Distinguish the link's `status` from `channel_status`: a created link is not a connected account, and an expired link does not mean an account was disconnected.
- Connection status does not prove message delivery. Do not claim delivery was tested unless a tool result provides that evidence.
- The current MCP connection tool supports Instagram and Messenger. Do not invent a Telegram or widget connection tool.

## Disconnect

Use `disconnect_channel` only when the user asks to disconnect. First identify the active account with `list_channels`, then pass its provider: `instagram`, `messenger`, `telegram`, or `whatsapp`.

The tool disconnects the active account for that provider in the OAuth-bound team, clears saved credentials, and retains conversation history. Instagram and Messenger pending connection links are also cancelled. It does not delete the provider account.

Report `disconnected` only after a successful result. On failure, report the returned error and do not claim the account was disconnected. If the outcome is uncertain, check `list_channels` before retrying.

## Tool boundaries

These changes use dedicated channel tools, not `execute_action`. If a tool is unavailable or access is denied, report that limit without trying another team's credentials or a conversation action. Inbox reading and replies belong to `social-inbox`.

For results, identify the provider and account when available, the confirmed status, and any browser approval still required.

In Hermes, use `skills_list` to find sibling skills in this plugin and `skill_view` to read their full namespaced names.
