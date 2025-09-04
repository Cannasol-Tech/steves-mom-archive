#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_HOST=127.0.0.1
BACKEND_PORT=9696
FRONTEND_PORT=6969
BACKEND_URL="http://${BACKEND_HOST}:${BACKEND_PORT}"
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"
LOG_DIR="${REPO_ROOT}/.logs"
PREVIEW_KILL=${PREVIEW_KILL:-1}

mkdir -p "$LOG_DIR"

red()  { printf "\033[31m%s\033[0m\n" "$*"; }
grn()  { printf "\033[32m%s\033[0m\n" "$*"; }
yel()  { printf "\033[33m%s\033[0m\n" "$*"; }

is_port_busy() {
  local port="$1"
  lsof -i :"$port" -sTCP:LISTEN -n -P >/dev/null 2>&1
}

maybe_kill_port() {
  local port="$1"
  if is_port_busy "$port"; then
    yel "Port ${port} is busy."
    lsof -i :"$port" -sTCP:LISTEN -n -P || true
    if [ "$PREVIEW_KILL" = "1" ]; then
      yel "Killing process on port ${port}..."
      local pids
      pids=$(lsof -ti :"$port" -sTCP:LISTEN || true)
      if [ -n "$pids" ]; then
        kill -9 $pids || true
      fi
      sleep 1
    else
      red "Refusing to kill process on port ${port}. Set PREVIEW_KILL=1 to allow auto-kill."
      exit 1
    fi
  fi
}

start_backend() {
  yel "Starting FastAPI backend on ${BACKEND_URL} ..."
  if [ "${PREVIEW_NO_RELOAD:-}" = "1" ]; then
    (.venv/bin/uvicorn backend.api.app:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" >"$LOG_DIR/backend.log" 2>&1 & echo $! >"$LOG_DIR/backend.pid")
  else
    (.venv/bin/uvicorn backend.api.app:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload >"$LOG_DIR/backend.log" 2>&1 & echo $! >"$LOG_DIR/backend.pid")
  fi
}

wait_for_backend() {
  yel "Waiting for backend health..."
  for i in {1..30}; do
    if curl -s -m 1 -o /dev/null -w "%{http_code}" "${BACKEND_URL}/health" | grep -q '^200$'; then
      grn "Backend is up."
      return 0
    fi
    sleep 1
  done
  red "Backend did not become healthy in time. Tail ${LOG_DIR}/backend.log for details."
  return 1
}

start_frontend() {
  yel "Starting CRA frontend on ${FRONTEND_URL} ..."
  (cd "$REPO_ROOT/frontend" && REACT_APP_API_BASE="${BACKEND_URL}" REACT_APP_API_BASE_URL="${BACKEND_URL}" BROWSER=none PORT="$FRONTEND_PORT" npm start >"${LOG_DIR}/frontend.log" 2>&1 & echo $! >"${LOG_DIR}/frontend.pid")
}

wait_for_frontend() {
  yel "Waiting for frontend dev server ..."
  for i in {1..60}; do
    if curl -s -m 1 -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" | grep -E '^(200|301|302)$' >/dev/null; then
      grn "Frontend is up."
      return 0
    fi
    sleep 1
  done
  red "Frontend did not start in time. Tail ${LOG_DIR}/frontend.log for details."
  return 1
}

cleanup() {
  yel "Shutting down preview..."
  for f in backend.pid frontend.pid; do
    if [ -f "${LOG_DIR}/$f" ]; then
      pid=$(cat "${LOG_DIR}/$f" || true)
      if [ -n "${pid:-}" ]; then
        kill $pid 2>/dev/null || true
      fi
      rm -f "${LOG_DIR}/$f"
    fi
  done
}

trap cleanup EXIT

maybe_kill_port "$BACKEND_PORT"
maybe_kill_port "$FRONTEND_PORT"

start_backend
wait_for_backend

start_frontend
wait_for_frontend

yel "Logs:"
yel "  Backend: ${LOG_DIR}/backend.log"
yel "  Frontend: ${LOG_DIR}/frontend.log"
yel "Press Ctrl+C to stop"

# Keep script running to hold child processes
wait

