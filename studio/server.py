import logging
import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import threading
import uuid
from urllib.parse import urlsplit

from flask import Flask, jsonify, request, send_file, Response
from studio.core import split_text, validate_speed
from studio.engine import VoiceEngine


def create_app(engine=None, public_url=None, password=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 80 * 1024 * 1024
    public_url = (public_url or os.environ.get('OPENVOICE_PUBLIC_URL', '')).rstrip('/')
    password = password or os.environ.get('OPENVOICE_PASSWORD', '')
    remote = bool(public_url)
    if remote:
        parsed = urlsplit(public_url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.port:
            raise ValueError('OPENVOICE_PUBLIC_URL debe ser la dirección HTTPS de Tailscale, sin rutas ni puerto.')
        if len(password) < 16:
            raise ValueError('El acceso remoto requiere OPENVOICE_PASSWORD de al menos 16 caracteres.')
    app.config['REMOTE_ACCESS'] = remote
    engine = engine or VoiceEngine()
    pool = ThreadPoolExecutor(max_workers=1)
    jobs = {}
    lock = threading.Lock()

    @app.before_request
    def protect_access():
        local = request.host.split(':')[0] in ('127.0.0.1', 'localhost')
        expected_host = urlsplit(public_url).netloc if remote else ''
        if not local and (not remote or request.host != expected_host):
            return jsonify(error='El estudio solo acepta conexiones locales.'), 403
        origin = request.headers.get('Origin')
        expected_origin = request.host_url.rstrip('/') if local else public_url
        if (origin and origin.rstrip('/') != expected_origin) or (remote and request.method == 'POST' and not origin):
            return jsonify(error='Abrí el estudio desde su dirección autorizada.'), 403
        if remote:
            auth = request.authorization
            if not auth or auth.type.lower() != 'basic' or not secrets.compare_digest(auth.username or '', 'marko') or not secrets.compare_digest((auth.password or '').encode(), password.encode()):
                return Response('Ingresá con el usuario marko y tu contraseña del estudio.', 401,
                                {'WWW-Authenticate': 'Basic realm="Susurros de Eternidad", charset="UTF-8"'})

    def enqueue(fn):
        identity = str(uuid.uuid4())
        with lock:
            if any(j['state'] in ('queued', 'running') for j in jobs.values()):
                raise ValueError('Ya hay un trabajo en curso. Esperá a que termine.')
            jobs[identity] = {'state': 'queued', 'progress': 0, 'message': 'Preparando modelos; la primera vez puede tardar varios minutos…'}

        def progress(value, message):
            with lock:
                jobs[identity].update(progress=value, message=message)

        def run():
            with lock:
                jobs[identity]['state'] = 'running'
            try:
                result = fn(progress)
                with lock:
                    jobs[identity].update(state='done', progress=1, message='Listo.', result=result)
            except Exception as exc:
                logging.exception('Falló el trabajo %s', identity)
                with lock:
                    jobs[identity].update(state='error', message=str(exc) or 'No se pudo completar el trabajo.')
        pool.submit(run)
        return identity

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    @app.errorhandler(ValueError)
    def invalid(exc):
        return jsonify(error=str(exc)), 400

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(error='El archivo supera 80 MB. Usá una muestra más corta.'), 413

    @app.get('/')
    def index():
        return send_file(Path(__file__).parent / 'index.html')

    @app.get('/api/status')
    def status():
        return jsonify({**engine.status(), 'remote_access': remote})

    @app.get('/api/voices')
    def voices():
        return jsonify(engine.list_profiles())

    @app.post('/api/voices')
    def create_voice():
        if request.form.get('own_voice') != 'yes':
            raise ValueError('Confirmá que estás usando tu propia voz o una voz autorizada.')
        file = request.files.get('sample')
        if not file or not file.filename:
            raise ValueError('Cargá una grabación de voz.')
        name = request.form.get('name', '').strip()[:60]
        if not name:
            raise ValueError('Poné un nombre a tu voz.')
        extension = Path(file.filename).suffix.lower()
        if extension not in ('.wav', '.mp3', '.m4a', '.flac', '.ogg'):
            raise ValueError('Usá un archivo M4A, MP3, WAV, FLAC u OGG.')
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / ('sample' + extension)
        file.save(path)

        def job(progress):
            try:
                return engine.create_profile(name, path, progress)
            finally:
                tmp.cleanup()
        try:
            identity = enqueue(job)
        except Exception:
            tmp.cleanup()
            raise
        return jsonify(job=identity), 202

    @app.post('/api/generate')
    def generate():
        payload = request.get_json(silent=True) or {}
        text = payload.get('text')
        if not isinstance(text, str):
            raise ValueError('Escribí el texto que querés narrar.')
        split_text(text)
        speed = validate_speed(payload.get('speed', 0.9))
        identity = payload.get('voice', '')
        engine.profile_path(identity)
        return jsonify(job=enqueue(lambda progress: engine.generate(identity, text, speed, progress))), 202

    @app.get('/api/jobs/<identity>')
    def job_status(identity):
        with lock:
            if identity not in jobs:
                return jsonify(error='Trabajo no encontrado. Si reiniciaste la aplicación, iniciá uno nuevo.'), 404
            return jsonify(jobs[identity])

    @app.get('/api/audio/<identity>/<kind>')
    def audio(identity, kind):
        try:
            identity = str(uuid.UUID(identity))
        except ValueError:
            return jsonify(error='Audio no encontrado.'), 404
        if kind not in ('wav', 'mp3'):
            return jsonify(error='Formato no válido.'), 404
        path = engine.outputs / identity / f'narracion.{kind}'
        if not path.is_file():
            return jsonify(error='Audio no encontrado.'), 404
        return send_file(path, as_attachment=request.args.get('download') == '1', download_name=f'Marko_narracion.{kind}')

    return app


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=7860)
    args = parser.parse_args()
    from waitress import serve
    # Bind only to loopback, including in remote mode. Tailscale Serve provides
    # private HTTPS and forwards requests here; never use Tailscale Funnel.
    serve(create_app(), host='127.0.0.1', port=args.port, threads=4,
          max_request_body_size=80 * 1024 * 1024)
