#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then echo 'Ejecutá primero instalar.command.'; exit 1; fi
echo 'Antes de continuar, seguí ACCESO_REMOTO.md para activar Tailscale Serve.'
read -r -p 'Dirección HTTPS del estudio en Tailscale: ' OPENVOICE_PUBLIC_URL
export OPENVOICE_PUBLIC_URL
if [ -z "$OPENVOICE_PUBLIC_URL" ]; then echo 'La dirección es obligatoria.'; exit 1; fi
read -r -s -p 'Contraseña del estudio (al menos 16 caracteres): ' OPENVOICE_PASSWORD
echo
export OPENVOICE_PASSWORD
export TOKENIZERS_PARALLELISM=false
echo 'Usuario: marko. La Mac debe permanecer encendida y conectada.'
if command -v caffeinate >/dev/null 2>&1; then
  exec caffeinate -i .venv/bin/python -m studio.server
else
  exec .venv/bin/python -m studio.server
fi
