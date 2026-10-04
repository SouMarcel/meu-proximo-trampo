#!/usr/bin/env sh
# Abre o dashboard (http://127.0.0.1:8765). Ctrl+C para parar.
cd "$(dirname "$0")/.." || exit 1
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python
exec "$PY" dash/servidor.py "$@"
