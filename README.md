# Replaid for Hermes

Read social inbox conversations, prepare replies, and save drafts from Hermes through Replaid. Connect your Replaid account with browser-based OAuth.

This plugin is maintained independently by Replaid. It is not maintained or endorsed by Nous Research, and is not yet listed in the Hermes plugin catalog.

## Install

You need Hermes Agent, a Replaid account, and a connected channel. Use the **same profile** in the terminal and Hermes Desktop.

For the default profile:

```bash
hermes --profile default plugins install replaid-pro/replaid-hermes --no-enable
hermes --profile default plugins enable replaid
hermes --profile default replaid setup
```

If Hermes asks whether the plugin can replace built-in tools, answer **no**. Replaid does not need that permission.

Complete sign-in in your browser. Setup is complete when the terminal confirms that Replaid is connected and inbox tools are available. Start a **new conversation** in that profile.

For a named profile, replace `default` in all three commands with its name. Create the profile in Hermes first. Profiles have separate plugins, connections, and OAuth tokens.

## Use

Ask in normal language:

- “Show messages in Replaid that need a reply.”
- “Suggest a reply to this conversation. Do not send it.”
- “Save this reply as a draft in Replaid.”
- “Show my connected Replaid channels.”

Use conversation IDs returned by Replaid when selecting a specific conversation. Mention Replaid when other inbox integrations are installed. Sending and other changes require a user request and must pass Replaid's server-side policies. Skill instructions guide the agent; they are not a permission enforcement system.

## Check setup

```bash
hermes --profile default replaid status
hermes --profile default replaid check
```

`status` checks saved settings without connecting. `check` verifies the connection and the required inbox tools. `setup` saves a missing connection **before** OAuth, so interrupted sign-in does not leave a token without a server entry. Rerun setup after an interrupted sign-in.

Setup preserves existing settings. It stops if `replaid` names another endpoint, is disabled, uses custom authentication headers, or excludes the required inbox tools. Review those settings in Hermes rather than overwriting them. If the existing connection has expired credentials, use `hermes --profile default mcp login replaid`, then run the check again.

An enabled plugin and a saved OAuth token do not by themselves prove that a connection exists. If a chat searches files or other services instead of Replaid, check the selected profile and start a new conversation after setup.

## What is installed

- A `hermes replaid setup|status|check` command.
- A read-only `replaid_connection_status` tool, which checks local settings.
- Three skills: social inbox, channel management, and team/webhooks.
- An OAuth MCP connection to `https://mcp.replaid.pro`, created only when setup is explicitly run.

Registration does not connect or change settings. Setup does not send messages or create drafts. The remote MCP server provides the Replaid tools; this repository contains no Replaid backend implementation, credentials, or customer data. Hermes stores OAuth tokens in the selected profile, outside the plugin folder. Removing the plugin does not revoke OAuth or remove the separately configured MCP connection.

## Compatibility and tests

Validated locally on macOS with Hermes 0.21.3. Setup currently uses Hermes MCP configuration and connection helpers that are internal APIs; compatibility is tested against the exact Hermes revision in CI. Other Hermes versions and Windows are not yet verified.

Use the Python environment from your Hermes installation:

```bash
python -m unittest discover -s tests -v
hermes plugins doctor . --ci
hermes plugins validate . --json
```

The tests use temporary profiles and mock network responses. They do not require credentials or make customer changes. A live browser sign-in and a saved draft require a separate authorized acceptance test. CI does not prove live OAuth or message delivery.

## License

MIT. See [LICENSE](LICENSE).
