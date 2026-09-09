#!/usr/bin/env bash
# Merge routing templates into ~/.codex without touching model_provider / MCP / notify / plugins.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="astra-luna"
INSTALL_HOME="${CODEX_HOME:-$HOME/.codex}"
DRY_RUN=0
INSTALL_PYTHON="${ASTRA_PYTHON:-$ROOT/.venv/bin/python3}"
if [[ ! -x "$INSTALL_PYTHON" ]]; then
  INSTALL_PYTHON="${ASTRA_PYTHON:-python3}"
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile|--codex-home)
      if [[ $# -lt 2 || -z "$2" || "$2" == --* ]]; then
        echo "$1 requires a value" >&2; exit 2
      fi
      if [[ "$1" == --profile ]]; then PROFILE="$2"; else INSTALL_HOME="$2"; fi
      shift 2
      ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help)
      echo "Usage: $0 [--profile astra-luna|astra-terra|astra-solo|sol-luna] [--codex-home DIR] [--dry-run]"
      exit 0
      ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

case "$PROFILE" in
  astra-luna|astra-terra|astra-solo|sol-luna) ;;
  *)
    echo "invalid profile: $PROFILE (allowed: astra-luna, astra-terra, astra-solo, sol-luna)" >&2
    exit 2
    ;;
esac

if [[ -z "$INSTALL_HOME" ]]; then
  echo "CODEX_HOME must not be empty" >&2
  exit 2
fi
if [[ "$INSTALL_HOME" == *$'\n'* ]]; then
  echo "CODEX_HOME must not contain newlines" >&2
  exit 2
fi

cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

export ASTRA_PROFILE="$PROFILE"
export ASTRA_CODEX_HOME="$INSTALL_HOME"
export ASTRA_DRY_RUN="$DRY_RUN"
"$INSTALL_PYTHON" - <<'PY'
import os
import sys
from pathlib import Path

if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11+ required; set ASTRA_PYTHON to that interpreter.")
try:
    from eval.install_merge import format_verify, install_files, verify_install, write_install
except ModuleNotFoundError as exc:
    raise SystemExit("Missing dependency. Run: python3 -m venv .venv && .venv/bin/python -m pip install -e .") from exc

profile = os.environ["ASTRA_PROFILE"]
codex_home = Path(os.environ["ASTRA_CODEX_HOME"]).expanduser()
if os.environ["ASTRA_DRY_RUN"] == "1":
    print("profile:", profile)
    for relative, content in install_files(codex_home, profile).items():
        print(f"--- {relative} ---")
        print(content)
    raise SystemExit(0)
backup = write_install(codex_home, profile)
errors, summary = verify_install(codex_home, profile)
print(f"installed {profile} into {codex_home}")
print(f"backup: {backup}")
print(format_verify(errors, summary))
if errors:
    raise SystemExit(1)
PY
