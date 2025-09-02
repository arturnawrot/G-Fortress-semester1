#!/usr/bin/env bash

set -o errexit
set -o pipefail

# ---- config ----
# docker compose subcommand: exec (default) or run
DC="${DC:-exec}"
# name of the service in docker-compose.yml
SERVICE="${SERVICE:-node}"

# pass a TTY only if stdout is a terminal
TTY=""
if [[ ! -t 1 ]]; then
  TTY="-T"
fi

# ---- internal wrapper ----
function _dc {
  docker compose "${DC}" ${TTY} "${SERVICE}" "${@}"
}

# ---- node/npm helpers ----

function node {
  _dc node "${@}"
}

function npx {
  _dc npx "${@}"
}

function npm {
  _dc npm "${@}"
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

function npm_dev {
  clean_vite_build_files
  npm run dev -- --host
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

# ---- help ----
function help {
  printf "%s <task> [args]\n\nTasks:\n" "${0}"
  # list public functions (exclude internals/this help footer)
  declare -F | awk '{print $3}' \
    | grep -v "^_" \
    | grep -v "^help$" \
    | sort \
    | cat -n
  echo
  echo "Tip: set SERVICE=<service> or DC=run|exec when invoking:"
  echo "  SERVICE=node DC=exec ${0} npm_install"
}

TIMEFORMAT=$'\nTask completed in %3lR'
time "${@:-help}"