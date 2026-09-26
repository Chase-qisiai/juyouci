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
        answers = card.get('answers', [row['term']])
        if not isinstance(answers, list) or not answers or any(not isinstance(a, str) or not a.strip() for a in answers):
            raise ValueError(f'第 {i} 项 answers 必须是非空字符串数组')
        row['answers'] = list(dict.fromkeys(a.strip() for a in answers))
        targets = card.get('targets', [row['term']])
        if not isinstance(targets, list) or not targets or any(not isinstance(t, str) or not t.strip() for t in targets):
            raise ValueError(f'第 {i} 项 targets 必须是非空字符串数组')
        spans = []
        for target in targets:
            pattern = r'(?<!\w)' + re.escape(target) + r'(?!\w)'
            matches = list(re.finditer(pattern, row['sentence'], re.IGNORECASE))
            if not matches:
                raise ValueError(f'第 {i} 项目标 {target!r} 未出现在原句中；请填写原句中的实际词形 targets')
            spans.extend((m.start(), m.end()) for m in matches)
        spans = sorted(set(spans))
        if any(a[1] > z[0] for a, z in zip(spans, spans[1:])):
            raise ValueError(f'第 {i} 项 targets 重叠')
        # JavaScript indexes UTF-16 code units, not Python Unicode characters.
        offset = lambda n: len(row['sentence'][:n].encode('utf-16-le')) // 2
        row['target_spans'] = [[offset(a), offset(z)] for a, z in spans]
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
