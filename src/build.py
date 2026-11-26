#!/usr/bin/env python3
"""리눅스 커널 깊이 읽기 — 빌드 스크립트.

  python3 src/build.py            전체(모든 장 + 표지 + 용어 사전 + 소스 색인 + 검색 색인)
  python3 src/build.py ch06       해당 장의 HTML만 다시 만든다

원고는 src/content/chNN.md (pandoc Markdown), 그림은 src/fig/chNN/*.svg.
필요한 도구: pandoc, Python 3 + beautifulsoup4.
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
OUT_CH = ROOT / 'chapters'
BOOK = json.loads((SRC / 'book.json').read_text(encoding='utf-8'))
PARTS = {p['id']: p for p in BOOK['parts']}
PART_NO = {p['id']: i for i, p in enumerate(BOOK['parts'])}
CHAPTERS = BOOK['chapters']
CH = {c['id']: c for c in CHAPTERS}
PAGES = [p for p in BOOK.get('pages', []) if (SRC / 'content' / f'{p["id"]}.md').exists()]
DEFS = (SRC / 'defs.svg').read_text(encoding='utf-8')
KVER = BOOK['kernel']
KSRC = BOOK['source']

CALLOUTS = {
    'note': ('참고', 'i-book'),
    'warn': ('주의', 'i-warn'),
    'myth': ('흔한 오해', 'i-cross'),
    'old': ('예전 자료와 다른 점', 'i-clock'),
    'lab': ('직접 확인하기', 'i-terminal'),
    'design': ('설계 노트', 'i-layers'),
    'key': ('핵심', 'i-bolt'),
}
CODE_LABELS = {
    'c': 'C', 'cpp': 'C++', 'rust': 'Rust', 'asm': '어셈블리', 'nasm': '어셈블리', 'python': 'Python',
    'bash': '셸', 'sh': '셸', 'zsh': '셸', 'console': '터미널', 'diff': 'diff', 'makefile': 'Makefile',
    'kconfig': 'Kconfig', 'json': 'JSON', 'yaml': 'YAML', 'toml': 'TOML', 'dts': 'Devicetree',
    'bpftrace': 'bpftrace', 'text': '출력', 'email': '메일',
}
TAIL_IDS = {'summary', 'quiz', 'terms', 'more'}
FONTS = ('<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>'
         '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">'
         '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap">')
warnings = []
HISTORY = []   # 각 장의 변천사 상자에서 모은 항목


def warn(ch, msg):
    warnings.append(f'[{ch}] {msg}')


def ch_no(cid):
    return int(cid[2:])


def ch_label(cid):
    return f'{ch_no(cid)}장'


def esc(s):
    return html.escape(str(s), quote=True)


def icon(name):
    return f'<svg viewBox="0 0 48 48" aria-hidden="true"><use href="#{name}"/></svg>'


def pandoc(md_text):
    r = subprocess.run(
        ['pandoc', '-f', 'markdown-smart-implicit_figures-raw_tex+east_asian_line_breaks', '-t', 'html5',
         '--mathml', '--wrap=none', '--section-divs'],
        input=md_text.encode('utf-8'), capture_output=True)
    if r.returncode != 0:
        raise SystemExit('pandoc 실패: ' + r.stderr.decode('utf-8'))
    for line in r.stderr.decode('utf-8').splitlines():
        if line.strip():
            warnings.append('[pandoc] ' + line)
    return r.stdout.decode('utf-8')


def attr(node, name):
    return node.get('data-' + name) or node.get(name) or ''


def load_svg(cid, name):
    p = SRC / 'fig' / cid / name
    if not p.exists():
        return None
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'<\?xml[^>]*\?>', '', s)
    s = re.sub(r'<!DOCTYPE[^>]*>', '', s).strip()
    m = re.match(r'<svg\b([^>]*)>', s)
    if not m:
        return None
    a = re.sub(r'\s(width|height)="[^"]*"', '', m.group(1))
    if 'viewBox' not in a:
        warn(cid, f'{name}: viewBox 없음')
    if 'role=' not in a:
        a += ' role="img"'
    return '<svg' + a + '>' + s[m.end():]


def text_of(node):
    return re.sub(r'\s+', ' ', node.get_text(' ', strip=True))


def inner(node):
    return ''.join(str(c) for c in node.contents)


def src_url(path, line=''):
    return KSRC + path + (f'#L{line}' if line else '')


def render_body(cid, md_text, root='../'):
    """md → (html, toc, 검색 항목, 용어, 소스 인용, 통계)"""
    soup = BeautifulSoup(pandoc(md_text), 'html.parser')
    is_ch = cid in CH
    no = ch_no(cid) if is_ch else 0
    blobs = {}

    def stash(raw):
        key = f'@@BLOB{len(blobs)}@@'
        blobs[key] = raw
        return key

    # 그림
    k = 0
    for div in soup.select('div.fig'):
        k += 1
        name = attr(div, 'src')
        svg = load_svg(attr(div, 'from') or cid, name)
        if svg is not None and root != '../':
            svg = svg.replace('href="../', f'href="{root}')
        cap = re.sub(r'^<p>(.*)</p>$', r'\1', inner(div).strip(), flags=re.S)
        fid = 'fig-' + re.sub(r'\.svg$', '', name)
        plain = 'plain' in (div.get('class') or [])
        if svg is None:
            warn(cid, f'그림 파일 없음: {name}')
            body = f'<p><code>{esc(name)}</code></p>'
        else:
            if '<title' not in svg:
                svg = re.sub(r'(<svg\b[^>]*>)', lambda m: m.group(1) + f'<title>{esc(text_of(div))}</title>', svg, count=1)
            body = stash(svg)
        num = f'<b>그림 {no}-{k}</b>' if is_ch else ''
        tab = '' if plain else ' tabindex="0" title="눌러서 크게 보기"'
        fig = BeautifulSoup(
            f'<figure class="fig{" plain" if plain else ""}" id="{esc(fid)}"><div class="fig-body"{tab}>{body}</div>'
            f'<figcaption>{num}{cap}</figcaption></figure>', 'html.parser')
        div.replace_with(fig)

    # 상자류
    for cls, (label, ic) in CALLOUTS.items():
        for div in soup.select(f'div.{cls}'):
            title = attr(div, 'title')
            lab = f'{label} · {esc(title)}' if title else label
            for a in ('title', 'data-title'):
                if div.has_attr(a):
                    del div[a]
            div['class'] = ['callout', cls]
            div.insert(0, BeautifulSoup(f'<div class="co-h">{icon(ic)}{lab}</div>', 'html.parser'))
    for div in soup.select('div.goals'):
        div.insert(0, BeautifulSoup(f'<div class="co-h">{icon("i-search")}이 장에서 답하는 질문</div>', 'html.parser'))
    for div in soup.select('div.history'):
        title = attr(div, 'title') or '변천사'
        for a in ('title', 'data-title'):
            if div.has_attr(a):
                del div[a]
        div.insert(0, BeautifulSoup(f'<div class="co-h">{icon("i-branch")}{esc(title)}</div>', 'html.parser'))
        dl = div.find('dl')
        if not dl:
            warn(cid, '.history 안에 정의 목록(버전\\n:   설명)이 없음')
        elif is_ch:
            for dt in dl.find_all('dt'):
                dd = dt.find_next_sibling('dd')
                HISTORY.append({'when': text_of(dt), 'html': re.sub(r'^<p>(.*)</p>$', r'\1', inner(dd).strip(), flags=re.S) if dd else '', 'ch': cid})
    for div in soup.select('div.deep'):
        title = attr(div, 'title') or '더 깊이 보기'
        det = soup.new_tag('details')
        det['class'] = ['deep']
        summ = BeautifulSoup(f'<summary><small>더 깊이</small>{esc(title)}</summary>', 'html.parser')
        body = soup.new_tag('div')
        body['class'] = ['deep-body']
        for c in list(div.contents):
            body.append(c.extract())
        det.append(summ)
        det.append(body)
        div.replace_with(det)

    # 확인 문제
    qs = soup.select('div.q')
    for q in qs:
        ans = q.find('div', class_='a')
        body = soup.new_tag('div')
        body['class'] = ['q-body']
        for c in list(q.contents):
            if c is ans:
                continue
            body.append(c.extract())
        q.insert(0, body)
        if ans is None:
            warn(cid, '확인 문제에 정답(.a)이 없음: ' + text_of(q)[:30])
            continue
        det = soup.new_tag('details')
        det['class'] = ['a']
        summ = soup.new_tag('summary')
        summ.string = '답 보기'
        box = soup.new_tag('div')
        for c in list(ans.contents):
            box.append(c.extract())
        det.append(summ)
        det.append(box)
        ans.replace_with(det)
    if qs:
        wrap = soup.new_tag('div')
        wrap['class'] = ['quiz']
        qs[0].insert_before(wrap)
        for q in qs:
            wrap.append(q.extract())

    # 용어
    terms = []
    for div in soup.select('div.terms'):
        dl = div.find('dl')
        if not dl:
            warn(cid, '.terms 안에 정의 목록이 없음')
            continue
        dl['class'] = ['terms']
        for dt in dl.find_all('dt'):
            raw = text_of(dt)
            m = re.match(r'^(.*?)\s*[\(（]([^)）]*)[\)）]\s*$', raw)
            name, en = (m.group(1), m.group(2)) if m else (raw, '')
            dd = dt.find_next_sibling('dd')
            terms.append({'term': name, 'en': en, 'def': text_of(dd) if dd else '', 'ch': cid})
            dt.clear()
            dt.append(NavigableString(name))
            if en:
                sm = soup.new_tag('small')
                sm.string = en
                dt.append(sm)
        div.replace_with(dl.extract())

    # 표, 링크
    for t in soup.find_all('table'):
        w = soup.new_tag('div')
        w['class'] = ['table-wrap']
        t.wrap(w)
    for a in soup.find_all('a', href=True):
        if re.match(r'https?://', a['href']):
            a['target'] = '_blank'
            a['rel'] = 'noopener'
    for a in soup.select('pre a[aria-hidden]'):
        a.decompose()

    # 코드: 커널 소스 인용은 파일 경로와 링크를, 그 밖은 언어 이름표를 단다
    cites = []
    for pre in soup.find_all('pre'):
        outer = pre.parent if pre.parent.name == 'div' and 'sourceCode' in (pre.parent.get('class') or []) else pre
        file = attr(outer, 'file') or attr(pre, 'file')
        line = attr(outer, 'line') or attr(pre, 'line')
        name = attr(outer, 'name') or attr(pre, 'name')
        lang = next((c for c in (pre.get('class') or []) if c in CODE_LABELS), None)
        if not (file or name or lang):
            continue
        box = soup.new_tag('div')
        box['class'] = ['code-box'] + (['is-src'] if file else [])
        if file:
            sec = pre.find_parent('section', class_='level2')
            cites.append({'file': file, 'ch': cid, 'sec': sec.get('id', '') if sec else ''})
            head = (f'<div class="code-head"><a class="code-file" href="{esc(src_url(file, line))}" target="_blank" rel="noopener">'
                    f'{esc(file)}</a><span class="code-ver">v{esc(KVER)}</span></div>')
        elif name:
            head = f'<div class="code-head"><span class="code-file">{esc(name)}</span><span class="code-ver">{esc(CODE_LABELS.get(lang, ""))}</span></div>'
        else:
            head = f'<div class="code-head"><span class="code-lang">{esc(CODE_LABELS[lang])}</span></div>'
        outer.wrap(box)
        box.insert(0, BeautifulSoup(head, 'html.parser'))

    # 제목 번호·앵커·목차·검색
    toc, entries = [], []
    n = 0
    for sec in soup.select('section.level2'):
        h = sec.find('h2')
        sid = sec.get('id', '')
        title = text_of(h)
        if re.search(r'[^\x00-\x7f]', sid):
            warn(cid, f'h2에 영문 id를 지정하세요: "{title}"')
        if is_ch and sid not in TAIL_IDS:
            n += 1
            h.insert(0, BeautifulSoup(f'<span class="sec-n">{no}.{n}</span>', 'html.parser'))
        h.append(BeautifulSoup(f'<a class="anchor" href="#{esc(sid)}" aria-label="이 절의 링크">#</a>', 'html.parser'))
        toc.append((sid, title))
        where = f'{ch_label(cid)} · {CH[cid]["title"]}' if is_ch else next((p['title'] for p in PAGES if p['id'] == cid), '')
        if sid != 'more':
            entries.append({'u': f'chapters/{cid}.html#{sid}', 'c': where, 't': title, 'x': text_of(sec)[:2600], 'k': 'sec'})

    out = str(soup)
    for key, raw in blobs.items():
        out = out.replace(key, raw)
    plain = soup.get_text()
    if re.search(r'(^|\n)\s*:::', plain):
        warn(cid, '본문에 ":::" 가 그대로 남아 있음 — 상자 문법을 확인하세요')
    stats = {'figs': k, 'chars': len(plain), 'sections': n, 'quiz': len(qs), 'terms': len(terms), 'cites': len(cites)}
    return out, toc, entries, terms, cites, stats


def sidebar(active, root):
    parts = []
    for p in BOOK['parts']:
        items = []
        for c in CHAPTERS:
            if c['part'] != p['id']:
                continue
            cur = ' aria-current="page"' if c['id'] == active else ''
            items.append(
                f'<li data-ch="{c["id"]}"><a href="{root}chapters/{c["id"]}.html"{cur}><span class="n">{ch_no(c["id"]):02d}</span>'
                f'<span>{esc(c["title"])}</span><span class="done" aria-label="읽음">✓</span></a></li>')
        parts.append(f'<div class="side-part pc-{p["color"]}"><i></i>{PART_NO[p["id"]]}부 · {esc(p["title"])}</div><ol>{"".join(items)}</ol>')

    def cur_of(pid):
        return ' aria-current="page"' if active == pid else ''
    links = [('home', f'{root}index.html', '전체 지도'), ('timeline', f'{root}chapters/timeline.html', '버전 연표')]
    links += [(p['id'], f'{root}chapters/{p["id"]}.html', p['title']) for p in PAGES]
    links += [('sources', f'{root}chapters/sources.html', '소스 색인'), ('glossary', f'{root}chapters/glossary.html', '용어 사전')]
    link_html = ''.join(f'<a href="{u}"{cur_of(i)}>{esc(t)}</a>' for i, u, t in links)
    return f'''<aside class="side" id="side" aria-label="전체 목차">
<a class="brand" href="{root}index.html"><b>{esc(BOOK["title"])}</b><span>Linux v{esc(KVER)}</span></a>
<button class="side-search search-open" type="button">{icon("i-search").replace("<svg", '<svg width="16" height="16"')}검색<kbd>/</kbd></button>
<nav>{"".join(parts)}</nav>
<div class="side-links">{link_html}<a href="{esc(BOOK["repo"])}" target="_blank" rel="noopener">GitHub ↗</a></div>
</aside>'''


def site_footer():
    links = ''.join(f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(n)}</a>' for n, u in BOOK['links'])
    lic = BOOK['license']
    return (f'<footer class="site-foot"><p><b>{esc(BOOK["author"])}</b></p>'
            f'<p class="foot-links"><a href="{esc(BOOK["repo"])}" target="_blank" rel="noopener">GitHub</a>{links}</p>'
            f'<p class="foot-lic">글과 그림 <a href="{esc(lic["url"])}" target="_blank" rel="noopener license">{esc(lic["name"])}</a>'
            f' · 인용한 커널 소스 <a href="{esc(BOOK["source"])}COPYING" target="_blank" rel="noopener">GPL-2.0</a></p></footer>')


def page(title, body, page_id, root, crumb, toc=None, desc=''):
    toc_html = ''
    if toc:
        links = ''.join(f'<a href="#{esc(i)}">{esc(t)}</a>' for i, t in toc)
        toc_html = f'<nav class="toc" aria-label="이 장의 순서"><h2>이 장의 순서</h2>{links}</nav>'
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="{esc(BOOK["author"])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<link rel="license" href="{esc(BOOK["license"]["url"])}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%23a85d00'/%3E%3Cpath d='M10 7v18M22 7l-11 9.5L22 25' fill='none' stroke='white' stroke-width='3.4' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
<script>try{{var t=JSON.parse(localStorage.getItem('lkd-theme')||'""');if(t)document.documentElement.setAttribute('data-theme',t)}}catch(e){{}}</script>
{FONTS}
<link rel="stylesheet" href="{root}assets/site.css">
</head>
<body data-page="{esc(page_id)}" data-root="{root}">
{DEFS}
<a class="skip" href="#main">본문으로 건너뛰기</a>
{sidebar(page_id, root)}
<div class="shell">
<header class="top">
<button class="icon-btn menu-btn" id="menu-btn" type="button" aria-label="목차 열기">☰ 목차</button>
<div class="crumb">{crumb}</div>
<button class="icon-btn search-open" type="button">검색</button>
<button class="icon-btn" id="theme-btn" type="button">테마</button>
</header>
<div class="progress-line" aria-hidden="true"><i></i></div>
<main id="main" class="layout{' has-toc' if toc else ''}">
<article>
{body}
{site_footer()}
</article>
{toc_html}
</main>
</div>
<script src="{root}assets/site.js"></script>
</body>
</html>
'''


def chapter_page(cid):
    c = CH[cid]
    p = PARTS[c['part']]
    md = SRC / 'content' / f'{cid}.md'
    idx = [x['id'] for x in CHAPTERS].index(cid)
    prev_c = CHAPTERS[idx - 1] if idx > 0 else None
    next_c = CHAPTERS[idx + 1] if idx + 1 < len(CHAPTERS) else None
    stats, entries, terms, cites = None, [], [], []
    if md.exists():
        body, toc, entries, terms, cites, stats = render_body(cid, md.read_text(encoding='utf-8'))
    else:
        body, toc = '<div class="callout note"><p>준비 중입니다.</p></div>', []
    mins = max(5, round((stats['chars'] / 480 + stats['figs'] * 0.4) / 5) * 5) if stats else 0
    files = []
    for ct in cites:
        if ct['file'] not in files:
            files.append(ct['file'])
    file_html = ''
    if files:
        chips = ''.join(f'<a class="chip mono" href="{esc(src_url(f))}" target="_blank" rel="noopener">{esc(f)}</a>' for f in files[:8])
        file_html = f'<div class="ch-files"><span class="chip-label">읽는 소스</span>{chips}</div>'
    time_chip = f'<span class="chip">약 {mins}분</span>' if mins else ''
    head = f'''<header class="ch-head pc-{p["color"]}">
<div class="ch-kicker"><span class="ch-no">{ch_no(cid):02d}</span><span class="part">{PART_NO[p["id"]]}부 · {esc(p["title"])}</span></div>
<h1>{esc(c["title"])}</h1>
<p class="ch-sub">{esc(c["sub"])}</p>
<div class="ch-meta"><span class="chip ver">Linux v{esc(KVER)} 기준</span>{time_chip}</div>
{file_html}
</header>'''
    pv = (f'<a class="prev" href="{prev_c["id"]}.html"><small>← {ch_label(prev_c["id"])}</small><b>{esc(prev_c["title"])}</b></a>'
          if prev_c else '<span></span>')
    nx = (f'<a class="next" href="{next_c["id"]}.html"><small>{ch_label(next_c["id"])} →</small><b>{esc(next_c["title"])}</b></a>'
          if next_c else '<a class="next" href="../index.html"><small>끝 →</small><b>전체 지도</b></a>')
    foot = (f'<footer class="ch-foot"><button class="read-btn" id="read-btn" type="button" aria-pressed="false">읽음으로 표시</button>'
            f'<nav class="pager" aria-label="이전·다음 장">{pv}{nx}</nav></footer>')
    crumb = f'{PART_NO[p["id"]]}부 {esc(p["title"])} › <b>{ch_label(cid)} {esc(c["title"])}</b>'
    out = page(f'{c["title"]} — {BOOK["title"]}', head + body + foot, cid, '../', crumb, toc, c['sub'])
    OUT_CH.mkdir(exist_ok=True)
    (OUT_CH / f'{cid}.html').write_text(out, encoding='utf-8')
    return stats, entries, terms, cites


def home_page():
    md = (SRC / 'content' / 'home.md').read_text(encoding='utf-8')
    top = render_body('home', md, root='')[0]
    blocks = []
    for p in BOOK['parts']:
        cards = []
        for c in CHAPTERS:
            if c['part'] != p['id']:
                continue
            cards.append(
                f'<a class="card" href="chapters/{c["id"]}.html" data-ch="{c["id"]}">'
                f'<i class="cn">{ch_no(c["id"]):02d}</i><b>{esc(c["title"])}</b><span>{esc(c["sub"])}</span></a>')
        blocks.append(
            f'<section class="part-block pc-{p["color"]}" id="{p["id"]}"><div class="part-head"><span class="pn">{PART_NO[p["id"]]}부</span>'
            f'<h2>{esc(p["title"])}</h2><p>{esc(p["desc"])}</p></div><div class="cards">{"".join(cards)}</div></section>')
    body = top + ''.join(blocks)
    out = page(f'{BOOK["title"]} — {BOOK["subtitle"]}', body, 'home', '', '<b>전체 지도</b>', None, BOOK['subtitle'])
    (ROOT / 'index.html').write_text(out, encoding='utf-8')


def initial_of(s):
    ch = s[:1]
    if not ch:
        return '#'
    code = ord(ch)
    if 0xAC00 <= code <= 0xD7A3:
        return 'ㄱㄱㄴㄷㄷㄹㅁㅂㅂㅅㅅㅇㅈㅈㅊㅋㅌㅍㅎ'[(code - 0xAC00) // 588]
    if ch.isascii() and ch.isalpha():
        return ch.upper()
    return '#'


def glossary_page(terms):
    items, seen = [], set()
    for t in terms:
        name = t['term'].strip()
        if not name or (name, t['ch']) in seen:
            continue
        seen.add((name, t['ch']))
        items.append(t)
    items.sort(key=lambda t: (t['term'].lower(), t['ch']))
    groups = {}
    for t in items:
        groups.setdefault(initial_of(t['term']), []).append(t)
    order = sorted(groups, key=lambda g: (0 if 'ㄱ' <= g <= 'ㅎ' else 1 if g != '#' else 2, g))
    parts, entries = [], []
    for g in order:
        rows = []
        for t in groups[g]:
            link = f'<a href="{t["ch"]}.html#terms">{ch_label(t["ch"])} {esc(CH[t["ch"]]["title"])}</a>'
            en = f'<small>{esc(t["en"])}</small>' if t['en'] else ''
            k = esc((t['term'] + ' ' + t['en'] + ' ' + t['def']).lower())
            rows.append(f'<div class="gl-item" data-k="{k}"><b>{esc(t["term"])}</b>{en}{link}<p>{esc(t["def"])}</p></div>')
            entries.append({'u': f'chapters/{t["ch"]}.html#terms', 'c': f'용어 · {ch_label(t["ch"])}',
                            't': t['term'] + (f' ({t["en"]})' if t['en'] else ''), 'x': t['def'], 'k': 'term'})
        parts.append(f'<section class="gl-group"><h2 id="g-{esc(g)}">{esc(g)}</h2>{"".join(rows)}</section>')
    jump = ''.join(f'<a class="chip" href="#g-{esc(g)}">{esc(g)}</a>' for g in order)
    body = ('<header class="ch-head"><h1>용어 사전</h1></header>'
            '<input id="gl-filter" class="gl-filter" type="search" placeholder="찾기" aria-label="용어 거르기">'
            f'<div class="ch-meta" style="margin-bottom:8px">{jump}</div>' + ''.join(parts))
    (OUT_CH / 'glossary.html').write_text(page(f'용어 사전 — {BOOK["title"]}', body, 'glossary', '../', '<b>용어 사전</b>'), encoding='utf-8')
    return entries


def sources_page(cites):
    """본문이 인용한 커널 소스 파일 → 인용한 장."""
    by_file = {}
    for c in cites:
        by_file.setdefault(c['file'], [])
        if (c['ch'], c['sec']) not in by_file[c['file']]:
            by_file[c['file']].append((c['ch'], c['sec']))
    groups = {}
    for f in sorted(by_file):
        top = f.split('/')[0] if '/' in f else '.'
        if top in ('arch', 'include', 'drivers', 'Documentation', 'tools') and f.count('/') >= 2:
            top = '/'.join(f.split('/')[:2])
        groups.setdefault(top, []).append(f)
    parts, entries = [], []
    for g in sorted(groups):
        rows = []
        for f in groups[g]:
            where = ''.join(f'<a href="{ch}.html#{esc(sec)}">{ch_label(ch)}</a>' for ch, sec in by_file[f])
            rows.append(f'<div class="src-item" data-k="{esc(f.lower())}"><a class="mono" href="{esc(src_url(f))}" target="_blank" rel="noopener">{esc(f)}</a>'
                        f'<span class="src-where">{where}</span></div>')
            ch0, sec0 = by_file[f][0]
            entries.append({'u': f'chapters/{ch0}.html#{sec0}', 'c': '소스 · ' + ', '.join(ch_label(ch) for ch, _ in by_file[f]),
                            't': f, 'x': '', 'k': 'term'})
        parts.append(f'<section class="gl-group"><h2 id="s-{esc(g.replace("/", "-"))}">{esc(g)}/</h2>{"".join(rows)}</section>')
    body = (f'<header class="ch-head"><h1>소스 색인</h1><p class="ch-sub">본문이 인용한 Linux v{esc(KVER)} 소스 파일 {len(by_file)}개</p></header>'
            '<input id="gl-filter" class="gl-filter" type="search" placeholder="파일 경로로 찾기" aria-label="파일 거르기">' + ''.join(parts))
    (OUT_CH / 'sources.html').write_text(page(f'소스 색인 — {BOOK["title"]}', body, 'sources', '../', '<b>소스 색인</b>'), encoding='utf-8')
    return entries


def timeline_page():
    """각 장의 변천사를 버전순으로 합친 연표."""
    def parse(when):
        m = re.match(r'\s*v?(\d+(?:\.\d+)*)', when)
        ver = tuple(int(x) for x in m.group(1).split('.')) if m and '.' in m.group(1) else None
        y = re.search(r'(19|20)\d\d', when if ver is None else when[m.end():])
        return ver, (int(y.group(0)) if y else None)
    items = []
    year_of = {}
    for h in HISTORY:
        ver, year = parse(h['when'])
        if ver and year:
            year_of.setdefault(ver, year)
        items.append({**h, 'ver': ver, 'year': year})
    for it in items:
        if it['year'] is None and it['ver'] in year_of:
            it['year'] = year_of[it['ver']]
        if it['year'] is None:
            warn(it['ch'], f'변천사 항목에 연도가 없음: "{it["when"]}"')
    items.sort(key=lambda it: (it['year'] or 9999, it['ver'] or (0,), it['ch']))
    rows, entries, last = [], [], None
    for it in items:
        year = it['year']
        if year != last:
            rows.append(f'<h2 class="tl-year" id="y{year or 0}">{year or "연도 미상"}</h2>')
            last = year
        label = '.'.join(str(x) for x in it['ver']) if it['ver'] else ''
        pill = f'<span class="v">v{esc(label)}</span>' if label else '<span></span>'
        link = f'<a href="{it["ch"]}.html">{ch_label(it["ch"])} {esc(CH[it["ch"]]["title"])}</a>'
        rows.append(f'<div class="tl-item">{pill}<div class="tl-body"><p>{it["html"]}</p>{link}</div></div>')
        plain = BeautifulSoup(it['html'], 'html.parser').get_text(' ', strip=True)
        entries.append({'u': f'chapters/timeline.html#y{year or 0}', 'c': f'연표 · {year or ""}', 't': (f'v{label} ' if label else '') + plain[:60], 'x': plain, 'k': 'sec'})
    body = (f'<header class="ch-head"><h1>버전 연표</h1><p class="ch-sub">본문이 다룬 변화를 버전순으로 모았습니다.</p></header>'
            + ''.join(rows))
    (OUT_CH / 'timeline.html').write_text(page(f'버전 연표 — {BOOK["title"]}', body, 'timeline', '../', '<b>버전 연표</b>'), encoding='utf-8')
    return entries


def extra_page(p):
    pid, title = p['id'], p['title']
    body, toc, entries, _, _, _ = render_body(pid, (SRC / 'content' / f'{pid}.md').read_text(encoding='utf-8'))
    head = f'<header class="ch-head"><h1>{esc(title)}</h1></header>'
    (OUT_CH / f'{pid}.html').write_text(page(f'{title} — {BOOK["title"]}', head + body, pid, '../', f'<b>{esc(title)}</b>', toc, title), encoding='utf-8')
    return entries


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    targets = args or [c['id'] for c in CHAPTERS]
    all_entries, all_terms, all_cites = [], [], []
    for cid in targets:
        if cid not in CH:
            raise SystemExit(f'모르는 장: {cid}')
        stats, entries, terms, cites = chapter_page(cid)
        all_entries += entries
        all_terms += terms
        all_cites += cites
        if stats:
            print(f'{cid}  절 {stats["sections"]:>2} · 그림 {stats["figs"]:>2} · 소스 인용 {stats["cites"]:>2} · 문제 {stats["quiz"]} · 용어 {stats["terms"]:>2} · 글자 {stats["chars"]:>6}')
        else:
            print(f'{cid}  (원고 없음)')
    if not args:
        home_page()
        all_entries += glossary_page(all_terms)
        all_entries += sources_page(all_cites)
        all_entries += timeline_page()
        for p in PAGES:
            all_entries += extra_page(p)
        (ROOT / 'assets' / 'search-index.js').write_text(
            'window.LKD_INDEX=' + json.dumps(all_entries, ensure_ascii=False, separators=(',', ':')) + ';', encoding='utf-8')
        print(f'index.html · glossary · sources · timeline({len(HISTORY)}) · {" · ".join(p["id"] for p in PAGES)} · search-index.js ({len(all_entries)}항목)')
    if warnings:
        print('\n경고 ' + str(len(warnings)) + '건:')
        for w in warnings:
            print('  ' + w)


if __name__ == '__main__':
    main()
