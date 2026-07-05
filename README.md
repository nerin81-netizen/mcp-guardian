# mcp-guardian

[English](./README.md) | [한국어](./README.ko.md) | [中文](./README.zh.md) | [日本語](./README.ja.md)

---

Privacy firewall for AI-powered development. Stops secrets, PII, and
internal keywords from ever reaching GitHub when an AI agent commits code.

## ✨ What this is

**AI가 코드를 작성합니다.** 그리고 실수를 합니다. 민감한 정보를 커밋에 넣거나, 토큰을 원격 URL에 노출하거나, 개인 정보를 README에 적는 실수 말이죠.

한 번 GitHub에 올라가면 **되돌릴 수 없습니다.** fork되고, 캐시되고, 영구적으로 남아요.

`mcp-guardian`는 **4단계 방어선**입니다:

```bash
# ❌ Before: AI가 실수할 때까지 기다림
AI가 API 키를 하드코딩 → push → 발견 → panic → 히스토리 정리 → 토큰 revoke

# ✅ After: 사전 차단
AI가 API 키를 하드코딩 → check_files가 즉시 차단 → 커밋 안 됨 → 사고 없음
```

**실제 동작 방식:**

```text
AI: "이 파일 저장할게요"
→ check_files("src/config.py")
→ 🔍 스캔 중...
→ ❌ 발견: OpenAI API 키 패턴 (line 12)
→ 차단: 커밋이 진행되지 않음

AI: "아, 감사합니다. 수정할게요."
```

## 🎯 When to use it

**Scenario 1: AI가 민감한 정보를 포함하는 파일을 작성할 때**

```text
AI: "이 설정 파일을 저장할게요"
→ check_files("config.py")

결과:
🔍 스캔 결과 — 2개 파일, 1개 문제

❌ config.py
   Line 12: OPENAI_API_KEY = "sk-proj-abc123..."
   → 감지됨: OpenAI API 키 패턴
   → 차단됨

✅ 수정 후:
   OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
   → ✅ 통과
```

**Scenario 2: 커밋 전에 전체 변경사항 검사**

```bash
# Staged 파일들을 자동으로 검사
git add .
→ check_commit()

결과:
🔍 커밋 전 검사 — 5개 파일

❌ README.md
   Line 45: export GH_TOKEN=ghp_abc123...
   → 감지됨: GitHub PAT 패턴
   → 커밋 차단됨

✅ 수정 후 다시 커밋:
   export GH_TOKEN=$GITHUB_TOKEN
   → ✅ 커밋 성공
```

**Scenario 3: 이미 push된 민감한 정보 추적**

```text
"아, 전에 토큰을 실수로 push한 것 같은데..."
→ sanitize_history()

결과:
🔍 히스토리 검사 — 47개 커밋

❌ 발견: 1개
   커밋: a1b2c3d (2주 전)
   파일: .env
   내용: OPENAI_API_KEY = "sk-..."
   → 이 커밋에서 최초 노출됨

조치:
   1. 토큰 즉시 revoke
   2. git filter-branch로 히스토리 정리
   3. force push (주의!)
```

**Scenario 4: 원격 URL에 토큰이 포함되었을 때**

```bash
git remote set-url origin https://ghp_abc123@github.com/user/repo.git
git push
→ check_remote_url()

결과:
❌ 원격 URL에 토큰 포함됨
   감지됨: GitHub PAT (ghp_...)
   자동 수정: 토큰 제거 후 push

✅ 수정된 URL:
   https://github.com/user/repo.git
```

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
