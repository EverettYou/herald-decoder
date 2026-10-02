(function () {
  const ICONS = {
    project: 'fa-compass',
    index: 'fa-map',
    concept: 'fa-lightbulb',
    method: 'fa-screwdriver-wrench',
    model: 'fa-cubes',
    implementation: 'fa-code',
    reference: 'fa-file-lines',
    evidence: 'fa-chart-line',
    note: 'fa-note-sticky'
  };

  function resultRow(page, escapeHtml) {
    const type = page.page_type || 'note';
    return `
      <a class="wiki-page-search-result" href="/wiki?page=${encodeURIComponent(page.id)}" data-wiki-result>
        <span class="wiki-page-search-result-icon" aria-hidden="true">
          <i class="fa-solid ${ICONS[type] || ICONS.note}"></i>
        </span>
        <span class="wiki-page-search-result-copy">
          <strong>${escapeHtml(page.title)}</strong>
        </span>
        <span class="wiki-page-search-result-type">${escapeHtml(type)}</span>
      </a>`;
  }

  function pageMetadata(meta, path, escapeHtml) {
    const type = meta.page_type || 'note';
    const status = meta.status || 'active';
    const topics = meta.topics || [];
    return `
      <header class="wiki-page-meta" aria-label="Page information">
        <div class="wiki-page-path">
          <span>File</span>
          <code>${escapeHtml(path)}</code>
        </div>
        <div class="wiki-page-meta-row">
          <span class="wiki-page-meta-label">Types</span>
          <span class="wiki-page-meta-chip"><i class="fa-solid ${ICONS[type] || ICONS.note}" aria-hidden="true"></i>${escapeHtml(type)}</span>
          <span class="wiki-page-meta-chip">${escapeHtml(status)}</span>
        </div>
        <div class="wiki-page-meta-row wiki-page-keywords">
          <span class="wiki-page-meta-label">Keywords</span>
          <div class="topic-row">${topics.length ? topics.map(topic => `<span>${escapeHtml(topic)}</span>`).join('') : '<span>Unclassified</span>'}</div>
        </div>
      </header>`;
  }

  async function render({ api, go, query, escapeHtml, markdown, typeset }) {
    const selected = query().get('page') || 'thesis';
    const [catalog, page] = await Promise.all([
      api('/api/wiki'),
      api(`/api/wiki/page/${encodeURIComponent(selected)}`)
    ]);
    const root = document.querySelector('#app');
    const pageById = new Map(catalog.pages.map(item => [item.id, item]));
    const meta = page.page || {};

    root.innerHTML = `
      <section class="wiki-head">
        <div>
          <p class="eyebrow">Project knowledge</p>
          <h1>Research Wiki</h1>
          <p>Knowledge base for the project’s concepts, methods and evolving research understanding.</p>
        </div>
        <a class="button secondary" href="/" data-wiki-nav><i class="fa-solid fa-circle-nodes" aria-hidden="true"></i> View knowledge graph</a>
      </section>
      <div class="wiki-page-shell">
        <section class="wiki-searchbar wiki-page-search" aria-label="Search the project Wiki">
          <div class="search-control">
            <i class="fa-solid fa-magnifying-glass search-icon" aria-hidden="true"></i>
            <input id="wiki-search" type="search" placeholder="Search concepts, methods, claims, or describe what you need" aria-label="Search project knowledge" autocomplete="off">
            <button id="wiki-clear" class="search-clear" type="button" aria-label="Clear Wiki search"><i class="fa-solid fa-xmark" aria-hidden="true"></i></button>
          </div>
          <div id="wiki-page-search-results" class="wiki-page-search-results" hidden></div>
        </section>
        <article id="wiki-document" class="document-panel wiki-page-document">
          ${pageMetadata(meta, page.path, escapeHtml)}
          <div class="wiki-page-reading rich-text">${markdown(page.content, { sourcePath: page.path })}</div>
        </article>
      </div>`;

    const input = root.querySelector('#wiki-search');
    const results = root.querySelector('#wiki-page-search-results');
    const paintResults = state => {
      if (!state.query) {
        results.hidden = true;
        results.innerHTML = '';
        return;
      }
      if (state.mode === 'pending' || state.mode === 'refining') {
        results.innerHTML = `<p class="wiki-page-search-status">${state.mode === 'refining' ? 'Refining natural-language query…' : 'Searching project knowledge…'}</p>`;
      } else if (state.mode === 'unavailable') {
        results.innerHTML = '<p class="wiki-page-search-status">Search is temporarily unavailable.</p>';
      } else {
        const pages = state.results.map(result => pageById.get(result.entity_id)).filter(Boolean).slice(0, 10);
        results.innerHTML = pages.length
          ? pages.map(item => resultRow(item, escapeHtml)).join('')
          : '<p class="wiki-page-search-status">No matching Wiki pages.</p>';
      }
      results.hidden = false;
    };

    window.HeraldSearch.bind({
      scope: 'wiki',
      input,
      clear: root.querySelector('#wiki-clear'),
      limit: 20,
      onUpdate: paintResults
    }).run();

    results.addEventListener('click', event => {
      const link = event.target.closest('[data-wiki-result]');
      if (!link) return;
      event.preventDefault();
      go(link.getAttribute('href'));
    });
    input.addEventListener('keydown', event => {
      if (event.key !== 'Escape') return;
      input.value = '';
      results.hidden = true;
      results.innerHTML = '';
      input.blur();
    });
    input.addEventListener('focus', () => {
      if (input.value.trim() && results.innerHTML) results.hidden = false;
    });
    root.onclick = event => {
      if (!event.target.closest('.wiki-page-search')) results.hidden = true;
    };
    root.querySelector('[data-wiki-nav]').addEventListener('click', event => {
      event.preventDefault();
      go('/');
    });
    root.querySelectorAll('.wiki-page-reading a[href^="/wiki?page="]').forEach(link => {
      link.addEventListener('click', event => {
        event.preventDefault();
        go(link.getAttribute('href'));
      });
    });
    typeset(root.querySelector('#wiki-document'));
  }

  window.HeraldWikiPage = { render };
})();
