"""Build an unsigned macOS launcher bundle; no personal data or models included.

Runs on Linux or macOS. Native execution must be tested on a Mac.
"""
import hashlib
from pathlib import Path
import plistlib
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
APP = DIST / 'Susurros de Eternidad.app'


def build():
    if APP.exists():
        shutil.rmtree(APP)
    resources = APP / 'Contents' / 'Resources'
    project = resources / 'project'
    executable = APP / 'Contents' / 'MacOS' / 'Susurros'
    executable.parent.mkdir(parents=True)
    project.mkdir(parents=True)
    shutil.copy2(ROOT / 'packaging/macos/launcher', executable)
    executable.chmod(0o755)
    shutil.copy2(ROOT / 'packaging/macos/launch.command', resources / 'launch.command')
    (resources / 'launch.command').chmod(0o755)
    for directory in ('studio', 'openvoice'):
        shutil.copytree(ROOT / directory, project / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('instalar.command', 'iniciar.command', 'iniciar-remoto.command',
                 'LICENSE', 'README.md', 'LEEME_MARKO.md', 'ACCESO_REMOTO.md', 'VALIDACION.md'):
        shutil.copy2(ROOT / name, project / name)
    digest = hashlib.sha256()
    for path in sorted(project.rglob('*')):
        if path.is_file():
            digest.update(path.relative_to(project).as_posix().encode())
            digest.update(path.read_bytes())
    (project / 'APP_VERSION').write_text(digest.hexdigest() + '\n')
    info = {
        'CFBundleName': 'Susurros de Eternidad',
        'CFBundleDisplayName': 'Susurros de Eternidad',
        'CFBundleIdentifier': 'com.susurrosdeeternidad.voicestudio',
        'CFBundleExecutable': 'Susurros',
        'CFBundlePackageType': 'APPL',
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '1',
        'NSHighResolutionCapable': True,
    }
    (APP / 'Contents/Info.plist').write_bytes(plistlib.dumps(info))
    instructions = DIST / 'ABRIR_EN_MAC.txt'
    instructions.write_text('''SUSURROS DE ETERNIDAD · MI VOZ

1. Descomprimí el ZIP y arrastrá Susurros de Eternidad.app a Aplicaciones.
2. Abrila. Si macOS la bloquea por ser de un desarrollador no identificado,
   revisá Privacidad y seguridad > Abrir de todos modos después de intentar abrirla.
   Esta aplicación no está firmada ni notarizada por Apple.
3. Se abrirá Terminal para instalar componentes la primera vez.
   Si falta Homebrew, se abre brew.sh: instalalo y volvé a abrir la app.
4. Cuando termine, se abre la interfaz en el navegador.
5. Cargá una muestra limpia de tu voz, guardala y probá una frase corta.

No consume créditos de ElevenLabs. La primera instalación necesita internet y
varios GB libres. La generación usa la CPU y puede tardar.

Dejá Terminal abierta mientras usás el estudio. Control+C detiene el motor.
Las voces y los audios se guardan en:
~/Library/Application Support/SusurrosDeEternidad/studio_data

Esta es una aplicación iniciadora: abre una interfaz web local, no una ventana
nativa de edición. El paquete se construyó en Linux; no se ha ejecutado en una
Mac física. El parecido de la voz debe valorarse al escuchar una prueba.

Para acceso desde fuera de casa, seguí ACCESO_REMOTO.md en la carpeta de datos.
''', encoding='utf-8')
    archive = DIST / 'Susurros-de-Eternidad-Mac.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
        output.write(instructions, instructions.name)
        for path in sorted(APP.rglob('*')):
            if path.is_file():
                output.write(path, path.relative_to(DIST))
    with zipfile.ZipFile(archive) as output:
        assert output.testzip() is None
        launcher = output.getinfo('Susurros de Eternidad.app/Contents/MacOS/Susurros')
        assert (launcher.external_attr >> 16) & 0o111
        assert not any('/studio_data/' in name or '/.venv/' in name for name in output.namelist())
    print(archive)


if __name__ == '__main__':
    build()
