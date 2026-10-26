# Usar el estudio desde cualquier lugar

Esta versión permite entrar desde tus dispositivos conectados a Tailscale.
La Mac procesa los audios y debe permanecer encendida, con internet y con el
estudio abierto. No está desplegada todavía: estos pasos se realizan en tu Mac.

## Configurar una vez

1. Instalá la aplicación con `bash instalar.command`.
2. Instalá Tailscale en la Mac y en el celular, iPad u otra computadora desde
   https://tailscale.com/download. Iniciá sesión con la misma cuenta.
3. En Terminal de la Mac ejecutá:

   ```bash
   tailscale serve --bg http://127.0.0.1:7860
   ```

   Si `tailscale` no aparece como comando, usá la ruta de la aplicación:

   ```bash
   /Applications/Tailscale.app/Contents/MacOS/Tailscale serve --bg http://127.0.0.1:7860
   ```

4. Si pide habilitar HTTPS/Serve, abrí el enlace que indique y completá el paso.
   Copiá la dirección HTTPS que devuelve, por ejemplo `https://mi-mac.mi-red.ts.net`.
   Usá **Serve**, que comparte dentro de tu red privada, no Funnel.
5. Desde la carpeta Voice ejecutá:

   ```bash
   bash iniciar-remoto.command
   ```

6. Pegá la dirección HTTPS sin barra final ni rutas. Elegí una contraseña de al
   menos 16 caracteres; no se guarda en Git ni en un archivo. Necesitarás escribir
   la misma al reiniciar si querés seguir usándola.
7. Desde otro dispositivo, activá Tailscale y abrí esa dirección en el navegador.
   Usuario **marko**, contraseña la que elegiste. La ventana de acceso la muestra
   el navegador. Después verás la interfaz completa, adaptada a móvil.

Podés guardar la página como acceso directo en tu celular. No importa si usás
otra red Wi-Fi o datos móviles mientras Tailscale esté conectado y permitido por
las reglas de tu red privada.

## Durante el uso

- Dejá la Terminal abierta. Control+C detiene el estudio.
- El iniciador evita el reposo por inactividad en macOS mientras corre; cerrar
  la tapa, apagar o desconectar la Mac puede interrumpir el acceso.
- Las voces y los MP3 quedan en `studio_data/` de la Mac. Podés descargarlos
  desde la página en el dispositivo que estés usando.
- No abras puertos en el router. El servidor solo escucha en 127.0.0.1.
- Para desactivar el acceso de Tailscale Serve, ejecutá `tailscale serve reset`
  (esto elimina la configuración Serve de esta Mac, incluso otros servicios que
  hayas configurado allí; revisá antes `tailscale serve status`).

## Si querés que funcione con la Mac apagada

Hay que instalar el motor en un servidor con almacenamiento persistente y
capacidad de cómputo. GitHub Pages solo aloja páginas estáticas y no ejecuta
OpenVoice. Esta entrega no contrata ni configura un servidor de pago.

## Validación pendiente

Las pruebas automáticas comprueban contraseña, host y origen autorizados.
No se ha probado una conexión real entre tus dispositivos ni se ha configurado
Tailscale en tu cuenta. Ese paso requiere instalarlo en tu Mac.

Documentación oficial:
- https://tailscale.com/docs/reference/tailscale-cli/serve
- https://tailscale.com/docs/reference/examples/serve
- https://tailscale.com/docs/reference/tailscale-cli
