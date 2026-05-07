#!/bin/bash
# Knowledge Radar Backend — Start Script
# Saves the PID so the PM2 / systemd can manage it

PORT=${PORT:-8787}
HOST=${HOST:-127.0.0.1}
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/server.log"
PIDFILE="$DIR/server.pid"

# Load .env if exists
if [ -f "$DIR/.env" ]; then
  set -a; source "$DIR/.env"; set +a
fi

export FEISHU_TOKEN="${FEISHU_TOKEN:-}"
export LLM_API_KEY="${LLM_API_KEY:-}"
export LLM_BASE_URL="${LLM_BASE_URL:-https://api.openai.com/v1}"
export LLM_MODEL="${LLM_MODEL:-gpt-4o-mini}"

cd "$DIR"
echo "Starting Knowledge Radar Backend..."
echo "  Port: $PORT"
echo "  Feishu: $([ -n "$FEISHU_TOKEN" ] && echo 'connected' || echo 'no token')"
echo "  LLM: $([ -n "$LLM_API_KEY" ] && echo "$LLM_MODEL" || echo 'disabled')"

npx --yes node server.js > "$LOG" 2>&1 &
PID=$!
echo $PID > "$PIDFILE"
echo "  PID: $PID"
echo "  Log: $LOG"
echo "Ready."
