import re
from difflib import SequenceMatcher
from pathlib import Path


def normalize(value):
    return re.sub(r'[^\w\u4e00-\u9fff]', '', value.casefold())


def match_name(text, names, threshold=0.75):
    query = normalize(text)
    if not query:
        return []
    found = []
    for species, aliases in names.items():
        score = max(SequenceMatcher(None, query, normalize(a)).ratio() for a in [species, *aliases])
        if score >= threshold:
            found.append({'species': species, 'score': round(score, 3), 'source': 'ocr'})
    return sorted(found, key=lambda x: x['score'], reverse=True)[:3]


def crop(image, rect):
    x, y, w, h = rect
    if min(x, y) < 0 or min(w, h) <= 0 or x+w > image.width or y+h > image.height:
        raise ValueError(f'区域 {rect} 超出图片 {image.size} 或无效')
    return image.crop((x, y, x+w, y+h))


def ocr(image, lang):
    import pytesseract
    from PIL import ImageOps
    gray = ImageOps.grayscale(image).resize((image.width*3, image.height*3))
    return pytesseract.image_to_string(gray, lang=lang, config='--psm 7').strip()


def match_sprite(image, root, threshold=0.65):
    import cv2
    import numpy as np
    from PIL import Image
    files = [p for p in Path(root).glob('*/*') if p.suffix.lower() in ('.png', '.jpg', '.jpeg')]
    if not files:
        return [], '模板库为空，头像匹配不可用'
    source = np.asarray(image.convert('RGB').resize((64, 64)), dtype=np.uint8)
    scores = {}
    for path in files:
        try:
            with Image.open(path) as im:
                template = np.asarray(im.convert('RGB').resize((64, 64)), dtype=np.uint8)
        except (OSError, ValueError):
            continue
        score = float(cv2.matchTemplate(source, template, cv2.TM_CCOEFF_NORMED)[0, 0])
        if np.isfinite(score):
            scores[path.parent.name] = max(scores.get(path.parent.name, -1), score)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ([{'species': s, 'score': round(v, 3), 'source': 'sprite'} for s, v in ranked if v >= threshold][:3], None)


def combine(names, sprites):
    if names and sprites and names[0]['species'] != sprites[0]['species']:
        return None, '名称与图像识别冲突'
    pool = names or sprites
    if not pool:
        return None, '未识别'
    if len(pool) > 1 and pool[0]['score'] - pool[1]['score'] < 0.1:
        return None, '候选分数接近'
    return pool[0]['species'], None
