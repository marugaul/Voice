# Aplicación para Mac

El paquete `Susurros-de-Eternidad-Mac.zip` contiene una aplicación iniciadora
`Susurros de Eternidad.app` y las instrucciones de apertura.

Arrastrá la aplicación a Aplicaciones y abrila. En la primera apertura instala
componentes en Terminal y abre la interfaz en el navegador. Si falta Homebrew,
abre su página para instalarlo y luego hay que volver a abrir la aplicación.

No es una aplicación firmada o notarizada por Apple. Si el sistema bloquea su
apertura, revisá Privacidad y seguridad tras intentar abrirla. No se ha ejecutado
en una Mac física: se verificaron la estructura del paquete, sus permisos,
integridad ZIP y sintaxis de los scripts en Linux.

El proyecto operativo queda en:
`~/Library/Application Support/SusurrosDeEternidad`.
Las voces y las narraciones quedan en `studio_data/` dentro de esa carpeta,
fuera de la aplicación. Se conservan al copiar una nueva versión del código.

Dejá Terminal abierta durante el uso; Control+C detiene el motor. La velocidad
inicial de narración es 90%. La primera instalación requiere internet y espacio
para las bibliotecas y los modelos. Usa CPU; el tiempo depende de la Mac.

## Construir el ZIP desde el código

```bash
python3 packaging/build_mac_app.py
```

No requiere modelos, muestras, credenciales ni dependencias de síntesis para
empaquetar. El resultado se guarda en `dist/`, excluido de Git.

Para acceso desde otros dispositivos, consultar [ACCESO_REMOTO.md](ACCESO_REMOTO.md).
La aplicación por sí sola inicia un estudio local; no contrata alojamiento web.
