#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v uv >/dev/null 2>&1 || ! command -v ffmpeg >/dev/null 2>&1; then
  echo 'Primero instalá uv y FFmpeg desde Terminal:'
  echo '  brew install uv ffmpeg'
  echo 'Si no tenés Homebrew, instalalo desde https://brew.sh y volvé a ejecutar este archivo.'
  exit 1
fi
uv python install 3.10
if [ ! -d .venv ]; then uv venv --python 3.10 --seed .venv; fi
uv pip install --python .venv/bin/python -r studio/requirements.txt wheel
.venv/bin/python -m studio.setup_models
echo 'Instalación terminada. Ahora abrí iniciar.command.'
