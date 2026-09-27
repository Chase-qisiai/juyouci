#!/usr/bin/env python3
"""Create the reusable Juyouci HTML page or merge a vocabulary pack into it."""
import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path

FIELDS = ('term', 'meaning', 'ipa', 'sentence', 'translation')
LIBRARY_SCHEMA = 1


def safe_json(value):
    return (json.dumps(value, ensure_ascii=False)
            .replace('&', r'\u0026').replace('<', r'\u003c').replace('>', r'\u003e')
            .replace('\u2028', r'\u2028').replace('\u2029', r'\u2029'))


def validate(data):
    """Normalize one episode vocabulary pack and calculate browser-ready fields."""
    if not isinstance(data, dict):
        raise ValueError('输入必须是 JSON 对象')
    for name in ('title', 'deck_id'):
        if not isinstance(data.get(name), str) or not data[name].strip():
            raise ValueError(f'{name} 必须是非空字符串')
    cards = data.get('cards')
    if not isinstance(cards, list) or not cards or len(cards) > 500:
        raise ValueError('cards 必须包含 1–500 个词条')

    seen, ids, clean = set(), set(), []
    for i, card in enumerate(cards, 1):
        if not isinstance(card, dict):
            raise ValueError(f'第 {i} 项不是对象')
        for field in FIELDS:
            if not isinstance(card.get(field), str) or not card[field].strip():
                raise ValueError(f'第 {i} 项缺少非空 {field}')
        row = {key: card[key].strip() for key in FIELDS}
        answers = card.get('answers', [row['term']])
        if not isinstance(answers, list) or not answers or any(not isinstance(a, str) or not a.strip() for a in answers):
            raise ValueError(f'第 {i} 项 answers 必须是非空字符串数组')
        row['answers'] = list(dict.fromkeys(a.strip() for a in answers))
        targets = card.get('targets', [row['term']])
        if not isinstance(targets, list) or not targets or any(not isinstance(t, str) or not t.strip() for t in targets):
            raise ValueError(f'第 {i} 项 targets 必须是非空字符串数组')
        row['targets'] = list(dict.fromkeys(t.strip() for t in targets))

        spans = []
        for target in row['targets']:
            pattern = r'(?<!\w)' + re.escape(target) + r'(?!\w)'
            matches = list(re.finditer(pattern, row['sentence'], re.IGNORECASE))
            if not matches:
                raise ValueError(f'第 {i} 项目标 {target!r} 未出现在原句中；请填写原句中的实际词形 targets')
            spans.extend((match.start(), match.end()) for match in matches)
        spans = sorted(set(spans))
        if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
            raise ValueError(f'第 {i} 项 targets 重叠')
        # JavaScript indexes UTF-16 code units, not Python Unicode characters.
        offset = lambda position: len(row['sentence'][:position].encode('utf-16-le')) // 2
        row['target_spans'] = [[offset(start), offset(end)] for start, end in spans]

        normalized_sentence = re.sub(r'\s+', ' ', row['sentence']).casefold()
        if normalized_sentence in seen:
            raise ValueError(f'第 {i} 项英文原句重复')
        seen.add(normalized_sentence)
        identity = row['term'].casefold() + '\n' + normalized_sentence
        row['id'] = hashlib.sha256(identity.encode()).hexdigest()[:20]
        if row['id'] in ids:
            raise ValueError('词条 ID 重复')
        ids.add(row['id'])
        clean.append(row)

    sources = data.get('sources', [])
    if not isinstance(sources, list) or any(not isinstance(source, str) for source in sources):
        raise ValueError('sources 必须是字符串数组')
    return {
        'title': data['title'].strip(),
        'deck_id': data['deck_id'].strip(),
        'cards': clean,
        'sources': sources,
        'note': str(data.get('note', '')),
    }


def library_for(deck):
    return {'schema_version': LIBRARY_SCHEMA, 'decks': [deck]}


def find_data_script(html, script_id):
    pattern = re.compile(
        r'<script\b(?=[^>]*\bid=["\']' + re.escape(script_id) +
        r'["\'])(?=[^>]*\btype=["\']application/json["\'])[^>]*>(.*?)</script\s*>',
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(html)
    return match, pattern


def recover_targets_from_spans(card):
    """Recover target text from a previous generated page's UTF-16 offsets."""
    spans = card.get('target_spans')
    sentence = card.get('sentence')
    if not isinstance(spans, list) or not isinstance(sentence, str):
        return None
    offsets = {0: 0}
    units = 0
    for index, char in enumerate(sentence, 1):
        units += len(char.encode('utf-16-le')) // 2
        offsets[units] = index
    recovered = []
    for span in spans:
        if (not isinstance(span, list) or len(span) != 2 or
                span[0] not in offsets or span[1] not in offsets or span[0] >= span[1]):
            return None
        recovered.append(sentence[offsets[span[0]]:offsets[span[1]]])
    return recovered or None


def existing_library(html):
    match, pattern = find_data_script(html, 'vocab-library')
    if match:
        library = json.loads(match.group(1))
        if not isinstance(library, dict) or library.get('schema_version') != LIBRARY_SCHEMA or not isinstance(library.get('decks'), list):
            raise ValueError('通用学习器中的词库格式不受支持')
        decks = [validate(deck) for deck in library['decks']]
        if not decks:
            raise ValueError('通用学习器中没有有效词库')
        return {'schema_version': LIBRARY_SCHEMA, 'decks': decks}, pattern, match

    # Upgrade the previous single-deck file without losing its vocabulary.
    match, pattern = find_data_script(html, 'vocab-data')
    if match:
        legacy_deck = json.loads(match.group(1))
        for card in legacy_deck.get('cards', []):
            if isinstance(card, dict) and 'targets' not in card:
                recovered = recover_targets_from_spans(card)
                if recovered:
                    card['targets'] = recovered
        deck = validate(legacy_deck)
        return library_for(deck), pattern, match
    raise ValueError('目标文件不是剧有词学习器；请检查母版路径或先生成通用学习器')


def render_library(template, library):
    placeholder = '__VOCAB_LIBRARY__'
    if placeholder not in template:
        raise ValueError(f'页面模板缺少 {placeholder} 占位符')
    return template.replace(placeholder, safe_json(library), 1)


def build(data, output):
    """Create a master page or merge/replace a deck while reusing the generic app template."""
    deck = validate(data)
    output = Path(output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)

    if output.exists():
        html = output.read_text(encoding='utf-8')
        library, _, _ = existing_library(html)
        decks = library['decks']
        index = next((i for i, current in enumerate(decks) if current['deck_id'] == deck['deck_id']), None)
        if index is None:
            decks.append(deck)
        else:
            # Replacing a deck preserves progress for unchanged cards because card IDs are stable.
            decks[index] = deck
        library = {'schema_version': LIBRARY_SCHEMA, 'decks': decks}
    else:
        library = library_for(deck)

    template = (Path(__file__).resolve().parents[1] / 'assets' / 'study.html').read_text(encoding='utf-8')
    # Reuse the same generic app shell each time; only the embedded deck library changes.
    html = render_library(template, library)

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=output.parent,
                                         prefix=f'.{output.name}.', suffix='.tmp', delete=False) as temp:
            temp.write(html)
            temp_path = Path(temp.name)
        temp_path.replace(output)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()
    return len(deck['cards']), output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='单集 UTF-8 词库 JSON；作为合并源数据保留于任务临时目录')
    parser.add_argument('output', type=Path, help='通用学习器 HTML 路径；存在时自动添加/更新该集词库')
    args = parser.parse_args()
    try:
        count, path = build(json.loads(args.input.read_text(encoding='utf-8')), args.output)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        parser.exit(1, f'生成失败：{error}\n')
    print(f'已更新 {path}（本集 {count} 个词条）')
