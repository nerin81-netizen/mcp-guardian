"""Pattern definitions for mcp-guardian.

This module is intentionally exempt from self-scanning (whitelisted in
server.GUARDIAN_WHITELIST) so the guardian can ship its own rule set
without triggering itself.
"""

# Keep this file in sync with HOOK_SCRIPT in server.py.
PII_KEYWORDS = (
    "ezedi",
    "hermes",
    "playmcp",
    "에이전틱",
    "공모전",
    "sanghak",
    "상학",
    "nerin81@gmail",
)

GITHUB_PAT_PATTERNS = (
    r"ghp_[A-Za-z0-9]{20,}",
    r"gho_[A-Za-z0-9]{20,}",
    r"ghu_[A-Za-z0-9]{20,}",
    r"ghs_[A-Za-z0-9]{20,}",
    r"ghr_[A-Za-z0-9]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
)

PROVIDER_KEY_PATTERNS = (
    r"sk-[A-Za-z0-9]{20,}",
    r"sk-ant-[A-Za-z0-9\-]{20,}",
    r"xox[baprs]-[A-Za-z0-9\-]{10,}",
    r"AIza[A-Za-z0-9_\-]{35}",
    r"AKIA[0-9A-Z]{16}",
)
