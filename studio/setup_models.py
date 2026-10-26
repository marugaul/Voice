"""Fetch official OpenVoice weights and a pinned, Spanish-only MeloTTS adapter."""
from pathlib import Path
import subprocess
import urllib.request
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
MELO_COMMIT = '209145371cff8fc3bd60d7be902ea69cbdb7965a'
MODEL_COMMIT = 'f36e7edfe1684461a8343844af60babc2efbb727'


def download(url, destination):
    destination = Path(destination)
    partial = destination.with_suffix(destination.suffix + '.part')
    try:
        with urllib.request.urlopen(url, timeout=120) as source, partial.open('wb') as target:
            shutil.copyfileobj(source, target)
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)


def setup():
    converter = ROOT / 'checkpoints_v2' / 'converter'
    print('Preparando modelos oficiales de OpenVoice V2…', flush=True)
    for relative in ('converter/config.json', 'converter/checkpoint.pth', 'base_speakers/ses/es.pth'):
        dest = ROOT / 'checkpoints_v2' / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.is_file():
            print('Descargando ' + relative, flush=True)
            download(f'https://huggingface.co/myshell-ai/OpenVoiceV2/resolve/{MODEL_COMMIT}/{relative}', dest)
    if not (converter / 'config.json').is_file():
        raise RuntimeError('No se encontró checkpoints_v2/converter. Revisá la descarga oficial.')

    vendor = ROOT / 'vendor' / 'MeloTTS'
    vendor.parent.mkdir(exist_ok=True)
    if not (vendor / 'melo' / 'api.py').is_file():
        subprocess.run(['git', 'clone', 'https://github.com/myshell-ai/MeloTTS.git', str(vendor)], check=True)
        subprocess.run(['git', '-C', str(vendor), 'checkout', MELO_COMMIT], check=True)
    # Avoid eagerly importing/downloading tokenizers for Japanese, Chinese, etc.
    # This application intentionally exposes Spanish only.
    (vendor / 'melo' / 'text' / 'cleaner.py').write_text('''from . import spanish
def clean_text(text, language):
    if language not in ("ES", "SP"):
        raise ValueError("Este estudio está configurado para español.")
    norm = spanish.text_normalize(text)
    phones, tones, word2ph = spanish.g2p(norm)
    return norm, phones, tones, word2ph
''', encoding='utf-8')
    init = vendor / 'melo' / 'text' / '__init__.py'
    original = init.read_text(encoding='utf-8')
    marker = 'def get_bert(norm_text, word2ph, language, device):'
    original = original[:original.index(marker)] + '''def get_bert(norm_text, word2ph, language, device):
    if language not in ("ES", "SP"):
        raise ValueError("Este estudio está configurado para español.")
    from .spanish_bert import get_bert_feature
    return get_bert_feature(norm_text, word2ph, device)
'''
    init.write_text(original, encoding='utf-8')
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--no-build-isolation', '-e', str(vendor)], check=True)
    print('Modelos de conversión y MeloTTS preparados. El modelo español se descarga en el primer uso.', flush=True)


if __name__ == '__main__':
    setup()
