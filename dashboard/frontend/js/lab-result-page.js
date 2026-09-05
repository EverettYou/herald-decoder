(function () {
  const assetHref = (lab, path) => `/lab-assets/${encodeURIComponent(lab)}/${String(path).split('/').map(encodeURIComponent).join('/')}`;
  const icons = { artifact: 'fa-cubes', figure: 'fa-chart-line', note: 'fa-file-lines', paper: 'fa-file-pdf', code: 'fa-code' };
  const pythonKeywords = new Set('and as assert async await break class continue def del elif else except False finally for from global if import in is lambda None nonlocal not or pass raise return True try while with yield'.split(' '));

  function highlightPython(source, escapeHtml) {
    const token = /#[^\n]*|(?:'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")|\b[A-Za-z_]\w*\b|\b\d+(?:\.\d+)?\b/g;
    let cursor = 0;
    return String(source).replace(token, (match, offset) => {
      const before = escapeHtml(source.slice(cursor, offset));
      cursor = offset + match.length;
      const kind = match.startsWith('#') ? 'comment' : /^["']/.test(match) ? 'string' : /^\d/.test(match) ? 'number' : pythonKeywords.has(match) ? 'keyword' : '';
      return before + (kind ? `<span class="token-${kind}">${escapeHtml(match)}</span>` : escapeHtml(match));
    }) + escapeHtml(source.slice(cursor));
  }

  async function render(context) {
    const { api, go, query, escapeHtml, markdown, typeset } = context;
    const root = document.querySelector('#app');
    const labId = query().get('lab');
    const resultId = query().get('result');
    if (!labId || !resultId) return go('/labs');
    const data = await api(`/api/labs/${encodeURIComponent(labId)}`);
    const output = data.outputs?.find(item => item.id === resultId);
    if (!output) throw new Error('Research result not found');
    const href = assetHref(labId, output.asset_path);
    const icon = icons[output.kind] || 'fa-box-archive';
    document.title = `${output.title} · ${data.lab.title}`;
    root.innerHTML = `
      <div class="result-page-head">
        <a class="back" href="/lab?id=${encodeURIComponent(labId)}" data-result-nav>← ${escapeHtml(data.lab.title)}</a>
        <div class="result-page-heading">
          <div><p class="lab-overline">Research result · ${escapeHtml(output.kind)} / ${escapeHtml(output.format)}</p><h1>${escapeHtml(output.title)}</h1><p>${escapeHtml(output.summary)}</p></div>
          <a class="button secondary" href="${href}" target="_blank" rel="noreferrer"><i class="fa-solid fa-arrow-up-right-from-square" aria-hidden="true"></i> Open source</a>
        </div>
      </div>
      <section class="result-workspace result-workspace-${escapeHtml(output.format)}" aria-label="${escapeHtml(output.title)}">
        <div class="result-workspace-label"><span><i class="fa-solid ${icon}" aria-hidden="true"></i> ${escapeHtml(output.kind)}</span><code>${escapeHtml(output.path)}</code></div>
        <div id="result-content" class="result-content"><div class="document-loading">Loading result…</div></div>
      </section>`;
    document.querySelector('[data-result-nav]').addEventListener('click', event => { event.preventDefault(); go(event.currentTarget.getAttribute('href')); });
    const content = document.querySelector('#result-content');
    if (output.format === 'interactive') {
      content.innerHTML = `<iframe class="result-interactive-frame" title="${escapeHtml(output.title)}" src="${href}" scrolling="no"></iframe>`;
      const frame = content.querySelector('iframe');
      const fitInteractiveFrame = () => {
        const documentElement = frame.contentDocument?.documentElement;
        const body = frame.contentDocument?.body;
        if (!documentElement || !body) return;
        const height = Math.max(
          documentElement.scrollHeight, documentElement.offsetHeight,
          body.scrollHeight, body.offsetHeight
        );
        frame.style.height = `${height}px`;
      };
      frame.addEventListener('load', () => {
        fitInteractiveFrame();
        const observed = frame.contentDocument?.documentElement;
        if (observed && window.ResizeObserver) new ResizeObserver(fitInteractiveFrame).observe(observed);
      }, { once: true });
    } else if (['image', 'png', 'jpg', 'jpeg', 'svg', 'webp'].includes(String(output.format).toLowerCase())) {
      content.innerHTML = `<figure class="result-figure"><img src="${href}" alt="${escapeHtml(output.title)}"><figcaption>${escapeHtml(output.summary)}</figcaption></figure>`;
    } else {
      const response = await fetch(href);
      if (!response.ok) throw new Error('Could not load result content');
      const text = await response.text();
      content.innerHTML = output.format === 'markdown'
        ? `<article class="result-document rich-text">${markdown(text, { sourcePath: output.path })}</article>`
        : `<pre class="result-code"><code class="language-${escapeHtml(output.language || 'plain')}">${output.language === 'python' ? highlightPython(text, escapeHtml) : escapeHtml(text)}</code></pre>`;
      typeset(content);
    }
  }
  window.HeraldLabResultPage = { render };
})();
