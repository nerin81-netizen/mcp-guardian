"""mcp-guardian — Privacy Firewall for AI-Powered Development.

An MCP server that prevents AI agents from accidentally pushing
secrets, PII, and internal keywords to GitHub. Operates at multiple
checkpoints: file edit, pre-commit, pre-push, and remote URL inspection.

Recursive safety: any path matching GUARDIAN_WHITELIST is exempt from
self-scanning, so the server can ship its own pattern rules.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SERVER_NAME = "mcp-guardian"
SERVER_VERSION = "0.1.0"

# Paths exempt from pattern scanning. The guardian must be able to ship
# its own rule definitions without triggering itself.
GUARDIAN_WHITELIST = (
    "src/mcp_guardian/patterns.py",
    "src/mcp_guardian/server.py",  # server itself declares the rules
    "tests/fixtures/",
)

# Sensitive patterns. Mirrors the rules shipped by the mcp-publish skill.
PATTERNS: dict[str, list[tuple[str, str]]] = {
    "PII / user-identifying keywords": [
        (r"\bacme\b", "company name (example)"),
        (r"\binternal-tool\b", "internal project name (example)"),
        (r"\bspecific-platform\b", "platform-specific term (example)"),
        (r"\b특정플랫폼\b", "platform-specific term (Korean, example)"),
        (r"\b특정행사\b", "event-specific term (Korean, example)"),
        (r"\bjohndoe\b", "personal name (example)"),
        (r"\b홍길동\b", "personal name (Korean, example)"),
        (r"user@example\.com", "personal email address (example)"),
    ],
    "GitHub Personal Access Tokens": [
        (r"ghp_[A-Za-z0-9]{20,}", "GitHub PAT (OAuth user)"),
        (r"gho_[A-Za-z0-9]{20,}", "GitHub PAT (OAuth)"),
        (r"ghu_[A-Za-z0-9]{20,}", "GitHub PAT (user-to-server)"),
        (r"ghs_[A-Za-z0-9]{20,}", "GitHub PAT (server-to-server)"),
        (r"ghr_[A-Za-z0-9]{20,}", "GitHub PAT (refresh)"),
        (r"github_pat_[A-Za-z0-9_]{20,}", "GitHub fine-grained PAT"),
    ],
    "Provider API keys": [
        (r"sk-[A-Za-z0-9]{20,}", "OpenAI / Anthropic style key"),
        (r"sk-ant-[A-Za-z0-9\-]{20,}", "Anthropic specific prefix"),
        (r"xox[baprs]-[A-Za-z0-9\-]{10,}", "Slack token"),
        (r"AIza[A-Za-z0-9_\-]{35}", "Google API key"),
        (r"AKIA[0-9A-Z]{16}", "AWS access key ID"),
    ],
    "Generic secret assignments": [
        (r"(?i)(api[_-]?key|secret|token|password)\s*[=:]\s*[\"'][A-Za-z0-9_\-]{16,}[\"']",
         "hard-coded credential assignment"),
    ],
    "Email addresses": [
        (r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
         "email address (noreply@github.com is whitelisted by callers)"),
    ],
}

# Email allowlist applied by check_files / check_commit
EMAIL_ALLOWLIST = ("noreply@github.com", "actions@github.com")


# ---------------------------------------------------------------------------
# Core scanning logic (pure functions, easy to unit-test)
# ---------------------------------------------------------------------------

def _is_exempt(path: str) -> bool:
    """Return True if path matches the recursive-safe whitelist."""
    normalized = path.replace("\\", "/")
    return any(wl in normalized for wl in GUARDIAN_WHITELIST)


def _redact_email(match: re.Match[str]) -> str:
    email = match.group(0)
    if email.lower() in EMAIL_ALLOWLIST:
        return email
    return "[REDACTED_EMAIL]"


def _scan_text(text: str, source_label: str) -> list[dict[str, Any]]:
    """Scan a string for all sensitive patterns. Returns findings list."""
    findings: list[dict[str, Any]] = []

    # Email addresses get special handling so that noreply@github.com passes
    text_with_redacted_emails = re.sub(
        r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
        _redact_email,
        text,
    )

    for category, rules in PATTERNS.items():
        if category == "Email addresses":
            # Compare against redacted text so allowlisted emails pass
            scan_target = text
            target_for_match = text_with_redacted_emails
        else:
            scan_target = text
            target_for_match = text

        for pattern, description in rules:
            for match in re.finditer(pattern, target_for_match, flags=re.IGNORECASE):
                # For email category, only report non-allowlisted matches
                if category == "Email addresses":
                    if match.group(0).lower() in EMAIL_ALLOWLIST:
                        continue
                findings.append({
                    "source": source_label,
                    "category": category,
                    "rule": description,
                    "pattern": pattern,
                    "match": match.group(0)[:8] + "…" if len(match.group(0)) > 8 else match.group(0),
                    "position": match.start(),
                })

    return findings


def scan_paths(
    paths: list[str],
    root: str | None = None,
    recursive: bool = True,
) -> dict[str, Any]:
    """Scan a list of file or directory paths. Returns structured result."""
    root = root or os.getcwd()
    all_findings: list[dict[str, Any]] = []
    files_scanned = 0
    files_skipped: list[str] = []

    for raw in paths:
        p = Path(raw)
        if not p.is_absolute():
            p = Path(root) / p

        if p.is_file():
            targets = [p]
        elif p.is_dir():
            if recursive:
                targets = [f for f in p.rglob("*") if f.is_file()]
            else:
                targets = [f for f in p.iterdir() if f.is_file()]
        else:
            files_skipped.append(str(p))
            continue

        for f in targets:
            rel = str(f.relative_to(Path(root))) if f.is_relative_to(Path(root)) else str(f)
            if _is_exempt(rel):
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                files_skipped.append(rel)
                continue
            files_scanned += 1
            all_findings.extend(_scan_text(content, rel))

    return {
        "verdict": "BLOCK" if all_findings else "PASS",
        "files_scanned": files_scanned,
        "files_skipped": files_skipped,
        "findings_count": len(all_findings),
        "findings": all_findings,
    }


def scan_staged(root: str | None = None) -> dict[str, Any]:
    """Scan all files currently staged for commit."""
    root = root or os.getcwd()
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return {"verdict": "ERROR", "error": f"git diff failed: {exc}"}

    staged_files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not staged_files:
        return {
            "verdict": "PASS",
            "files_scanned": 0,
            "files_skipped": [],
            "findings_count": 0,
            "findings": [],
            "note": "no staged files",
        }

    return scan_paths(staged_files, root=root, recursive=False)


def scan_history(root: str | None = None, max_commits: int = 50) -> dict[str, Any]:
    """Scan the last N commits' diffs for any sensitive content."""
    root = root or os.getcwd()
    try:
        log_result = subprocess.run(
            ["git", "log", f"-{max_commits}", "--pretty=format:%H"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return {"verdict": "ERROR", "error": f"git log failed: {exc}"}

    commits = [c for c in log_result.stdout.splitlines() if c]
    all_findings: list[dict[str, Any]] = []
    scanned = 0

    for commit in commits:
        diff_result = subprocess.run(
            ["git", "show", commit, "--pretty=", "-z"],
            cwd=root,
            capture_output=True,
            text=True,
            errors="ignore",
        )
        scanned += 1
        all_findings.extend(_scan_text(diff_result.stdout, f"commit:{commit[:7]}"))

    return {
        "verdict": "BLOCK" if all_findings else "PASS",
        "commits_scanned": scanned,
        "findings_count": len(all_findings),
        "findings": all_findings,
    }


def check_remote_url(root: str | None = None) -> dict[str, Any]:
    """Verify the current remote URL does not contain a PAT."""
    root = root or os.getcwd()
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return {"verdict": "ERROR", "error": f"not a git repo or no origin: {exc}"}

    url = result.stdout.strip()
    # Strip credentials portion for display
    display_url = re.sub(r"https://[^@]+@", "https://[REDACTED]@", url)

    # Detect PAT-shaped credentials embedded in the URL
    findings = _scan_text(url, "remote_url")

    return {
        "verdict": "BLOCK" if findings else "PASS",
        "url": display_url,
        "findings_count": len(findings),
        "findings": findings,
    }


def install_pre_commit_hook(
    root: str | None = None,
    hook_source: str | None = None,
) -> dict[str, Any]:
    """Install a pre-commit hook that calls check_commit on every commit.

    The hook is a self-contained bash script that calls back into the
    `mcp-guardian check-commit` command (if installed) or, as a fallback,
    embeds a minimal pattern check directly.
    """
    root = root or os.getcwd()
    git_dir = Path(root) / ".git"
    if not git_dir.exists():
        return {"verdict": "ERROR", "error": "not a git repository"}

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_path = hooks_dir / "pre-commit"

    if hook_source:
        try:
            hook_body = Path(hook_source).read_text(encoding="utf-8")
        except OSError as exc:
            return {"verdict": "ERROR", "error": f"cannot read hook source: {exc}"}
    else:
        # 동적으로 RULES 배열을 생성하여 템플릿에 주입
        rules_lines = []
        for category, rules in PATTERNS.items():
            label = category.split(" ")[0].split("/")[0].upper()
            for pattern, _ in rules:
                rules_lines.append(f'  "{label}:{pattern}"')
        rules_str = "\n".join(rules_lines)
        hook_body = HOOK_SCRIPT_TEMPLATE.replace("##RULES_PLACEHOLDER##", rules_str)

    # Windows에서 Git Bash가 \r (CR) 문자로 인해 구문 오류를 내지 않도록 LF(\n)로 강제 지정하여 저장합니다.
    try:
        with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(hook_body)
    except OSError as exc:
        return {"verdict": "ERROR", "error": f"failed to write hook file: {exc}"}

    # Windows 환경 등 OS 종류에 따라 chmod 실패 예외가 발생할 수 있으므로 예외 처리를 감싸줍니다.
    try:
        hook_path.chmod(0o755)
    except OSError:
        pass

    return {
        "verdict": "PASS",
        "hook_path": str(hook_path),
        "executable": True,
        "size_bytes": hook_path.stat().st_size,
    }


# Self-contained hook script template. Dynamically populated with patterns at install time.
HOOK_SCRIPT_TEMPLATE = r"""#!/usr/bin/env bash
# mcp-guardian pre-commit hook — generated by `mcp-guardian install-hook`
# Dynamically compiled from src/mcp_guardian/patterns.py.

set -e

STAGED=$(git diff --cached --name-only --diff-filter=ACM)
if [ -z "$STAGED" ]; then
  exit 0
fi

# Allowlist of self-referential files (the guardian ships its own rules)
WHITELIST="src/mcp_guardian/patterns.py|src/mcp_guardian/server.py|tests/fixtures/"

# Patterns: (label, regex) — dynamically injected
declare -a RULES=(
##RULES_PLACEHOLDER##
)

FOUND=0
for FILE in $STAGED; do
  if [[ "$FILE" =~ $WHITELIST ]]; then
    continue
  fi
  if [ ! -f "$FILE" ]; then
    continue
  fi
  for RULE in "${RULES[@]}"; do
    LABEL="${RULE%%:*}"
    PATTERN="${RULE##*:}"
    if grep -EHn -- "$PATTERN" "$FILE" >/dev/null 2>&1; then
      echo "✘ mcp-guardian BLOCKED: $FILE matches $LABEL rule ($PATTERN)"
      grep -EHn -- "$PATTERN" "$FILE" | head -3 | sed 's/^/    /'
      FOUND=1
    fi
  done
done

if [ "$FOUND" -eq 1 ]; then
  echo ""
  echo "Commit blocked by mcp-guardian pre-commit hook."
  echo "Remove the sensitive content, then retry the commit."
  echo "To bypass (NOT recommended): git commit --no-verify"
  exit 1
fi

exit 0
"""


# ---------------------------------------------------------------------------
# MCP server registration
# ---------------------------------------------------------------------------

mcp = FastMCP(SERVER_NAME)


@mcp.tool(
    annotations={
        "title": "Scan Workspace Files",
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
        "idempotentHint": True,
    }
)
def check_files(
    paths: list[str],
    root: str | None = None,
    recursive: bool = True,
) -> dict[str, Any]:
    """Scan files or directories for secrets, PII, and sensitive patterns from mcp-guardian(엠씨피가디언).

    Args:
        paths: List of file or directory paths (absolute or relative to root).
        root: Working directory for resolving relative paths. Defaults to CWD.
        recursive: If True, descend into directories.

    Returns:
        Dict with verdict (PASS/BLOCK), files_scanned, findings_count, findings.
    """
    return scan_paths(paths, root=root, recursive=recursive)


@mcp.tool(
    annotations={
        "title": "Scan Staged Git Files",
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
        "idempotentHint": True,
    }
)
def check_commit(root: str | None = None) -> dict[str, Any]:
    """Scan all files currently staged in the local git repository from mcp-guardian(엠씨피가디언).

    Mirrors the pre-commit hook behavior. Use before running `git commit`
    to get a structured result you can react to.

    Args:
        root: Path to the git repository. Defaults to CWD.

    Returns:
        Dict with verdict, files_scanned, findings_count, findings.
    """
    return scan_staged(root=root)


@mcp.tool(
    annotations={
        "title": "Scan Git Commit History",
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
        "idempotentHint": True,
    }
)
def sanitize_history(root: str | None = None, max_commits: int = 50) -> dict[str, Any]:
    """Scan the last N commits for sensitive content that may have leaked from mcp-guardian(엠씨피가디언).

    Use this after a suspected exposure to identify which commits contain
    secrets. The tool does not rewrite history — that is a separate manual
    step (`git filter-repo`).

    Args:
        root: Path to the git repository. Defaults to CWD.
        max_commits: How many recent commits to scan (default: 50).

    Returns:
        Dict with verdict, commits_scanned, findings_count, findings.
    """
    return scan_history(root=root, max_commits=max_commits)


@mcp.tool(
    annotations={
        "title": "Check Git Remote URL Credentials",
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
        "idempotentHint": True,
    }
)
def check_remote_url_tool(root: str | None = None) -> dict[str, Any]:
    """Verify the git origin URL does not embed a PAT in the credentials slot from mcp-guardian(엠씨피가디언).

    Returns:
        Dict with verdict, url (credentials redacted), findings_count, findings.
    """
    return check_remote_url(root=root)


@mcp.tool(
    annotations={
        "title": "Install Git Pre-Commit Hook",
        "readOnlyHint": False,
        "destructiveHint": False,
        "openWorldHint": False,
        "idempotentHint": False,
    }
)
def install_hook(
    root: str | None = None,
    hook_source: str | None = None,
) -> dict[str, Any]:
    """Install a pre-commit hook that blocks sensitive content at commit time from mcp-guardian(엠씨피가디언).

    The hook runs the same pattern rules as the MCP tools. Once installed,
    `git commit` itself will refuse to create a commit that contains
    secrets, PII keywords, or other sensitive patterns.

    Args:
        root: Path to the git repository. Defaults to CWD.
        hook_source: Optional path to a custom hook script. If omitted,
            the bundled self-contained hook is installed.

    Returns:
        Dict with verdict, hook_path, executable, size_bytes.
    """
    return install_pre_commit_hook(root=root, hook_source=hook_source)


@mcp.resource("config://rules")
def get_rules() -> str:
    """The current pattern ruleset used by all check tools.

    Returns the full rule set as a JSON document so other agents and
    auditors can inspect what mcp-guardian is actively scanning for.
    """
    payload = {
        "version": SERVER_VERSION,
        "whitelist": list(GUARDIAN_WHITELIST),
        "email_allowlist": list(EMAIL_ALLOWLIST),
        "categories": {
            category: [{"description": desc, "pattern": pat} for pat, desc in rules]
            for category, rules in PATTERNS.items()
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def main() -> None:
    import sys
    import os
    if len(sys.argv) > 1 and sys.argv[1] == "sse":
        import uvicorn
        from starlette.applications import Starlette
        from starlette.routing import Mount
        port = int(os.getenv("PORT", 8000))
        sse_app = mcp.sse_app()
        app = Starlette(routes=[
            Mount("/mcp", app=sse_app),
            Mount("/", app=sse_app)
        ])
        print(f"Starting mcp-guardian SSE Server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        mcp.run()

if __name__ == "__main__":
    main()
