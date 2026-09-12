#!/usr/bin/env bash
# Create the reproducible local environment.  Default is intentionally torch-free.
set -euo pipefail

usage() {
  printf '%s\n' "Usage: ./scripts/install.sh [--full]"
  printf '%s\n' "  default  install the offline smoke/demo/test dependencies"
  printf '%s\n' "  --full   also install PyTorch and fair-esm for local ESM-2 extraction"
}

full=0
case "${1:-}" in
  "") ;;
  --full) full=1 ;;
  -h|--help) usage; exit 0 ;;
  *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
esac

if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' "Missing python3. Install Python 3.11 or newer, then rerun this script." >&2
  exit 1
fi

python_version="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
if ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
  printf 'Python %s found; Python 3.11 or newer is required. Install it and rerun.\n' "$python_version" >&2
  exit 1
fi

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$repo_root"

if [ ! -x .venv/bin/python ]; then
  printf '[install] creating .venv with python %s\n' "$python_version"
  python3 -m venv .venv
fi

venv_python="$(pwd)/.venv/bin/python"
printf '%s\n' '[install] installing offline smoke/demo/test dependencies'
"$venv_python" -m pip install --upgrade pip
"$venv_python" -m pip install -r requirements.txt

if [ "$full" -eq 1 ]; then
  printf '%s\n' '[install] installing optional ESM-2 dependencies (PyTorch and fair-esm)'
  "$venv_python" -m pip install -r requirements-full.txt
  printf '%s\n' '[install] Full mode does not download the GB1 CSV. See data/README.md for its source and placement.'
fi

"$venv_python" - <<'PY'
import importlib
modules = ('numpy', 'pandas', 'scipy', 'sklearn', 'yaml', 'networkx', 'pydantic', 'streamlit', 'matplotlib')
for module in modules:
    importlib.import_module(module)
print('[install] verified imports: ' + ', '.join(modules))
PY

printf '%s\n' '[install] ready. Next: ./scripts/run_all.sh (self-contained smoke by default).'
