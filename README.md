# Voice · Susurros de Eternidad

Página para crear narraciones en español a partir de guiones y una muestra
de voz propia o autorizada. Construida con Flask, OpenVoice V2 y MeloTTS.

## Funciones

- Guardar un perfil de voz desde M4A, MP3, WAV, FLAC u OGG.
- Pegar un guion o cargar un TXT; hasta 60.000 caracteres.
- Ajustar velocidad entre 75% y 120%, con 90% inicial.
- Escuchar y descargar MP3 y WAV.
- Procesamiento por bloques y progreso de cada trabajo.

## Arranque en Mac

Necesitás Homebrew, Git y espacio para Python, bibliotecas y modelos.

```bash
git clone https://github.com/marugaul/Voice.git
cd Voice
brew install uv ffmpeg
bash instalar.command
bash iniciar.command
```

Abrí **http://127.0.0.1:7860**. Dejá Terminal abierta durante el uso.
La primera instalación y la primera generación requieren internet.

Para empezar, grabá entre 30 y 60 segundos sin música ni ruido. Guardá la voz y
probá una frase corta antes de generar todo un episodio.

Instrucciones completas: [LEEME_MARKO.md](LEEME_MARKO.md).
Resultados de las pruebas y límites: [VALIDACION.md](VALIDACION.md).

## Página y servidor

**Acceso desde cualquier lugar:** seguí [ACCESO_REMOTO.md](ACCESO_REMOTO.md).
Incluye acceso privado por HTTPS con Tailscale y contraseña. Podés usar el
celular o una computadora fuera de casa; la Mac sigue procesando los audios.

La interfaz está en `studio/index.html`; el servidor se inicia con
`python -m studio.server`. Abrir el HTML por separado no genera audio.
GitHub aloja el código; GitHub Pages no puede ejecutar este motor Python.
Esta versión funciona localmente o en tus dispositivos mediante Tailscale.
Publicarla para varios usuarios
requiere un servidor con autenticación y una configuración distinta.

La CPU de la Mac realiza la generación. No se ha probado en una Mac física;
la síntesis real se verificó en Linux. El parecido y el acento pueden variar.

## Datos privados

`studio_data/` contiene muestras, perfiles y narraciones. No se sube a Git.
Tampoco se incluyen pesos, entornos, contraseñas ni archivos `.env`.
Respaldá `studio_data/` por separado si querés conservar tus voces.

## Desarrollo

```bash
python -m unittest studio.test_studio -v
```

Estas siete pruebas usan un motor simulado; no descargan modelos.
Para ejecutarlas basta instalar Flask: `python -m pip install flask==3.0.3`.

## Créditos

OpenVoice V2: https://github.com/myshell-ai/OpenVoice, licencia MIT.
La documentación original se conserva en [README_OPENVOICE.md](README_OPENVOICE.md).
MeloTTS: https://github.com/myshell-ai/MeloTTS, licencia MIT.
Se conserva la marca de agua del motor OpenVoice.
