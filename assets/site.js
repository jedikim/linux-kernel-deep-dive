/* 리눅스 커널 깊이 읽기 — 공용 스크립트: 테마, 목차 강조, 읽음 표시, 검색, 그림 확대 */
(function () {
  'use strict';
  var root = document.documentElement;
  var ROOT = document.body.getAttribute('data-root') || '';
  var PAGE = document.body.getAttribute('data-page') || '';
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };
  function $(s, el) { return (el || document).querySelector(s); }
  function $$(s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); }

  /* 테마 */
  var themeBtn = $('#theme-btn');
  function applyTheme(t) {
    if (t === 'light' || t === 'dark') root.setAttribute('data-theme', t); else root.removeAttribute('data-theme');
    if (themeBtn) themeBtn.textContent = t === 'dark' ? '밝게' : t === 'light' ? '어둡게' : '테마';
  }
  applyTheme(store.get('lkd-theme', ''));
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var cur = root.getAttribute('data-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    var next = cur === 'dark' ? 'light' : 'dark';
    store.set('lkd-theme', next); applyTheme(next);
  });

  /* 모바일 메뉴 */
  var menuBtn = $('#menu-btn');
  function closeNav() { document.body.classList.remove('nav-open'); var s = $('.scrim'); if (s) s.remove(); }
  if (menuBtn) menuBtn.addEventListener('click', function () {
    if (document.body.classList.toggle('nav-open')) {
      var s = document.createElement('div'); s.className = 'scrim'; s.addEventListener('click', closeNav); document.body.appendChild(s);
    } else closeNav();
  });
  var cur = $('.side nav a[aria-current=page]');
  if (cur && cur.scrollIntoView) { try { cur.scrollIntoView({ block: 'center' }); } catch (e) {} }

  /* 읽음 표시 */
  var read = store.get('lkd-read', {});
  function paintRead() {
    $$('.side li[data-ch]').forEach(function (li) { li.classList.toggle('is-read', !!read[li.getAttribute('data-ch')]); });
    $$('.card[data-ch]').forEach(function (c) { c.classList.toggle('is-read', !!read[c.getAttribute('data-ch')]); });
    var rb = $('#read-btn');
    if (rb) { var on = !!read[PAGE]; rb.setAttribute('aria-pressed', on ? 'true' : 'false'); rb.textContent = on ? '✓ 읽음' : '읽음으로 표시'; }
  }
  paintRead();
  var rb = $('#read-btn');
  if (rb) rb.addEventListener('click', function () { if (read[PAGE]) delete read[PAGE]; else read[PAGE] = 1; store.set('lkd-read', read); paintRead(); });

  /* 읽기 진행 선 + 오른쪽 목차 강조 */
  var line = $('.progress-line i');
  var tocLinks = $$('.toc a');
  var heads = tocLinks.map(function (a) { return document.getElementById(decodeURIComponent(a.getAttribute('href').slice(1))); });
  function onScroll() {
    var h = document.documentElement.scrollHeight - innerHeight;
    if (line) line.style.width = (h > 0 ? Math.min(100, scrollY / h * 100) : 0) + '%';
    if (!tocLinks.length) return;
    var idx = 0;
    for (var i = 0; i < heads.length; i++) { if (heads[i] && heads[i].getBoundingClientRect().top < 120) idx = i; }
    tocLinks.forEach(function (a, i) { a.classList.toggle('on', i === idx); });
  }
  addEventListener('scroll', onScroll, { passive: true }); onScroll();

  /* 코드 복사 */
  $$('article pre').forEach(function (pre) {
    var wrap = document.createElement('div'); wrap.className = 'code-wrap';
    pre.parentNode.insertBefore(wrap, pre); wrap.appendChild(pre);
    var b = document.createElement('button'); b.className = 'copy-btn'; b.type = 'button'; b.textContent = '복사';
    b.addEventListener('click', function () {
      var t = pre.innerText;
      if (navigator.clipboard) navigator.clipboard.writeText(t).then(function () { b.textContent = '복사됨'; setTimeout(function () { b.textContent = '복사'; }, 1200); });
    });
    wrap.appendChild(b);
  });

  /* 그림 확대 */
  function zoom(node) {
    var z = document.createElement('div'); z.className = 'zoom'; z.setAttribute('role', 'dialog'); z.setAttribute('aria-label', '그림 크게 보기');
    var inner = document.createElement('div'); inner.className = 'zoom-in';
    var c = node.cloneNode(true); c.removeAttribute('style'); inner.appendChild(c); z.appendChild(inner);
    function close() { z.remove(); removeEventListener('keydown', esc); }
    function esc(e) { if (e.key === 'Escape') close(); }
    z.addEventListener('click', close); addEventListener('keydown', esc);
    document.body.appendChild(z);
  }
  $$('figure.fig:not(.plain) .fig-body').forEach(function (b) {
    function open() { var s = $('svg', b); if (s) zoom(s); }
    b.addEventListener('click', open);
    b.addEventListener('keydown', function (e) { if (e.key === 'Enter') open(); });
  });

  /* 용어 사전·소스 색인 필터 */
  var gf = $('#gl-filter');
  if (gf) gf.addEventListener('input', function () {
    var q = gf.value.trim().toLowerCase();
    $$('.gl-item, .src-item').forEach(function (it) { it.hidden = q && it.getAttribute('data-k').indexOf(q) < 0; });
    $$('.gl-group').forEach(function (g) { g.hidden = !$$('.gl-item, .src-item', g).some(function (it) { return !it.hidden; }); });
  });

  /* 검색 */
  var searchEl = null, loaded = false, sel = 0, results = [];
  function loadIndex(cb) {
    if (loaded) return cb();
    var s = document.createElement('script'); s.src = ROOT + 'assets/search-index.js';
    s.onload = function () { loaded = true; cb(); }; s.onerror = function () { loaded = true; window.LKD_INDEX = []; cb(); };
    document.head.appendChild(s);
  }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function run(q) {
    var box = $('.search-res', searchEl);
    q = q.trim().toLowerCase();
    if (!q) { box.innerHTML = '<div class="search-empty">개념, 함수 이름, 소스 경로로 찾습니다. 예: 선점, __schedule, kernel/fork.c</div>'; results = []; return; }
    var toks = q.split(/\s+/);
    results = [];
    (window.LKD_INDEX || []).forEach(function (e) {
      var t = e.t.toLowerCase(), x = e.x.toLowerCase(), score = 0;
      for (var i = 0; i < toks.length; i++) {
        var k = toks[i], inT = t.indexOf(k) >= 0, inX = x.indexOf(k) >= 0;
        if (!inT && !inX) { score = 0; break; }
        score += (inT ? (t === k ? 40 : 14) : 0) + (inX ? 2 : 0) + (e.k === 'term' && inT ? 10 : 0);
      }
      if (score) results.push({ e: e, s: score, p: x.indexOf(toks[0]) });
    });
    results.sort(function (a, b) { return b.s - a.s; });
    results = results.slice(0, 30);
    if (!results.length) { box.innerHTML = '<div class="search-empty">찾지 못했습니다.</div>'; return; }
    box.innerHTML = results.map(function (r, i) {
      var e = r.e, snip = e.x;
      if (r.p > 40) snip = '…' + e.x.slice(r.p - 30);
      snip = snip.slice(0, 110);
      return '<a href="' + ROOT + e.u + '" class="' + (i === sel ? 'sel' : '') + '"><small>' + esc(e.c) + '</small><b>' + esc(e.t) + '</b><span>' + esc(snip) + '</span></a>';
    }).join('');
  }
  function openSearch() {
    if (searchEl) return;
    searchEl = document.createElement('div'); searchEl.className = 'search';
    searchEl.innerHTML = '<div class="search-box" role="dialog" aria-label="검색"><input type="search" placeholder="검색" aria-label="검색어"><div class="search-res"></div></div>';
    document.body.appendChild(searchEl);
    var inp = $('input', searchEl);
    searchEl.addEventListener('click', function (e) { if (e.target === searchEl) closeSearch(); });
    inp.addEventListener('input', function () { sel = 0; run(inp.value); });
    inp.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { sel = Math.min(sel + 1, results.length - 1); run(inp.value); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { sel = Math.max(sel - 1, 0); run(inp.value); e.preventDefault(); }
      else if (e.key === 'Enter' && results[sel]) { location.href = ROOT + results[sel].e.u; closeSearch(); }
    });
    loadIndex(function () { run(inp.value); });
    inp.focus();
  }
  function closeSearch() { if (searchEl) { searchEl.remove(); searchEl = null; } }
  $$('.search-open').forEach(function (b) { b.addEventListener('click', openSearch); });
  addEventListener('keydown', function (e) {
    var tag = (e.target.tagName || '').toLowerCase();
    if (e.key === 'Escape') { closeSearch(); closeNav(); }
    else if ((e.key === '/' || ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k')) && tag !== 'input' && tag !== 'textarea') { e.preventDefault(); openSearch(); }
  });
})();
