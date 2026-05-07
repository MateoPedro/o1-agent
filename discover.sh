#!/usr/bin/env bash
# Run all discovery tasks manually.
# Usage:
#   ./discover.sh            — runs all 5 verticals
#   ./discover.sh speaking   — runs one vertical
#   ./discover.sh judging publishing

set -e

BACKEND_DIR="$(cd "$(dirname "$0")/apps/backend" && pwd)"
PYTHON="$BACKEND_DIR/.venv/bin/python"

if [ ! -f "$PYTHON" ]; then
  echo "Error: venv not found at $BACKEND_DIR/.venv"
  echo "Run: cd apps/backend && python -m venv .venv && pip install -r requirements.txt"
  exit 1
fi

cd "$BACKEND_DIR"

ALL_TASKS=(speaking judging publishing media memberships)

# Determine which tasks to run
if [ $# -eq 0 ]; then
  TASKS=("${ALL_TASKS[@]}")
else
  TASKS=("$@")
fi

run_task() {
  local name=$1
  local task

  case "$name" in
    speaking)   task="discover_speaking_ops" ;;
    judging)    task="discover_judging_ops" ;;
    publishing) task="discover_publishing_ops" ;;
    media)      task="discover_media_ops" ;;
    memberships) task="discover_membership_ops" ;;
    *)
      echo "  Unknown task: $name (choose from: speaking judging publishing media memberships)"
      return 1
      ;;
  esac

  echo ""
  echo "▶ Running $name discovery..."
  result=$("$PYTHON" -c "from app.tasks import $task; import json; print(json.dumps($task()))" 2>&1)

  if echo "$result" | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(f\"  ✓ discovered={d['discovered']}  skipped={d['skipped_duplicates']}  failed={d['failed']}\")" 2>/dev/null; then
    :
  else
    echo "  ✗ Error: $result"
  fi
}

echo "================================================"
echo " o1-agent discovery — $(date '+%Y-%m-%d %H:%M')"
echo "================================================"

for task in "${TASKS[@]}"; do
  run_task "$task"
done

echo ""
echo "Done. Open http://localhost:3000/inbox to see results."
