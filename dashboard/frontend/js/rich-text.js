(function () {
  const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, character => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#039;',
    '"': '&quot;'
  })[character]);

  function renderWikiLinks(source) {
    return String(source).replace(
      /(^|[^\\])\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]/g,
      (match, prefix, rawTarget, rawLabel) => {
        const target = rawTarget.trim().replace(/\.md$/, '');
        const label = (rawLabel || rawTarget).trim();
        if (!/^[a-z0-9][a-z0-9/-]*$/i.test(target) || !label) return match;
        return `${prefix}[${label}](/wiki?page=${encodeURIComponent(target)})`;
      }
    );
  }

  function resolveProjectHref(href, sourcePath = '') {
    const rawHref = String(href || '');
    if (!sourcePath || !rawHref || rawHref.startsWith('#') || /^(?:[a-z][a-z0-9+.-]*:|\/\/|\/)/i.test(rawHref)) return null;
    let parsed;
    try {
      const base = `https://herald.local/${String(sourcePath).replace(/[^/]*$/, '')}`;
      parsed = new URL(rawHref, base);
    } catch {
      return null;
    }
    const path = decodeURIComponent(parsed.pathname).replace(/^\/+/, '');
    const parts = path.split('/');
    if (!path || parts.includes('..') || !['labs', 'wiki', 'models', 'src'].includes(parts[0])) return null;
    const fragment = parsed.hash || '';
    if (/\.md$/i.test(path)) {
      if (path.startsWith('wiki/')) return `/wiki?page=${encodeURIComponent(path.slice(5, -3))}${fragment}`;
      return `/document?path=${encodeURIComponent(path)}${fragment}`;
    }
    if (/\.(?:py|cc|cpp|c|h|hpp|js|ts|json|ya?ml|toml|ini|cfg|txt|rst|cmake|bazel|bzl|sh|csv)$/i.test(path)) {
      return `/document?path=${encodeURIComponent(path)}${fragment}`;
    }
    const labAsset = path.match(/^labs\/([^/]+)\/(figures|results)\/(.+)$/);
    if (labAsset) return `/lab-assets/${encodeURIComponent(labAsset[1])}/${labAsset[2]}/${labAsset[3].split('/').map(encodeURIComponent).join('/')}${fragment}`;
    return null;
  }

  function protectMath(source) {
    let prefix = 'HERALDMATHPLACEHOLDER';
    while (source.includes(prefix)) prefix += 'X';
    const tokens = [];
    const stash = math => {
      const token = `${prefix}${tokens.length}END`;
      tokens.push({ token, math });
      return token;
    };

    let protectedSource = source
      .replace(/\$\$[\s\S]*?\$\$/g, stash)
      .replace(/\\\[[\s\S]*?\\\]/g, stash)
      .replace(/\\\([\s\S]*?\\\)/g, stash);

    protectedSource = protectedSource.replace(
      /(^|[^\\$])\$([^\n$]+?)\$/gm,
      (match, leading, body) => `${leading}${stash(`$${body}$`)}`
    );
    return { source: protectedSource, tokens };
  }

  function restoreMathTokens(value, tokens) {
    return tokens.reduce(
      (result, item) => result.split(item.token).join(escapeHtml(item.math)),
      value
    );
  }

  function renderRichText(value = '', inline = false, options = {}) {
    const source = renderWikiLinks(String(value).replace(/^---\n[\s\S]*?\n---\n?/, ''));
    const protectedMath = protectMath(source);

    if (!window.marked || !window.DOMPurify) {
      const safe = restoreMathTokens(escapeHtml(protectedMath.source), protectedMath.tokens);
      return inline
        ? safe
        : `<p>${safe.replace(/\n{2,}/g, '</p><p>').replace(/\n/g, '<br>')}</p>`;
    }

    const rendered = inline
      ? window.marked.parseInline(protectedMath.source, { gfm: true })
      : window.marked.parse(protectedMath.source, { gfm: true, breaks: false });
    const sanitized = window.DOMPurify.sanitize(rendered, { USE_PROFILES: { html: true } });
    const template = document.createElement('template');
    template.innerHTML = restoreMathTokens(sanitized, protectedMath.tokens);
    template.content.querySelectorAll('a[href]').forEach(link => {
      const href = link.getAttribute('href') || '';
      const paper = href.match(/(?:\.\.\/)+references\/([^/]+)\/paper\.pdf/);
      if (paper) link.setAttribute('href', `/reference?id=${paper[1]}`);
      const projectHref = resolveProjectHref(href, options.sourcePath);
      if (projectHref) link.setAttribute('href', projectHref);
      if (/^https?:/.test(href)) {
        link.target = '_blank';
        link.rel = 'noreferrer';
      }
    });
    template.content.querySelectorAll('img[src]').forEach(image => {
      const projectHref = resolveProjectHref(image.getAttribute('src') || '', options.sourcePath);
      if (projectHref) image.setAttribute('src', projectHref);
    });
    return template.innerHTML;
  }

  function typeset(element) {
    if (!element || !window.renderMathInElement) return;
    window.renderMathInElement(element, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '\\[', right: '\\]', display: true },
        { left: '\\(', right: '\\)', display: false },
        { left: '$', right: '$', display: false }
      ],
      throwOnError: false,
      ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
    });
  }

  window.HeraldRichText = {
    block: (value, options) => renderRichText(value, false, options),
    inline: (value, options) => renderRichText(value, true, options),
    typeset,
    testing: { protectMath, restoreMathTokens, renderWikiLinks, resolveProjectHref }
  };
})();
