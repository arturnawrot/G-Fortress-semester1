# Use bash as the interpreter for this script
#!/usr/bin/env bash
# Exit immediately on errors (-e), treat unset vars as errors (-u), and
# make pipelines fail if any command fails (-o pipefail)
set -euo pipefail

# -----------------------------
# ---- Config (overrides) -----
# -----------------------------

# Path to the Security Content Automation Protocol (SCAP) content bundle (SSG)
# Can be overridden by env var SSG_DIR; defaults to the 0.1.78 folder you unzipped
SSG_DIR=${SSG_DIR:-/opt/ssg/scap-security-guide-0.1.78}

# Default XCCDF profile to evaluate (CIS L1 Server for most baseline scans)
PROFILE=${PROFILE:-xccdf_org.ssgproject.content_profile_cis_level1_server}

# Base directory where all scan outputs will be written
OUT_BASE=${OUT_BASE:-/var/lib/gfortress/scans}

# Whether to run OpenSCAP remediation (0 = no, 1 = yes). Off by default.
REMEDIATE=${REMEDIATE:-0}

# Optional URL to POST the JSON summary to your collector
POST_URL=${POST_URL:-}

# Human/agent-friendly host tag; defaults to FQDN or short hostname
HOST_TAG=${HOST_TAG:-$(hostname -f || hostname)}

# Path/command name for jq (used to build JSON nicely). Optional but recommended.
JQ_BIN=${JQ_BIN:-jq}

# Path/command name for xmllint (used to parse XML results)
XMLLINT_BIN=${XMLLINT_BIN:-xmllint}

# -----------------------------
# --------- Helpers -----------
# -----------------------------

# Print an error to stderr and exit with code 2
die(){ echo "ERROR: $*" >&2; exit 2; }

# Ensure the script is running as root, since many checks require it
need_root(){
  if [[ $EUID -ne 0 ]]; then die "Run as root (sudo) so all checks work."; fi
}

# Ensure required binaries exist before proceeding
need_bins(){
  # Verify oscap and xmllint are present
  for b in oscap $XMLLINT_BIN; do command -v "$b" >/dev/null 2>&1 || die "Missing $b"; done
  # If POSTing results, ensure curl exists
  if [[ -n "$POST_URL" ]]; then command -v curl >/dev/null 2>&1 || die "Missing curl for POST"; fi
  # Warn (donâ€™t fail) if jq is missing; weâ€™ll still emit minimal JSON
  command -v $JQ_BIN >/dev/null 2>&1 || echo "WARN: jq not found; JSON will be built without jq."
}

# Choose the correct SSG datastream file for this OS from /etc/os-release
pick_dsfile(){
  # Load OS metadata variables like ID and VERSION_ID
  source /etc/os-release
  # Normalize the ID to lowercase
  local id="${ID,,}"
  # Remove dots from VERSION_ID (e.g., 24.04 -> 2404)
  local ver="${VERSION_ID//./}"
  # Map distro ID/version to the appropriate SSG datastream filename
  case "$id" in
    # Ubuntu uses the ubuntuNNNN naming
    ubuntu)  echo "ssg-ubuntu${ver}-ds.xml" ;;
    # Debian uses debianNN naming (11, 12, 13...)
    debian)  echo "ssg-debian${ver}-ds.xml" ;;
    # RHEL may report ID as rhel or redhat
    rhel|redhat) echo "ssg-rhel${ver}-ds.xml" ;;
    # AlmaLinux mapping
    almalinux) echo "ssg-almalinux${ver}-ds.xml" ;;
    # Oracle Linux appears under various IDs; map to ssg-olNN
    ol|oracle|olinux|oraclelinux) echo "ssg-ol${ver}-ds.xml" ;;
    # Fedora uses a generic single DS file name in the bundle
    fedora) echo "ssg-fedora-ds.xml" ;;
    # openSUSE uses a generic DS name in the bundle
    opensuse) echo "ssg-opensuse-ds.xml" ;;
    # For any unknown distro, bail out with a clear error
    *) die "Unsupported/unknown distro for auto-mapping: $id $VERSION_ID";;
  esac
}

# Emit a UTC timestamp suitable for directory names and event records
ts(){ date -u +%Y%m%dT%H%M%SZ; }

# Build a compact JSON summary from the XCCDF results XML
summarize(){
  # First argument is the path to the results.xml
  local results_xml="$1"
  # Initialize an associative array with all possible result states
  local -A cnt=([pass]=0 [fail]=0 [error]=0 [fixed]=0 [notapplicable]=0 [notchecked]=0 [unknown]=0)
  # For each result state, count the occurrences using XPath with xmllint
  for k in "${!cnt[@]}"; do
    cnt[$k]=$($XMLLINT_BIN --xpath "string(count(//*[local-name()='rule-result']/*[local-name()='result' and text()='$k']))" "$results_xml" 2>/dev/null || echo 0)
  done

  # Extract the benchmark title for context
  local bench_title=$($XMLLINT_BIN --xpath "string(//*[local-name()='Benchmark']/*[local-name()='title'][1])" "$results_xml" 2>/dev/null || echo "")
  # Extract the evaluated profile id (falls back to configured PROFILE on failure)
  local prof_id=$($XMLLINT_BIN --xpath "string(//*[local-name()='TestResult']/*[local-name()='profile'][1]/@idref)" "$results_xml" 2>/dev/null || echo "$PROFILE")

  # If jq exists, construct pretty/typed JSON; otherwise emit minimal JSON
  if command -v $JQ_BIN >/dev/null 2>&1; then
    $JQ_BIN -n --arg host "$HOST_TAG" \
      --arg bench "$bench_title" --arg profile "$prof_id" \
      --arg ts "$(ts)" \
      --arg results_xml "$results_xml" \
      '{
        host: $host,
        timestamp: $ts,
        benchmark_title: $bench,
        profile_id: $profile,
        counts: {
          pass:'"${cnt[pass]}"'|tonumber,
          fail:'"${cnt[fail]}"'|tonumber,
          error:'"${cnt[error]}"'|tonumber,
          fixed:'"${cnt[fixed]}"'|tonumber,
          notapplicable:'"${cnt[notapplicable]}"'|tonumber,
          notchecked:'"${cnt[notchecked]}"'|tonumber,
          unknown:'"${cnt[unknown]}"'|tonumber
        },
        artifacts: {
          results_xml: $results_xml
        }
      }'
  else
    # Fallback JSON without jq (types are strings/numbers as written)
    cat <<EOF
{"host":"$HOST_TAG","timestamp":"$(ts)","benchmark_title":"$bench_title","profile_id":"$prof_id","counts":{"pass":${cnt[pass]},"fail":${cnt[fail]},"error":${cnt[error]},"fixed":${cnt[fixed]},"notapplicable":${cnt[notapplicable]},"notchecked":${cnt[notchecked]},"unknown":${cnt[unknown]}},"artifacts":{"results_xml":"$results_xml"}}
EOF
  fi
}

# If a POST_URL is provided, send the JSON summary to the collector
post_if_needed(){
  # First argument is the JSON file path to send
  local json_file="$1"
  # If no POST_URL set, do nothing
  [[ -z "$POST_URL" ]] && return 0
  # POST the JSON file; on failure, warn but do not abort the script
  curl -fsS -X POST "$POST_URL" \
    -H 'Content-Type: application/json' \
    --data-binary @"$json_file" \
    || echo "WARN: POST to $POST_URL failed"
}

# Print usage help text
usage(){
  cat <<EOF
Usage: sudo $0 [--profile XCCDF_PROFILE] [--remediate 0|1] [--out-dir PATH] [--post-url URL]
Env vars: SSG_DIR, PROFILE, REMEDIATE, OUT_BASE, POST_URL, HOST_TAG
EOF
}

# -----------------------------
# -------- Arg parsing --------
# -----------------------------

# While there are arguments, parse known flags and error on unknowns
while [[ $# -gt 0 ]]; do
  case "$1" in
    # Override the profile via CLI flag
    --profile) PROFILE="$2"; shift 2;;
    # Enable/disable remediation via CLI flag (expects 0 or 1)
    --remediate) REMEDIATE="$2"; shift 2;;
    # Change the base output directory via CLI flag
    --out-dir) OUT_BASE="$2"; shift 2;;
    # Set the collector POST URL via CLI flag
    --post-url) POST_URL="$2"; shift 2;;
    # Show usage and exit
    -h|--help) usage; exit 0;;
    # Any other argument is invalid; abort
    *) die "Unknown arg: $1";;
  esac
done

# -----------------------------
# ----------- Main ------------
# -----------------------------

# Confirm we are root before proceeding
need_root
# Confirm required binaries are present
need_bins

# Compute the datastream file name for this OS
DS_FILE_NAME=$(pick_dsfile)
# Full path to the datastream XML inside the SSG directory
DS_PATH="$SSG_DIR/$DS_FILE_NAME"
# Validate that the datastream file actually exists
[[ -f "$DS_PATH" ]] || die "Datastream not found: $DS_PATH"

# Capture a UTC timestamp for this run
STAMP=$(ts)
# Construct a unique output directory per host and run
OUT_DIR="$OUT_BASE/$HOST_TAG/$STAMP"
# Create the output directory hierarchy
mkdir -p "$OUT_DIR"

# Define standard artifact paths for this run
RESULTS_XML="$OUT_DIR/results.xml"
REPORT_HTML="$OUT_DIR/report.html"
ARF_XML="$OUT_DIR/arf.xml"
LOG="$OUT_DIR/run.log"

# Log that weâ€™re starting the scan
echo "[gfortress] Running OpenSCAP..." | tee -a "$LOG"

# If remediation is enabled, run oscap with --remediate; otherwise, without it.
# --oval-results: include OVAL details for deeper diagnostics
# --results-arf:  write the ARF (Aggregate Result Format) machine-readable file
# --results:      write the XCCDF results XML
# --report:       write a human-friendly HTML report
if [[ "$REMEDIATE" == "1" ]]; then
  oscap xccdf eval \
    --profile "$PROFILE" \
    --oval-results \
    --remediate \
    --results-arf "$ARF_XML" \
    --results "$RESULTS_XML" \
    --report "$REPORT_HTML" \
    "$DS_PATH" | tee -a "$LOG"
else
  oscap xccdf eval \
    --profile "$PROFILE" \
    --oval-results \
    --results-arf "$ARF_XML" \
    --results "$RESULTS_XML" \
    --report "$REPORT_HTML" \
    "$DS_PATH" | tee -a "$LOG"
fi

# Build a JSON summary from the results XML for your agent/collector
SUMMARY_JSON="$OUT_DIR/summary.json"
# Write the JSON summary to disk
summarize "$RESULTS_XML" > "$SUMMARY_JSON"

# If a POST URL was provided, attempt to send the summary now
post_if_needed "$SUMMARY_JSON"

# Print completion message including the output directory path
echo "[gfortress] Done. Output in $OUT_DIR"
# Echo the path to the JSON file on the last line (easy to capture by callers)
echo "$SUMMARY_JSON"
