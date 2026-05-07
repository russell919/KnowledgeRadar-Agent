#!/bin/bash
# Knowledge Radar Backend — Proactive Keep-Alive Script
# Run from heartbeat or cron to ensure backend is up

PORT=8787
DIR="$HOME/.openclaw/workspace/knowledge-radar/backend-server"
PIDFILE="$DIR/server.pid"
LOGFILE="$DIR/server.log"

# Load .env
if [ -f "$DIR/.env" ]; then
  set -a; source "$DIR/.env"; set +a
fi

# Check if server is running
if [ -f "$PIDFILE" ]; then
  PID=$(cat "$PIDFILE")
  if kill -0 "$PID" 2>/dev/null; then
    # Quick health check
    HEALTH=$(curl -sf "http://127.0.0.1:$PORT/v1/health" 2>/dev/null)
    if [ -n "$HEALTH" ]; then
      exit 0  # All good
    fi
    echo "[$(date)] Server PID $PID exists but health check failed, restarting..."
    kill "$PID" 2>/dev/null
    sleep 2
  else
    echo "[$(date)] Stale PID file, restarting..."
  fi
fi

# Start server
cd "$DIR"
nohup node server.js >> "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"
echo "[$(date)] Server started, PID $(cat $PIDFILE)"
