#!/usr/bin/env bash

set -o errexit
set -o pipefail

# ---- config ----
# docker compose subcommand: exec (default) or run
DC="${DC:-exec}"

# pass a TTY only if stdout is a terminal
TTY=""
if [[ ! -t 1 ]]; then
  TTY="-T"
fi

function setup_file_permissions {
  chmod +x backend/docker/entrypoint-api.sh
  chmod +x backend/docker/entrypoint-celery-beat.sh
  chmod +x backend/docker/entrypoint-celery-worker.sh
}

# ---- internal wrapper ----
function _dc {
  docker compose "${DC}" ${TTY} "${@}"
}

# ---- python/fastapi helpers ----

function test {
  _dc api pytest --disable-warnings -rP
}

function generate_secret_key {
  _dc api openssl rand -hex 32
}

# ---- node/npm helpers ----
function node {
  _dc node "${@}"
}

function npm {
  node npm "${@}"
}

function npm_install {
  npm install
}

function npm_ci {
  npm ci
}

function npm_run {
  npm run "${@}"
}

# Clean Vite build artifacts (adjust paths if your setup differs)
function clean_vite_build_files {
  rm -rf public/build
  rm -f public/hot
  rm -rf dist
}

function npm_build {
  clean_vite_build_files
  npm run build
}

function npm_test {
  npm run test "${@}"
}

# Optional helpers for other package managers if you use Corepack/pnpm/yarn
function pnpm {
  _dc pnpm "${@}"
}
function yarn {
  _dc yarn "${@}"
}

# ---- quality of life ----

# Start an interactive shell in the container
function sh {
  docker compose "${DC}" ${TTY} "${SERVICE}" sh -lc "corepack enable || true; sh"
}

function bash {
  docker compose "${DC}" ${TTY} "${SERVICE}" bash -lc "corepack enable || true; bash"
}

# Tail logs (uses `docker compose logs`, not tied to $DC)
function logs {
  docker compose logs -f "${SERVICE}" "${@}"
}

# Clean node_modules and lockfile on host (be careful!)
function clean_install {
  rm -rf node_modules
  rm -f package-lock.json pnpm-lock.yaml yarn.lock
  npm_install
}

# Project bootstrap (customize as you like)
function setup {
  npm_install
  npm_build
}

TIMEFORMAT=$'\nTask completed in %3lR'
time "${@:-help}"