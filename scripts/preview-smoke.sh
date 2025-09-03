#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="http://127.0.0.1:9696"
FRONTEND_URL="http://localhost:6969"

red()  { printf "\033[31m%s\033[0m\n" "$*"; }
grn()  { printf "\033[32m%s\033[0m\n" "$*"; }
yel()  { printf "\033[33m%s\033[0m\n" "$*"; }

fail() { red "[FAIL] $*"; exit 1; }
pass() { grn "[PASS] $*"; }
info() { yel "[INFO] $*"; }

# 1) Backend health
info "Checking backend health at ${BACKEND_URL}/health ..."
if command -v curl >/dev/null 2>&1; then
  code=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/health" || true)
  if [ "$code" != "200" ]; then
    fail "Backend /health returned HTTP ${code} (expected 200). Is make preview running?"
  fi
  pass "Backend health OK"
else
  info "curl not found; skipping HTTP checks."
fi

# 2) Backend chat endpoint basic contract
info "Probing backend /api/chat with minimal payload ..."
if command -v curl >/dev/null 2>&1; then
  resp=$(curl -s -X POST "${BACKEND_URL}/api/chat" \
    -H 'Content-Type: application/json' \
    -d '{"messages":[{"role":"user","content":"ping"}]}' || true)
  if [ -z "$resp" ]; then
    fail "/api/chat returned empty response"
  fi
  pass "/api/chat responded (stream or text)"
fi

# 3) Frontend dev server reachable
info "Checking frontend at ${FRONTEND_URL} ..."
if command -v curl >/dev/null 2>&1; then
  code=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}" || true)
  case "$code" in
    200|301|302)
      pass "Frontend reachable (HTTP ${code})"
      ;;
    *)
      fail "Frontend not reachable (HTTP ${code}). Check CRA dev server logs."
      ;;
  esac
fi

# 4) Proxy check: fetch from frontend path that calls backend
info "Proxy spot-check via /api/health through frontend origin (should proxy to backend) ..."
if command -v curl >/dev/null 2>&1; then
  code=$(curl -s -o /dev/null -w "%{http_code}" "${FRONTEND_URL}/api/health" || true)
  if [ "$code" != "200" ]; then
    fail "Proxy check failed: GET ${FRONTEND_URL}/api/health returned ${code} (expected 200)"
  fi
  pass "Proxy check OK"
fi

pass "Smoke checks passed. make preview appears healthy."

