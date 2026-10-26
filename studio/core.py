"""Validation and text splitting, independent of model dependencies."""
import re
import unicodedata


def split_text(text, limit=320):
    text = unicodedata.normalize('NFC', text).replace('\r\n', '\n').strip()
    if not text:
        raise ValueError('Escribí o cargá el texto que querés narrar.')
    if len(text) > 60000:
        raise ValueError('El máximo por trabajo es de 60.000 caracteres.')
    chunks = []
    for paragraph in re.split(r'\n\s*\n', text):
        paragraph = re.sub(r'\s+', ' ', paragraph).strip()
        words = paragraph.split(' ')
        current = ''
        for word in words:
            if len(word) > limit:
                raise ValueError('Hay una palabra demasiado larga. Revisá el texto.')
            if current and len(current) + len(word) + 1 > limit:
                chunks.append((current, 0.18))
                current = word
            else:
                current = f'{current} {word}'.strip()
            if len(current) >= limit // 2 and re.search(r'[.!?…]["»”\)]?$', current):
                chunks.append((current, 0.25))
                current = ''
        if current:
            chunks.append((current, 0.55))
        elif chunks:
            chunks[-1] = (chunks[-1][0], 0.55)
    return chunks


def validate_speed(value):
    try:
        speed = float(value)
    except (ValueError, TypeError):
        raise ValueError('Indicá una velocidad válida.') from None
    if not 0.75 <= speed <= 1.2:
        raise ValueError('La velocidad debe estar entre 75% y 120%.')
    return speed
