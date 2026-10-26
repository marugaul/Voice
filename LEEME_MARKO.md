# Mi voz · Susurros de Eternidad

Una aplicación local para narrar guiones en español con una muestra de tu voz.
Usa OpenVoice V2 para adaptar el timbre y MeloTTS para leer el texto.

## En tu Mac

1. Descomprimí la carpeta y ponela en Documentos.
2. Instalá Homebrew desde https://brew.sh si todavía no lo tenés.
3. Abrí Terminal y ejecutá `brew install uv ffmpeg`.
4. En Terminal, escribí `cd `, arrastrá la carpeta del proyecto y presioná Enter.
5. Ejecutá `bash instalar.command`. La primera instalación descarga Python,
   bibliotecas y modelos. Necesita internet y varios GB de espacio libre.
6. Ejecutá `bash iniciar.command`. Abrirá http://127.0.0.1:7860 en tu navegador.
   Mantené abierta esa Terminal mientras trabajás; Control+C detiene el estudio.

El instalador usa un entorno Python 3.10 dentro de la carpeta, sin cambiar el
Python del sistema. Es repetible: no borra tus voces ni narraciones.

Para usarlo desde fuera de casa, seguí `ACCESO_REMOTO.md`.

## Tu primera prueba

1. Grabá 30–60 segundos en Notas de voz, con tono natural, sin música ni eco.
2. Cargá el M4A, nombrá la voz y elegí «Guardar mi voz».
3. Seleccioná la voz, escribí una frase corta y elegí «Crear narración».
4. Escuchá la prueba antes de generar un guion completo.
5. Para los relatos, cargá un TXT, dejá líneas en blanco entre párrafos y usá
   90% de velocidad si te gusta un ritmo tranquilo.
6. Descargá MP3 para el montaje o WAV para editarlo.

## Qué esperar

- La aplicación procesa el texto por bloques para admitir guiones largos
  (hasta 60.000 caracteres por trabajo).
- La muestra y el perfil se guardan en `studio_data/voices`; las narraciones,
  en `studio_data/outputs`. Guardá una copia de esa carpeta si querés respaldarlos.
- La primera generación descarga también el modelo de español y sus recursos.
  Las siguientes reutilizan lo descargado. No se envían tus muestras al servicio
  de ElevenLabs ni hay una cuota por caracteres de esta aplicación.
- El motor toma el timbre de la referencia; la pronunciación y el acento también
  dependen de la voz base de MeloTTS. No se garantiza conservar el acento
  costarricense ni un resultado idéntico a tu grabación.
- Mac usa CPU deliberadamente. Puede tardar más que la duración del audio;
  no se ha medido el rendimiento en tu Mac. No es un servicio en la nube.
- El estudio escucha únicamente en la computadora local. No lo expongás
  directamente a internet. Necesita una instalación distinta para uso multiusuario.

## Si algo falla

- «Faltan modelos»: repetí `bash instalar.command`.
- «Falta FFmpeg»: ejecutá `brew install ffmpeg`.
- Una descarga puede fallar por conexión; el mensaje de error aparece en pantalla
  y el detalle en Terminal. Revisá la conexión y volvé a intentar.
- La voz sale diferente: probá una muestra limpia, sin susurrar ni forzar el tono.
- Guardá primero una muestra nueva antes de generar todos los capítulos.

## Fuentes y licencias

- OpenVoice: https://github.com/myshell-ai/OpenVoice
  Base: commit `74a1d147b17a8c3092dd5430504bd83ef6c7eb23`.
- MeloTTS: https://github.com/myshell-ai/MeloTTS
  Base: commit `209145371cff8fc3bd60d7be902ea69cbdb7965a`.
- Ambos proyectos declaran licencia MIT. Se conserva LICENSE de OpenVoice;
  el repositorio de MeloTTS conserva la suya al instalarse.
- Adaptaciones propias en `studio/` y archivos `.command`. El adaptador de
  instalación limita las importaciones de MeloTTS a español; no cambia sus pesos.
- OpenVoice conserva su mecanismo de marca de agua de audio.

## Comprobaciones para desarrollo

`python -m unittest studio.test_studio -v`

Estas pruebas verifican conservación del texto, validaciones, trabajos en segundo
plano y descargas con un motor de prueba. No sustituyen una prueba auditiva del
parecido de la voz. Las pruebas de síntesis real, cuando se completen, se anotan
en `VALIDACION.md`.
