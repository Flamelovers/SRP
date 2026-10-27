import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
from .vision import crop, ocr, match_name, match_sprite, combine


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def recognize(args):
    layout, names = load(args.layout), load(args.names)
    with Image.open(args.image) as im:
        image = im.convert('RGB')
    result = {'schema_version':'0.1', 'captured_at':None, 'processed_at':datetime.now(timezone.utc).isoformat(), 'image':str(args.image), 'image_size':list(image.size), 'sides':{}, 'warnings':[]}
    for side in ('player', 'opponent'):
        name_image = crop(image, layout['regions'][side+'_name'])
        sprite_image = crop(image, layout['regions'][side+'_sprite'])
        try:
            raw = ocr(name_image, args.lang)
        except Exception as exc:
            raw = ''
            result['warnings'].append(f'{side} OCR 不可用: {exc}')
        nc = match_name(raw, names)
        sc, warning = match_sprite(sprite_image, args.templates)
        if warning:
            result['warnings'].append(f'{side}: {warning}')
        species, reason = combine(nc, sc)
        result['sides'][side] = {'active':{'species':species, 'uncertainty':reason, 'ocr_text':raw, 'name_candidates':nc, 'sprite_candidates':sc, 'hp':None, 'status':None, 'moves':None}, 'team':None}
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output+'\n', encoding='utf-8')
    print(output)


def capture(args):
    import mss
    import mss.tools
    with mss.mss() as screen:
        shot = screen.grab(screen.monitors[args.monitor])
        mss.tools.to_png(shot.rgb, shot.size, output=args.output)
    print(f'已保存 {args.output}')


def evaluate(args):
    moves = load(args.state)['sides']['player']['active'].get('moves')
    if not moves:
        print('无法生成行动：可用招式尚未识别，需先实现招式识别和规则数据。')
    else:
        print(json.dumps({'candidates':[{'kind':'move','move':m} for m in moves], 'evaluation':None, 'reason':'尚未接入规则与模拟器'}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(required=True)
    p = sub.add_parser('capture'); p.add_argument('--output', default='frame.png'); p.add_argument('--monitor', type=int, default=1); p.set_defaults(func=capture)
    p = sub.add_parser('recognize'); p.add_argument('image'); p.add_argument('--layout', default='config/layout.json'); p.add_argument('--names', default='config/names.json'); p.add_argument('--templates', default='assets/templates'); p.add_argument('--lang', default='chi_sim+eng'); p.add_argument('--output'); p.set_defaults(func=recognize)
    p = sub.add_parser('evaluate'); p.add_argument('state'); p.set_defaults(func=evaluate)
    args = parser.parse_args(); args.func(args)


if __name__ == '__main__':
    main()
