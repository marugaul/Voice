import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

from studio.core import split_text, validate_speed

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('OPENVOICE_DATA', ROOT / 'studio_data')).resolve()


def run_ffmpeg(args):
    if not shutil.which('ffmpeg'):
        raise ValueError('Falta FFmpeg. Ejecutá: brew install ffmpeg')
    proc = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', *map(str, args)], capture_output=True, text=True)
    if proc.returncode:
        raise ValueError('No pude procesar el audio. Probá con otro M4A, MP3 o WAV. ' + proc.stderr[-300:])


class VoiceEngine:
    def __init__(self, data=DATA):
        self.data = Path(data)
        self.profiles = self.data / 'voices'
        self.outputs = self.data / 'outputs'
        self.profiles.mkdir(parents=True, exist_ok=True)
        self.outputs.mkdir(parents=True, exist_ok=True)
        self.converter = None
        self.tts = None
        self.device = None

    def status(self):
        ckpt = ROOT / 'checkpoints_v2' / 'converter'
        return {'models_ready': all((ckpt / n).is_file() for n in ('config.json', 'checkpoint.pth')),
                'ffmpeg': bool(shutil.which('ffmpeg')), 'device': self.device or 'Sin cargar',
                'loaded': self.converter is not None and self.tts is not None}

    def load(self):
        if self.converter is not None and self.tts is not None:
            return
        if not self.status()['models_ready']:
            raise ValueError('Faltan los modelos. Cerrá esta ventana y ejecutá instalar.command.')
        import torch
        # Melo's BERT helper moves CPU tensors to MPS on Darwin unless disabled.
        # CPU is deliberate for Mac compatibility; CUDA is used on Linux if present.
        device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        if device == 'cpu' and hasattr(torch.backends, 'mps'):
            torch.backends.mps.is_available = lambda: False
        torch.set_num_threads(max(1, min(6, os.cpu_count() or 2)))
        from openvoice.api import ToneColorConverter
        from melo.api import TTS
        ckpt = ROOT / 'checkpoints_v2' / 'converter'
        converter = ToneColorConverter(str(ckpt / 'config.json'), device=device)
        converter.load_ckpt(str(ckpt / 'checkpoint.pth'))
        tts = TTS(language='ES', device=device)
        self.converter, self.tts, self.device = converter, tts, device

    def list_profiles(self):
        result = []
        for p in sorted(self.profiles.glob('*/profile.json')):
            try:
                result.append(json.loads(p.read_text(encoding='utf-8')))
            except (OSError, ValueError):
                continue
        return result

    def profile_path(self, identity):
        try:
            identity = str(uuid.UUID(identity))
        except (ValueError, TypeError):
            raise ValueError('Elegí una voz guardada.') from None
        path = self.profiles / identity
        if not (path / 'profile.json').is_file():
            raise ValueError('No encontré la voz seleccionada.')
        return path

    def create_profile(self, name, sample_path, progress=lambda *_: None):
        name = str(name).strip()[:60]
        if not name:
            raise ValueError('Poné un nombre a tu voz.')
        self.load()
        import numpy as np
        import soundfile as sf
        import torch
        identity = str(uuid.uuid4())
        dest = self.profiles / identity
        dest.mkdir()
        try:
            wav = dest / 'reference.wav'
            progress(0.15, 'Preparando tu muestra…')
            run_ffmpeg(['-i', sample_path, '-t', '120', '-ac', '1', '-ar', '22050', '-af',
                        'highpass=f=65,silenceremove=start_periods=1:start_duration=0.1:start_threshold=-45dB:stop_periods=-1:stop_duration=0.8:stop_threshold=-45dB',
                        '-y', wav])
            audio, sr = sf.read(wav)
            if len(audio) < sr * 8:
                raise ValueError('La muestra necesita al menos 8 segundos de voz; recomendamos 30–60 segundos limpios.')
            blocks = audio[:len(audio)//2205*2205].reshape(-1, 2205)
            spoken = float(np.sum(np.sqrt(np.mean(blocks**2, axis=1)) > 0.008) / 10)
            if spoken < 5:
                raise ValueError('La muestra tiene demasiado silencio o un volumen muy bajo.')
            progress(0.6, 'Creando tu perfil de voz…')
            # Direct extraction avoids the upstream CUDA-only Whisper path.
            refs = []
            for index, start in enumerate(range(0, len(audio), sr * 15)):
                chunk = audio[start:start + sr * 15]
                if len(chunk) < sr * 2:
                    continue
                p = dest / f'part-{index}.wav'
                sf.write(p, chunk, sr)
                refs.append(str(p))
            self.converter.extract_se(refs, se_save_path=str(dest / 'voice.pth'))
            for part in dest.glob('part-*.wav'):
                part.unlink()
            info = {'id': identity, 'name': name, 'seconds': round(len(audio) / sr, 1)}
            (dest / 'profile.json').write_text(json.dumps(info, ensure_ascii=False), encoding='utf-8')
            return info
        except Exception:
            shutil.rmtree(dest, ignore_errors=True)
            raise

    def generate(self, identity, text, speed=0.9, progress=lambda *_: None):
        chunks = split_text(text)
        speed = validate_speed(speed)
        profile = self.profile_path(identity)
        self.load()
        import numpy as np
        import soundfile as sf
        import torch
        speaker_key, speaker_id = next(iter(self.tts.hps.data.spk2id.items()))
        key = speaker_key.lower().replace('_', '-')
        source_path = ROOT / 'checkpoints_v2' / 'base_speakers' / 'ses' / f'{key}.pth'
        if not source_path.is_file():
            raise ValueError(f'Falta la referencia española: {source_path.name}. Ejecutá instalar.command.')
        source = torch.load(str(source_path), map_location=self.device, weights_only=True)
        target = torch.load(str(profile / 'voice.pth'), map_location=self.device, weights_only=True)
        identity = str(uuid.uuid4())
        final = self.outputs / identity
        final.mkdir()
        try:
            sample_rate = self.converter.hps.data.sampling_rate
            with sf.SoundFile(final / 'raw.wav', mode='w', samplerate=sample_rate, channels=1, subtype='PCM_16') as output:
                with tempfile.TemporaryDirectory(dir=final) as tmp:
                    tmp = Path(tmp)
                    for index, (chunk, pause) in enumerate(chunks):
                        progress(index / len(chunks), f'Narrando bloque {index + 1} de {len(chunks)}…')
                        self.tts.tts_to_file(chunk, speaker_id, str(tmp / 'base.wav'), speed=1.0, quiet=True)
                        self.converter.convert(str(tmp / 'base.wav'), source, target, output_path=str(tmp / 'converted.wav'), message='@MyShell')
                        audio, sr = sf.read(tmp / 'converted.wav')
                        if sr != sample_rate:
                            raise ValueError('El modelo produjo una frecuencia de audio inesperada.')
                        output.write(audio)
                        if index < len(chunks) - 1:
                            output.write(np.zeros(int(sample_rate * pause)))
            progress(0.96, 'Ajustando volumen y preparando descargas…')
            # Apply speed once, after synthesis, while preserving pitch.
            run_ffmpeg(['-i', final / 'raw.wav', '-af', f'atempo={speed},loudnorm=I=-18:TP=-2:LRA=7', '-ar', '44100', '-y', final / 'narracion.wav'])
            run_ffmpeg(['-i', final / 'narracion.wav', '-c:a', 'libmp3lame', '-b:a', '192k', '-y', final / 'narracion.mp3'])
            (final / 'raw.wav').unlink()
            (final / 'guion.txt').write_text(text, encoding='utf-8')
            return {'id': identity, 'mp3': f'/api/audio/{identity}/mp3', 'wav': f'/api/audio/{identity}/wav'}
        except Exception:
            shutil.rmtree(final, ignore_errors=True)
            raise
