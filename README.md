# mcp-guardian

[English](./README.md) | [한국어](./README.ko.md) | [中文](./README.zh.md) | [日本語](./README.ja.md)

---

Privacy firewall for AI-powered development. Stops secrets, PII, and
internal keywords from ever reaching GitHub when an AI agent commits code.

## What it does

`mcp-guardian` plugs into any MCP-compatible agent (Claude Code, Cursor,
Codex, etc.) and exposes five scanning tools plus a rule-resource:

| Tool | When to call it |
| --- | --- |
| `check_files` | Before saving a file that may contain sensitive data |
| `check_commit` | Before `git commit` — scans staged files |
| `sanitize_history` | After a suspected leak — finds the offending commit(s) |
| `check_remote_url` | Before `git push` — catches PATs in remote URLs |
| `install_hook` | One-time setup — installs a pre-commit hook so the OS enforces it |

Plus `config://rules`, a resource that returns the full active rule set
so auditors and other agents can introspect what is being blocked.

## Why it exists

AI agents write code faster than humans can review it. A single stray
credential or personal name in a README can become a permanent public
record the moment a commit lands on GitHub. `mcp-guardian` is the
defense layer that catches these mistakes at four checkpoints:

1. **Edit time** — `check_files` flags sensitive content before save.
2. **Commit time** — `check_commit` or the pre-commit hook blocks the
   commit entirely.
3. **Push time** — `check_remote_url` strips PATs that leaked into the
   remote URL.
4. **Audit time** — `sanitize_history` traces past leaks to their
   originating commit.

## Recursive safety

The server ships its own pattern rules in `src/mcp_guardian/patterns.py`.
That file is whitelisted (along with `server.py` and test fixtures) so
the guardian never blocks itself when it scans its own repository.

## Install

```bash
pip install mcp-guardian
```

Or from source:

```bash
git clone https://github.com/nerin81-netizen/mcp-guardian
cd mcp-guardian
pip install -e .
```

## Wire it up

In your MCP client config (e.g. Claude Code's `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "guardian": {
      "command": "python",
      "args": ["-m", "mcp_guardian.server"]
    }
  }
}
```

Then ask your agent:

> "Before you commit, run `check_commit` on this repo."

Or install the OS-level enforcement once and forget:

```bash
mcp-guardian install-hook
```

Now every `git commit` is guarded, even if the agent forgets to call the
tool.

## Rule categories

| Category | Examples caught |
| --- | --- |
| Personal identifiers | company / project / personal-name keywords |
| GitHub tokens | `ghp_…`, `gho_…`, `github_pat_…` |
| Provider keys | OpenAI, Anthropic, Slack, Google, AWS |
| Generic secrets | `api_key = "…"` style assignments |
| Email addresses | non-allowlisted addresses |

Inspect the live rules via the MCP resource:

```
resource: config://rules
```

## License

MIT — see [LICENSE](./LICENSE).
