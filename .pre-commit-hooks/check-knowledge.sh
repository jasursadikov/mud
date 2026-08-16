#!/usr/bin/env bash
# Warns when src/mud/*.py files are staged but knowledge base files are not.
# Non-blocking — always exits 0.

YELLOW='\033[0;33m'
RESET='\033[0m'

staged=$(git diff --cached --name-only)

mud_changed=false
kb_changed=false

while IFS= read -r file; do
    case "$file" in
        src/mud/*.py) mud_changed=true ;;
        .github/copilot-instructions.md|AGENTS.md) kb_changed=true ;;
    esac
done <<< "$staged"

if $mud_changed && ! $kb_changed; then
    echo -e "${YELLOW}warning:${RESET} src/mud/ changed but knowledge base was not updated."
    echo "  If behaviour changed, update .github/copilot-instructions.md (and README.md tables if user-facing)."
fi

exit 0
