(function () {
  const size = bytes => bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1048576).toFixed(1)} MB`;
  const title = path => String(path).split('/').pop() || 'Document';

  async function render(context) {
    const { api, go, query, escapeHtml, markdown, typeset } = context;
    const path = query().get('path') || '';
    if (!path) return go('/labs');
    const file = await api(`/api/documents/file?path=${encodeURIComponent(path)}`);
    document.title = `${title(file.path)} · Herald Decoder`;
    const root = document.querySelector('#app');
    root.innerHTML = `
      <a class="back" href="/labs" data-document-back>← Labs</a>
      <section class="project-document-shell">
        <header class="project-document-head">
          <div><p class="eyebrow">Project file</p><h1>${escapeHtml(title(file.path))}</h1><code>${escapeHtml(file.path)}</code></div>
          <small>${escapeHtml(file.kind)} · ${size(file.size)}</small>
        </header>
        <div class="repo-tabs" role="tablist">
          ${file.kind === 'markdown' ? '<button type="button" class="selected" data-document-mode="preview">Preview</button>' : ''}
          <button type="button" class="${file.kind === 'markdown' ? '' : 'selected'}" data-document-mode="source">Source</button>
        </div>
        <article class="project-document-preview rich-text ${file.kind === 'markdown' ? '' : 'hidden'}">${file.kind === 'markdown' ? markdown(file.content, { sourcePath: file.path }) : ''}</article>
        <pre class="project-document-source ${file.kind === 'markdown' ? 'hidden' : ''}"><code>${escapeHtml(file.content)}</code></pre>
      </section>`;
    root.querySelector('[data-document-back]').addEventListener('click', event => {
      event.preventDefault();
      if (history.length > 1) history.back(); else go('/labs');
    });
    root.querySelectorAll('[data-document-mode]').forEach(button => button.addEventListener('click', () => {
      const preview = root.querySelector('.project-document-preview');
      const source = root.querySelector('.project-document-source');
      const previewMode = button.dataset.documentMode === 'preview';
      preview.classList.toggle('hidden', !previewMode);
      source.classList.toggle('hidden', previewMode);
      root.querySelectorAll('[data-document-mode]').forEach(item => item.classList.toggle('selected', item === button));
      if (previewMode) typeset(preview);
    }));
    typeset(root);
  }

  window.HeraldDocumentPage = { render };
})();
