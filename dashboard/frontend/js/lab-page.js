(function () {
  const fileSize = bytes => {
    const value = Number(bytes || 0);
    if (value < 1024) return `${value} B`;
    return value < 1024 * 1024 ? `${(value / 1024).toFixed(1)} KB` : `${(value / 1024 / 1024).toFixed(1)} MB`;
  };
  const stateClass = value => {
    const state = String(value || '').toLowerCase();
    if (state.includes('block')) return 'blocked';
    if (state.includes('complete') || state.includes('done') || state === 'verified') return 'complete';
    if (state === 'active' || state.includes('progress')) return 'active';
    return 'queued';
  };

  async function render(context) {
    const {
      api, request, go, notice, query, escapeHtml, badge,
      markdown, richInline, typeset
    } = context;
    const root = document.querySelector('#app');
    const id = query().get('id');
    if (!id) return go('/labs');

    const data = await api(`/api/labs/${id}`);
    const lab = data.lab;
    const detail = data.detail;
    const labAssetHref = path => `/lab-assets/${encodeURIComponent(id)}/${String(path).split('/').map(encodeURIComponent).join('/')}`;
    const bindDocumentAssets = element => {
      element.querySelectorAll('img[src], a[href]').forEach(resource => {
        const attribute = resource.tagName === 'IMG' ? 'src' : 'href';
        const path = resource.getAttribute(attribute) || '';
        if (/^(?:figures|results)\//.test(path)) resource.setAttribute(attribute, labAssetHref(path));
      });
    };
    const outputHref = output => output.href || `/lab-result?lab=${encodeURIComponent(id)}&result=${encodeURIComponent(output.id)}`;
    const outputIcon = output => ({ artifact: 'fa-cubes', figure: 'fa-chart-line', note: 'fa-file-lines', paper: 'fa-file-pdf', code: 'fa-code', wiki: 'fa-book-bookmark' }[output.kind] || 'fa-box-archive');
    const list = (items, ordered = false) => {
      if (!items?.length) return '<p class="lab-record-empty">Nothing recorded.</p>';
      const tag = ordered ? 'ol' : 'ul';
      return `<${tag} class="lab-record-list">${items.map(item => `<li><span>${richInline(item)}</span></li>`).join('')}</${tag}>`;
    };
    const resultRows = data.outputs?.length
      ? data.outputs.map(output => { const file = output.wiki_page ? `Wiki · ${output.wiki_page}` : `${output.asset_path} · ${fileSize(output.size)}`; return `<a class="research-result-row" href="${outputHref(output)}" data-lab-nav role="listitem">
          <i class="fa-solid ${outputIcon(output)}" aria-hidden="true"></i>
          <span class="research-result-name"><strong>${escapeHtml(output.title)}</strong><small>${escapeHtml(output.summary)}</small></span>
          <span class="research-result-type">${escapeHtml(output.kind)}</span>
          <span class="research-result-file">${escapeHtml(file)}</span>
          <i class="fa-solid fa-chevron-right research-result-arrow" aria-hidden="true"></i>
        </a>`; }).join('')
      : '<div class="lab-result-empty"><i class="fa-regular fa-chart-bar" aria-hidden="true"></i><strong>No result attached yet</strong><p>The Lab has not produced a visual or numerical result artifact.</p></div>';
    const discussionLinks = data.threads.length
      ? data.threads.map(thread => `<a class="lab-thread-item" href="/discussion?thread=${encodeURIComponent(thread.id)}" data-lab-nav><span>${badge(thread.priority)} ${badge(thread.status)}</span><strong>${escapeHtml(thread.title)}</strong></a>`).join('')
      : '<p class="muted">No linked discussion yet.</p>';

    document.title = `${lab.title} · Herald Decoder`;
    root.innerHTML = `
      <a class="back" href="/labs" data-lab-nav>← All labs</a>
      <header class="lab-detail-header">
        <div class="lab-detail-heading">
          <div>
            <p class="lab-overline">${escapeHtml(lab.id)} · ${escapeHtml(detail.phase || lab.stage)}</p>
            <div class="lab-title-badges">${badge(lab.stage)}</div>
            <h1>${escapeHtml(lab.title)}</h1>
            <div class="lab-detail-summary rich-text">${markdown(lab.summary)}</div>
          </div>
          <button id="edit-lab" class="button secondary"><i class="fa-solid fa-pen" aria-hidden="true"></i> Edit snapshot</button>
        </div>
        <div class="lab-detail-meta">
          <div><strong>Current focus</strong><div class="rich-text">${markdown(lab.current_focus)}</div></div>
          <div><strong>Updated</strong>${escapeHtml(lab.updated)}</div>
        </div>
      </header>

      <nav class="lab-section-nav" aria-label="Lab sections">
        <a href="#lab-results">Results</a>
        <a href="#lab-documents">Report & Plan</a>
        <a href="#lab-record">Research record</a>
      </nav>

      <div class="lab-detail-layout">
        <div class="lab-detail-main">
          <section class="lab-research-brief">
            <div class="lab-section-heading">
              <div><p class="panel-kicker">THE SCIENTIFIC JOB</p><h2>Research brief</h2></div>
            </div>
            <div class="lab-question">
              <span>Current research question</span>
              <div class="rich-text">${markdown(detail.question)}</div>
            </div>
            <div class="lab-brief-columns">
              <div><h3>Motivation</h3><div class="rich-text">${markdown(detail.motivation)}</div></div>
              <div><h3>Current focus</h3><div class="rich-text">${markdown(lab.current_focus)}</div></div>
              <div><h3>Status</h3><div class="rich-text">${markdown(detail.status || `Stage: **${lab.stage}**. ${lab.next_action}`)}</div></div>
            </div>
          </section>

          <section id="lab-results" class="lab-primary-section lab-results-section">
            <div class="lab-section-heading">
              <div><p class="panel-kicker">WHAT THE LAB PRODUCED</p><h2>Results</h2></div>
              <span class="lab-section-count">${data.outputs?.length || 0} published result${data.outputs?.length === 1 ? '' : 's'}</span>
            </div>
            <div class="research-results-list" role="list">${resultRows}</div>
          </section>

          <section id="lab-documents" class="lab-primary-section lab-documents-section">
            <div class="lab-section-heading">
              <div><p class="panel-kicker">CORE RESEARCH DOCUMENTS</p><h2>Report & Plan</h2></div>
              <div class="lab-document-tabs" role="tablist" aria-label="Lab documents">
                <button class="selected" type="button" data-lab-document="report" role="tab" aria-selected="true"><i class="fa-regular fa-file-lines" aria-hidden="true"></i> Report</button>
                <button type="button" data-lab-document="plan" role="tab" aria-selected="false"><i class="fa-regular fa-map" aria-hidden="true"></i> Plan</button>
              </div>
            </div>
            <div id="lab-document-path" class="lab-document-path">${escapeHtml(data.report.path)}</div>
            <article id="lab-document" class="lab-document rich-text">${markdown(data.report.content, { sourcePath: data.report.path })}</article>
          </section>

          <section id="lab-record" class="lab-primary-section lab-record-section">
            <div class="lab-section-heading">
              <div><p class="panel-kicker">DECISIONS OVER TIME</p><h2>Research record</h2></div>
            </div>
            <details class="lab-record-group" open>
              <summary><span>Open frontier</span><small>${detail.frontier?.length || 0} questions</small></summary>
              ${list(detail.frontier)}
            </details>
            ${detail.blockers?.length ? `<details class="lab-record-group lab-record-blockers" open><summary><span>Blockers</span><small>${detail.blockers.length} active</small></summary>${list(detail.blockers)}</details>` : ''}
            <details class="lab-record-group">
              <summary><span>Resolved history</span><small>${detail.resolved?.length || 0} decisions</small></summary>
              ${list(detail.resolved, true)}
            </details>
          </section>
        </div>

        <aside class="lab-detail-rail" aria-label="Lab status and actions">
          <section class="lab-rail-card lab-next-card">
            <p class="panel-kicker">NEXT DECISIVE ACTION</p>
            <div class="rich-text">${markdown(lab.next_action)}</div>
          </section>


          <section class="lab-rail-card">
            <div class="lab-rail-heading"><div><p class="panel-kicker">DISCUSSION</p><h2>Linked threads</h2></div><button id="open-lab-thread" type="button" aria-label="Open a Lab discussion"><i class="fa-solid fa-plus" aria-hidden="true"></i></button></div>
            <div class="lab-thread-list">${discussionLinks}</div>
          </section>

        </aside>
      </div>

      <dialog id="lab-editor">
        <form method="dialog">
          <h2>Edit current snapshot</h2>
          <label>Stage<select name="stage">${['active', 'blocked', 'complete'].map(stage => `<option ${lab.stage === stage ? 'selected' : ''}>${stage}</option>`).join('')}</select></label>
          <label>Current focus<textarea name="current_focus">${escapeHtml(lab.current_focus)}</textarea></label>
          <label>Next action<textarea name="next_action">${escapeHtml(lab.next_action)}</textarea></label>
          <menu><button value="cancel" class="button secondary">Cancel</button><button id="save-lab" value="default" class="button">Save snapshot</button></menu>
        </form>
      </dialog>
    `;

    bindDocumentAssets(document.querySelector('#lab-document'));

    document.querySelectorAll('[data-lab-nav]').forEach(link => link.addEventListener('click', event => {
      event.preventDefault();
      go(link.getAttribute('href'));
    }));
    document.querySelectorAll('[data-lab-document]').forEach(button => button.addEventListener('click', () => {
      const kind = button.dataset.labDocument;
      document.querySelectorAll('[data-lab-document]').forEach(item => {
        const selected = item === button;
        item.classList.toggle('selected', selected);
        item.setAttribute('aria-selected', String(selected));
      });
      const documentTarget = document.querySelector('#lab-document');
      const source = kind === 'plan' ? data.plan : data.report;
      document.querySelector('#lab-document-path').textContent = source.path;
      documentTarget.innerHTML = markdown(source.content, { sourcePath: source.path });
      bindDocumentAssets(documentTarget);
      typeset(documentTarget);
    }));
    document.querySelector('#edit-lab').addEventListener('click', () => document.querySelector('#lab-editor').showModal());
    document.querySelector('#save-lab').addEventListener('click', async event => {
      event.preventDefault();
      const form = event.target.form;
      await request(`/api/labs/${id}`, 'PATCH', {
        stage: form.stage.value,
        current_focus: form.current_focus.value,
        next_action: form.next_action.value
      });
      form.closest('dialog').close();
      notice('Lab snapshot saved');
      render(context);
    });
    document.querySelector('#open-lab-thread').addEventListener('click', () => go(`/discussion?new=1&lab=${encodeURIComponent(id)}`));
    typeset(root);
  }

  window.HeraldLabPage = { render };
})();
