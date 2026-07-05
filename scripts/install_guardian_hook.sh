#!/usr/bin/env bash
# Install mcp-guardian pre-commit hook
# Usage: ./scripts/install_guardian_hook.sh [repo_path]

REPO_PATH="${1:-.}"
HOOK_PATH="$REPO_PATH/.git/hooks/pre-commit"

if [ ! -d "$REPO_PATH/.git" ]; then
  echo "❌ Not a Git repository: $REPO_PATH"
  exit 1
fi

if [ -f "$HOOK_PATH" ]; then
  echo "⚠️  Pre-commit hook already exists at $HOOK_PATH"
  echo "   Remove it first or merge manually."
  exit 1
fi

cat > "$HOOK_PATH" << 'HOOK'
#!/usr/bin/env bash
# mcp-guardian pre-commit hook (example)
# Customize the RULES array with your own sensitive keywords.

set -e

STAGED=$(git diff --cached --name-only --diff-filter=ACM)
if [ -z "$STAGED" ]; then
  exit 0
fi

# Allowlist of self-referential files (the guardian ships its own rules)
WHITELIST="src/mcp_guardian/patterns.py|src/mcp_guardian/server.py|tests/fixtures/"

# Patterns: (label, regex)
# Customize these with your own sensitive keywords:
declare -a RULES=(
  "PII:YOUR_COMPANY"
  "PII:YOUR_NAME"
  "PII:YOUR_EMAIL"
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

chmod +x "$HOOK_PATH"
echo "✅ Pre-commit hook installed at $HOOK_PATH"
echo ""
echo "💡 Customize the RULES array with your own sensitive keywords."
