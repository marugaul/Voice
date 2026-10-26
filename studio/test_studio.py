import io
import base64
import json
from pathlib import Path
import tempfile
import time
import unittest
import uuid
import wave

from studio.core import split_text, validate_speed
from studio.server import create_app


class TextTests(unittest.TestCase):
    def test_long_spanish_script_preserves_words_and_order(self):
        source = ('¿Cómo estás? Soy Marko, tu amigo. La fe y la esperanza nos acompañan. ' * 40) + '\n\nBuenas noches.'
        chunks = split_text(source)
        self.assertGreater(len(chunks), 10)
        self.assertEqual(' '.join(t for t, _ in chunks).split(), source.split())
        self.assertTrue(all(len(t) <= 320 for t, _ in chunks))
        self.assertEqual(chunks[-1][1], .55)

    def test_bad_text_and_speed_are_rejected(self):
        for text in ('', '   ', 'a' * 321, 'a' * 60001):
            with self.assertRaises(ValueError):
                split_text(text)
        for speed in (None, 'abc', 0, 2, float('nan')):
            with self.assertRaises(ValueError):
                validate_speed(speed)


class FakeEngine:
    def __init__(self, root):
        self.outputs = Path(root)
        self.identity = str(uuid.uuid4())
        self.created = False

    def status(self):
        return {'models_ready': True, 'ffmpeg': True, 'loaded': False}

    def profile_path(self, identity):
        if identity != self.identity:
            raise ValueError('Elegí una voz guardada.')
        return self.outputs

    def list_profiles(self):
        return [{'id': self.identity, 'name': 'Marko'}]

    def create_profile(self, name, path, progress):
        assert Path(path).read_bytes() == b'voice sample'
        self.created = True
        return {'id': self.identity, 'name': name}

    def generate(self, identity, text, speed, progress):
        self.profile_path(identity)
        progress(.5, 'Mitad del trabajo')
        folder = self.outputs / identity
        folder.mkdir(exist_ok=True)
        (folder / 'narracion.mp3').write_bytes(b'test audio')
        return {'id': identity, 'mp3': f'/api/audio/{identity}/mp3', 'wav': f'/api/audio/{identity}/wav'}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = FakeEngine(self.tmp.name)
        self.app = create_app(self.engine)
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def wait(self, identity):
        for _ in range(100):
            status = self.client.get('/api/jobs/' + identity).get_json()
            if status['state'] in ('done', 'error'):
                return status
            time.sleep(.01)
        self.fail('El trabajo no terminó')

    def test_upload_then_generate_and_download(self):
        response = self.client.post('/api/voices', data={'name': 'Marko', 'own_voice': 'yes', 'sample': (io.BytesIO(b'voice sample'), 'sample.m4a')})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(self.wait(response.json['job'])['state'], 'done')
        self.assertTrue(self.engine.created)
        response = self.client.post('/api/generate', json={'voice': self.engine.identity, 'text': 'Soy Marko, tu amigo.', 'speed': .9})
        self.assertEqual(response.status_code, 202)
        result = self.wait(response.json['job'])
        self.assertEqual(result['state'], 'done')
        with self.client.get(result['result']['mp3']) as download:
            self.assertEqual(download.data, b'test audio')

    def test_input_and_local_origin_protection(self):
        self.assertEqual(self.client.post('/api/generate', json={'text': '', 'speed': .9}).status_code, 400)
        self.assertEqual(self.client.post('/api/generate', json={'text': 'Hola', 'speed': None}).status_code, 400)
        self.assertEqual(self.client.post('/api/voices', data={'name': 'Marko'}).status_code, 400)
        self.assertEqual(self.client.get('/api/status', headers={'Host': 'evil.example'}).status_code, 403)
        self.assertEqual(self.client.post('/api/generate', headers={'Origin': 'https://other.example'}, json={}).status_code, 403)
        self.assertEqual(self.client.get('/api/audio/not-a-uuid/wav').status_code, 404)

    def test_background_failure_reaches_interface(self):
        def fail(*args):
            raise ValueError('No se pudo cargar el modelo')
        self.engine.generate = fail
        response = self.client.post('/api/generate', json={'voice': self.engine.identity, 'text': 'Hola.'})
        result = self.wait(response.json['job'])
        self.assertEqual(result['state'], 'error')
        self.assertIn('No se pudo cargar', result['message'])

    def test_remote_access_requires_password_and_authorized_origin(self):
        url = 'https://marko.example.ts.net'
        client = create_app(self.engine, public_url=url, password='clave-larga-para-la-prueba').test_client()
        auth = 'Basic ' + base64.b64encode(b'marko:clave-larga-para-la-prueba').decode()
        self.assertEqual(client.get('/api/voices', base_url=url).status_code, 401)
        self.assertEqual(client.get('/api/status', base_url=url, headers={'Authorization': 'Basic eDp5'}).status_code, 401)
        response = client.get('/api/status', base_url=url, headers={'Authorization': auth})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['remote_access'])
        self.assertEqual(client.get('/api/status', base_url='https://evil.example', headers={'Authorization': auth}).status_code, 403)
        for origin in (None, 'https://evil.example'):
            headers = {'Authorization': auth}
            if origin: headers['Origin'] = origin
            self.assertEqual(client.post('/api/generate', base_url=url, headers=headers, json={}).status_code, 403)
        response = client.post('/api/generate', base_url=url, headers={'Authorization': auth, 'Origin': url},
                               json={'voice': self.engine.identity, 'text': 'Buenas noches.'})
        self.assertEqual(response.status_code, 202)
        # Let the background operation finish before TemporaryDirectory cleanup.
        for _ in range(100):
            result = client.get('/api/jobs/' + response.json['job'], base_url=url, headers={'Authorization': auth}).json
            if result['state'] in ('done', 'error'): break
            time.sleep(.01)
        self.assertEqual(result['state'], 'done')

    def test_remote_configuration_rejects_weak_passwords_and_bad_urls(self):
        with self.assertRaises(ValueError):
            create_app(self.engine, public_url='https://marko.example.ts.net', password='short')
        for url in ('http://marko.example', 'https://marko.example/path', 'https://user@marko.example'):
            with self.assertRaises(ValueError):
                create_app(self.engine, public_url=url, password='clave-larga-para-la-prueba')


if __name__ == '__main__':
    unittest.main()
