#!/usr/bin/env bash
# install mcp-guardian pre-commit hook (with whitelist for self-referential files)

cat > .git/hooks/pre-commit << 'HOOK'
#!/usr/bin/env bash
# mcp-guardian pre-commit hook — blocks secrets, PII, and internal keywords.
# Self-referential files (patterns.py, server.py) are whitelisted.

set -e

STAGED=$(git diff --cached --name-only --diff-filter=ACM)
if [ -z "$STAGED" ]; then
  exit 0
fi

# Allowlist: self-referential files that ship the pattern rules
WHITELIST="src/mcp_guardian/patterns.py|src/mcp_guardian/server.py|scripts/|tests/fixtures/"

# Patterns: label:regex
declare -a RULES=(
  "PII:ezedi"
  "PII:hermes"
  "PII:playmcp"
  "PII:sanghak"
  "PII:상학"
  "PII:에이전틱"
  "PII:공모전"
  "PII:nerin81@gmail"
  "GH_PAT:ghp_[A-Za-z0-9]{20,}"
  "GH_PAT:gho_[A-Za-z0-9]{20,}"
  "GH_PAT:ghu_[A-Za-z0-9]{20,}"
  "GH_PAT:github_pat_[A-Za-z0-9_]{20,}"
  "PROVIDER:sk-[A-Za-z0-9]{20,}"
  "PROVIDER:sk-ant-[A-Za-z0-9-]{20,}"
  "PROVIDER:xox[baprs]-[A-Za-z0-9-]{10,}"
  "PROVIDER:AIza[A-Za-z0-9_-]{35}"
  "PROVIDER:AKIA[0-9A-Z]{16}"
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
HOOK

chmod +x .git/hooks/pre-commit
echo "✅ mcp-guardian pre-commit hook installed (with whitelist)"