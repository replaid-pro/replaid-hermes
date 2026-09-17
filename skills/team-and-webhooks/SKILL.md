---
name: team-and-webhooks
description: Manage Replaid team names, member invitations, and outbound webhook subscriptions. Use for team administration or configuring event delivery to a receiver; not for connecting social accounts or sending conversation replies.
---

# Replaid Team and Webhook Management

Use the existing Hermes MCP connection named `replaid`. The plugin provides `hermes replaid setup` to save and verify an OAuth connection in the active profile. Discover the available tools from that connection; Hermes can prefix the tool names shown below. Keep all operations in the environment requested by the user. If the connection or tools are unavailable, call `replaid_connection_status` and show its setup instruction. Stop there; do not search the web, local source files, a Replaid CLI, or another inbox provider to replace the missing connection. If settings exist but tools are absent, ask the user to run `hermes replaid check` in this profile and start a new session. Never request tokens or passwords in chat. Do not switch to another connection without the user's instruction.

Use the dedicated Replaid MCP tools, not `execute_action`. Management writes require an OAuth owner or administrator and apply to the team bound to the grant. A different team selected in the web app does not change that scope.

## Teams and invitations

- Use `list_team_members` to inspect membership when relevant.
- Use `update_team` to apply the user's requested team name. The slug can change; report the returned name and slug. This tool does not switch teams or transfer ownership.
- Use `invite_team_member` only for email addresses the user explicitly asks to invite. Default to `member`; use `admin` only when the user requests administrator access.
- An invitation is pending until accepted. Report `notification_status` accurately: `queued` does not prove email delivery, and `not_resent` means the existing invitation was reused. Do not claim the recipient is already a member.
- Do not invent tools to remove members, change existing roles, or transfer ownership.

## Outbound webhooks

1. Use `list_webhooks` to inspect existing subscriptions and select a returned `webhook_id` for changes.
2. Use `create_webhook` for a user-requested public HTTPS receiver and selected events. It is active by default: future matching events can send team data to that destination. Do not infer a destination or broaden the event selection.
3. Use `update_webhook` to change a subscription. Omitted fields are preserved; `events` replaces the whole selection. To disable delivery, set `is_active` to false.
4. A URL change blocks pending deliveries to the old destination; it does not redirect or replay those events. Disabling a subscription or removing an event also blocks the affected pending deliveries. An update cannot recall a request already in flight.
5. A signing secret is returned only when a subscription is first created. Store it securely in the intended receiver when that setup is authorized. Do not put it in a URL or repeat it in summaries. Repeated creation of the same subscription does not recover its secret.

Creating a subscription does not configure or test the receiver. Report the saved URL, events, and active state separately from any delivery evidence. For uncertain write results, inspect existing subscriptions before retrying to avoid duplicates.

Channel approval links and disconnections belong to `channel-management`. Conversation replies and action execution belong to `social-inbox`. If a required tool is unavailable or access is denied, report the limit without substituting unrelated tools.

In Hermes, use `skills_list` to find sibling skills in this plugin and `skill_view` to read their full namespaced names.
