# mcp-guardian

[English](./README.md) | [한국어](./README.ko.md) | [中文](./README.zh.md) | [日本語](./README.ja.md)

---

AI 기반 개발을 위한 프라이버시 방화벽. AI 에이전트가 코드를 커밋할 때
시크릿, 개인정보, 내부 키워드가 GitHub에 도달하지 않도록 차단합니다.

## 무엇을 하나요

`mcp-guardian`는 MCP 호환 에이전트(Claude Code, Cursor, Codex 등)에
연결되며, 다섯 가지 검사 도구와 룰 리소스를 제공합니다.

| 도구 | 호출 시점 |
| --- | --- |
| `check_files` | 민감한 데이터가 포함될 수 있는 파일 저장 전 |
| `check_commit` | `git commit` 전 — staged 파일 검사 |
| `sanitize_history` | 유출 의심 시 — 문제가 된 commit 추적 |
| `check_remote_url` | `git push` 전 — remote URL의 PAT 검사 |
| `install_hook` | 1회 설정 — pre-commit hook 설치로 OS 수준 강제 |

추가로 `config://rules` 리소스를 통해 현재 활성 룰셋을 조회할 수 있어,
감사자나 다른 에이전트가 차단 기준을 확인할 수 있습니다.

## 왜 만들었는가

AI 에이전트는 인간이 검토하는 것보다 훨씬 빠르게 코드를 작성합니다.
README에 실수로 포함된 한 줄의 자격증명이나 실명은 commit이 GitHub에
올라가는 순간 영구적인 공개 기록이 됩니다. `mcp-guardian`는 네 단계에서
이러한 실수를 잡아내는 방어층입니다.

1. **편집 시점** — `check_files`가 저장 전 민감 콘텐츠를 표시.
2. **커밋 시점** — `check_commit` 또는 pre-commit hook이 커밋 자체를 차단.
3. **푸시 시점** — `check_remote_url`이 remote URL에 새어든 PAT를 제거.
4. **감사 시점** — `sanitize_history`가 과거 유출의 원인이 된 commit을 추적.

## 재귀 안전성

이 서버는 자체 패턴 룰을 `src/mcp_guardian/patterns.py`에 동봉합니다.
해당 파일은(server.py 및 테스트 픽스처와 함께) 화이트리스트에 등록되어
있어, 가디언이 자신의 저장소를 검사할 때 스스로를 차단하지 않습니다.

## 설치

```bash
pip install mcp-guardian
```

또는 소스에서:

```bash
git clone https://github.com/nerin81-netizen/mcp-guardian
cd mcp-guardian
pip install -e .
```

## 연결 설정

MCP 클라이언트 설정 파일(예: Claude Code의 `claude_desktop_config.json`)에
추가:

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

그다음 에이전트에게 요청:

> "커밋하기 전에 이 저장소에서 `check_commit`을 실행해줘."

또는 1회성으로 OS 수준 강제를 설정:

```bash
mcp-guardian install-hook
```

이제 에이전트가 도구 호출을 잊더라도 모든 `git commit`이 보호됩니다.

## 룰 카테고리

| 카테고리 | 차단 예시 |
| --- | --- |
| 개인 식별자 | 회사 / 프로젝트 / 개인 이름 키워드 |
| GitHub 토큰 | `ghp_…`, `gho_…`, `github_pat_…` |
| 공급자 키 | OpenAI, Anthropic, Slack, Google, AWS |
| 일반 시크릿 | `api_key = "…"` 형식 할당 |
| 이메일 주소 | 허용 목록에 없는 주소 |

활성 룰은 MCP 리소스로 조회:

```
resource: config://rules
```

## 라이선스

MIT — [LICENSE](./LICENSE) 참고.
