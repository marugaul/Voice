#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then echo 'Ejecutá primero instalar.command.'; exit 1; fi
export PYTORCH_ENABLE_MPS_FALLBACK=1
export TOKENIZERS_PARALLELISM=false
if command -v open >/dev/null 2>&1; then
  ( .venv/bin/python -c 'import time; time.sleep(2)'; open 'http://127.0.0.1:7860' ) &
fi
.venv/bin/python -m studio.server
