# Validación

Pruebas realizadas el 26 de octubre de 2026 en Linux, Python 3.10.22,
PyTorch 2.5.1 CPU. No se ha ejecutado en una Mac física.

- Siete pruebas automáticas correctas: división del texto sin perder palabras,
  parámetros inválidos, carga de muestra, trabajos y descargas, controles de
  acceso local y remoto con contraseña, host/origen autorizados y propagación
  de errores del motor.
- Sintaxis de los dos scripts de Terminal y módulos Python comprobada.
- Descarga de pesos oficiales de OpenVoice V2 y carga de MeloTTS español correctas.
- Extracción real de perfil a partir de una grabación autorizada de Marko de
  24,9 segundos después de preparar el audio.
- Síntesis y conversión reales del texto «Soy Marko, tu amigo. Bienvenido a
  Susurros de Eternidad. Que esta noche encuentres paz y descanso.» al 90%.
  Se crearon WAV y MP3 válidos. Se mantuvo el mecanismo de marca de agua.

La prueba verifica el funcionamiento, no el parecido auditivo de la voz.
Quedan pendientes la escucha de Marko y la instalación/rendimiento en su Mac.
No se ha probado aquí un episodio completo de diez minutos.

La distribución excluye grabaciones personales, perfiles, audios generados,
entornos y pesos. El instalador obtiene los modelos al ejecutarse.
