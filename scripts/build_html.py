#!/usr/bin/env python3
"""Build a self-contained vocabulary page using only Python's standard library."""
import argparse
import hashlib
import json
import re
from pathlib import Path

FIELDS = ('term', 'meaning', 'ipa', 'sentence', 'translation')


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('输入必须是 JSON 对象')
    for name in ('title', 'deck_id'):
        if not isinstance(data.get(name), str) or not data[name].strip():
            raise ValueError(f'{name} 必须是非空字符串')
    cards = data.get('cards')
    if not isinstance(cards, list) or not cards or len(cards) > 500:
        raise ValueError('cards 必须包含 1–500 个词条')
    seen, ids = set(), set()
    clean = []
    for i, card in enumerate(cards, 1):
        if not isinstance(card, dict):
            raise ValueError(f'第 {i} 项不是对象')
        for field in FIELDS:
            if not isinstance(card.get(field), str) or not card[field].strip():
                raise ValueError(f'第 {i} 项缺少非空 {field}')
        row = {k: card[k].strip() for k in FIELDS}
        sentence = re.sub(r'\s+', ' ', row['sentence']).casefold()
        if sentence in seen:
            raise ValueError(f'第 {i} 项英文原句重复')
        seen.add(sentence)
        identity = row['term'].casefold() + '\n' + sentence
        row['id'] = hashlib.sha256(identity.encode()).hexdigest()[:20]
        if row['id'] in ids:
            raise ValueError('词条 ID 重复')
        ids.add(row['id'])
        clean.append(row)
    sources = data.get('sources', [])
    if not isinstance(sources, list) or any(not isinstance(s, str) for s in sources):
        raise ValueError('sources 必须是字符串数组')
    return {'title': data['title'], 'deck_id': data['deck_id'], 'cards': clean,
            'sources': sources, 'note': str(data.get('note', ''))}


def build(data, output):
    data = validate(data)
    template = (Path(__file__).resolve().parents[1] / 'assets' / 'study.html').read_text()
    # Never allow subtitle text to terminate the inert JSON script element.
    encoded = json.dumps(data, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    html = template.replace('__VOCAB_DATA__', encoded)
    output = Path(output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding='utf-8')
    return len(data['cards'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        count = build(json.loads(args.input.read_text(encoding='utf-8')), args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, f'生成失败：{error}\n')
    print(f'已生成 {args.output}（{count} 个词条）')
