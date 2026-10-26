#!/bin/bash
set -euo pipefail
project_source="$1"
project_data="$HOME/Library/Application Support/SusurrosDeEternidad"
mkdir -p "$project_data"
/usr/bin/ditto "$project_source" "$project_data"
cd "$project_data"

echo 'Susurros de Eternidad · Mi voz'
echo 'La primera apertura descarga componentes y modelos. Puede tardar varios minutos.'
echo 'Tus grabaciones y narraciones quedan en esta Mac.'

# Finder does not inherit the shell path configured by Homebrew.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v brew >/dev/null 2>&1; then
  echo
  echo 'Falta Homebrew. Instalalo desde la página que se abrirá y volvé a abrir la aplicación.'
  /usr/bin/open 'https://brew.sh'
  exit 1
fi
if ! command -v uv >/dev/null 2>&1 || ! command -v ffmpeg >/dev/null 2>&1; then
  brew install uv ffmpeg
fi

package_version="$(cat APP_VERSION)"
installed_version="$(cat .installed_app_version 2>/dev/null || true)"
if [ ! -x .venv/bin/python ] || [ "$installed_version" != "$package_version" ]; then
  bash instalar.command
  printf '%s\n' "$package_version" > .installed_app_version
fi

echo
echo 'La interfaz se abrirá en el navegador. Mantené esta Terminal abierta.'
echo 'Para cerrar el motor, presioná Control+C en esta ventana.'
if command -v caffeinate >/dev/null 2>&1; then
  exec caffeinate -i bash iniciar.command
else
  exec bash iniciar.command
fi
