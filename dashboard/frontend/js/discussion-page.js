(function () {
  const label = value => String(value || '').replaceAll('-', ' ');
  const shortId = value => String(value || '').replace(/^thread-0*/, '#');
  const formatDate = value => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value || '') : new Intl.DateTimeFormat(undefined, {
      month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
    }).format(date);
  };

  async function render(deps) {
    const { api, request, go, notice, query, escapeHtml, markdown, typeset } = deps;
    const root = document.querySelector('#app');
    const [discussion, labData] = await Promise.all([api('/api/discussion'), api('/api/labs')]);
    const threads = [...discussion.threads].sort((left, right) => String(right.updated || '').localeCompare(String(left.updated || '')));
    const selected = threads.find(item => item.id === query().get('thread')) || null;
    const creating = query().get('new') === '1';
    const relatedLab = query().get('lab') || '';

    root.innerHTML = `
      <section class="discussion-head">
        <div>
          <p class="eyebrow">Project Forum</p>
          <h1>Discussion</h1>
          <p>Open research questions, give direction, review evidence, and preserve decisions as threaded conversations.</p>
        </div>
        ${creating ? '' : '<button id="discussion-new-thread" class="button" type="button"><i class="fa-solid fa-plus" aria-hidden="true"></i> New thread</button>'}
      </section>
      <section id="discussion-surface" aria-live="polite"></section>`;

    const surface = document.querySelector('#discussion-surface');
    const openCount = threads.filter(item => item.status === 'open').length;
    const closedCount = threads.filter(item => item.status === 'closed').length;

    const issueRow = thread => `
      <button class="issue-row" type="button" data-thread-id="${escapeHtml(thread.id)}" data-status="${escapeHtml(thread.status)}" data-search="${escapeHtml([thread.title, thread.category, thread.priority, ...(thread.related_labs || [])].join(' ').toLowerCase())}">
        <i class="${thread.status === 'open' ? 'fa-regular fa-circle-dot issue-open-icon' : 'fa-regular fa-circle-check issue-closed-icon'}" aria-hidden="true"></i>
        <span class="issue-row-content">
          <span class="issue-row-title">${escapeHtml(thread.title)}</span>
          <span class="issue-labels"><span class="issue-label issue-label-topic">${escapeHtml(label(thread.category || 'scientific'))}</span><span class="issue-label issue-label-${escapeHtml(thread.priority)}">${escapeHtml(label(thread.priority))}</span>${(thread.related_labs || []).map(id => `<span class="issue-label issue-label-lab">${escapeHtml(id)}</span>`).join('')}</span>
          <small>${escapeHtml(shortId(thread.id))} updated ${escapeHtml(formatDate(thread.updated))}</small>
        </span>
        <span class="issue-row-comments"><i class="fa-regular fa-comment" aria-hidden="true"></i> ${Math.max(0, (thread.messages?.length || 1) - 1)}</span>
      </button>`;

    const bindThreadLinks = container => container.querySelectorAll('[data-thread-id]').forEach(button => {
      button.addEventListener('click', () => go(`/discussion?thread=${encodeURIComponent(button.dataset.threadId)}`));
    });

    const renderIssueList = () => {
      surface.innerHTML = `
        <section class="issue-board">
          <div class="issue-toolbar">
            <div class="issue-state-tabs" role="group" aria-label="Thread status">
              <button class="selected" type="button" data-issue-filter="open"><i class="fa-regular fa-circle-dot" aria-hidden="true"></i> ${openCount} Open</button>
              <button type="button" data-issue-filter="closed"><i class="fa-regular fa-circle-check" aria-hidden="true"></i> ${closedCount} Closed</button>
              <button type="button" data-issue-filter="all">${threads.length} All</button>
            </div>
            <div class="search-control issue-search"><i class="fa-solid fa-magnifying-glass search-icon" aria-hidden="true"></i><input id="discussion-search" type="search" placeholder="Search threads" aria-label="Search discussion threads"><button id="discussion-search-clear" class="search-clear" type="button" aria-label="Clear thread search"><i class="fa-solid fa-xmark" aria-hidden="true"></i></button></div>
          </div>
          <div id="issue-list" class="issue-list">${threads.length ? threads.map(issueRow).join('') : ''}</div>
          <div id="issue-list-empty" class="issue-list-empty" ${threads.length ? 'hidden' : ''}><i class="fa-regular fa-circle-dot" aria-hidden="true"></i><h2>No open research thread.</h2><p>There are no questions or decisions awaiting attention.</p><button class="button" type="button" data-start-thread>Start the first thread</button></div>
          <div id="issue-filter-empty" class="issue-filter-empty" hidden><i class="fa-solid fa-filter-circle-xmark" aria-hidden="true"></i><h2 id="issue-filter-empty-title">No matching threads</h2><p id="issue-filter-empty-copy">Try another status or a broader search.</p></div>
        </section>`;
      bindThreadLinks(surface);
      surface.querySelector('[data-start-thread]')?.addEventListener('click', () => go('/discussion?new=1'));
      const rows = [...surface.querySelectorAll('.issue-row')];
      const search = surface.querySelector('#discussion-search');
      let status = 'open';
      const paint = () => {
        const needle = search.value.trim().toLowerCase();
        let visible = 0;
        rows.forEach(row => {
          const show = (status === 'all' || row.dataset.status === status) && (!needle || row.dataset.search.includes(needle));
          row.hidden = !show;
          visible += Number(show);
        });
        const empty = surface.querySelector('#issue-filter-empty');
        empty.hidden = visible > 0 || threads.length === 0;
        const noOpenThreads = status === 'open' && !needle && openCount === 0;
        surface.querySelector('#issue-filter-empty-title').textContent = noOpenThreads ? 'No open research thread.' : 'No matching threads';
        surface.querySelector('#issue-filter-empty-copy').textContent = noOpenThreads
          ? 'There are no questions or decisions awaiting attention.'
          : 'Try another status or a broader search.';
      };
      surface.querySelectorAll('[data-issue-filter]').forEach(button => button.addEventListener('click', () => {
        status = button.dataset.issueFilter;
        surface.querySelectorAll('[data-issue-filter]').forEach(item => item.classList.toggle('selected', item === button));
        paint();
      }));
      search.addEventListener('input', paint);
      surface.querySelector('#discussion-search-clear').addEventListener('click', () => { search.value = ''; search.focus(); paint(); });
      paint();
    };

    const renderNewIssue = () => {
      surface.innerHTML = `
        <a class="discussion-back" href="/discussion" data-discussion-back><i class="fa-solid fa-arrow-left" aria-hidden="true"></i> All threads</a>
        <form id="new-issue-form" class="new-issue-layout">
          <section class="new-issue-editor">
            <header><span class="issue-avatar user-avatar"><i class="fa-regular fa-user" aria-hidden="true"></i></span><div><h2>Open a new research thread</h2><p>The title should name the question or decision. The description becomes the opening post.</p></div></header>
            <label for="new-issue-title">Title</label>
            <input id="new-issue-title" name="title" maxlength="160" placeholder="What should this thread resolve?" required autofocus>
            <label for="new-issue-body">Description</label>
            <div class="issue-editor-toolbar"><span><i class="fa-brands fa-markdown" aria-hidden="true"></i> Write</span><small>Markdown and LaTeX math supported</small></div>
            <textarea id="new-issue-body" name="message" rows="14" maxlength="12000" placeholder="Provide context, ask the question, or specify the next research action…" required></textarea>
            <div class="new-issue-actions"><button class="button secondary" type="button" data-cancel-new>Cancel</button><button class="button" type="submit"><i class="fa-regular fa-circle-dot" aria-hidden="true"></i> Open thread</button></div>
          </section>
          <aside class="new-issue-sidebar">
            <label>Topic<select name="category"><option value="scientific">Scientific</option><option value="task">Task</option><option value="scope">Scope</option><option value="checkpoint">Checkpoint</option></select></label>
            <label>Priority<select name="priority"><option value="normal">Normal</option><option value="high">High</option><option value="blocking">Blocking</option><option value="low">Low</option></select></label>
            <label>Related Lab<select name="related_lab"><option value="">Project-wide</option>${labData.labs.map(lab => `<option value="${escapeHtml(lab.id)}" ${lab.id === relatedLab ? 'selected' : ''}>${escapeHtml(lab.title)}</option>`).join('')}</select></label>
            <section><h3>Good research threads</h3><ul><li>Ask one concrete question.</li><li>Include the evidence or context needed to respond.</li><li>State whether a decision or an experiment is expected.</li></ul></section>
          </aside>
        </form>`;
      surface.querySelector('[data-discussion-back]').addEventListener('click', event => { event.preventDefault(); go('/discussion'); });
      surface.querySelector('[data-cancel-new]').addEventListener('click', () => go('/discussion'));
      surface.querySelector('#new-issue-form').addEventListener('submit', async event => {
        event.preventDefault();
        const form = event.currentTarget;
        const submit = form.querySelector('[type="submit"]');
        submit.disabled = true;
        try {
          const result = await request('/api/discussion/threads', 'POST', {
            title: form.title.value,
            message: form.message.value,
            category: form.category.value,
            priority: form.priority.value,
            related_labs: form.related_lab.value ? [form.related_lab.value] : []
          });
          notice('Discussion thread created');
          go(`/discussion?thread=${encodeURIComponent(result.thread.id)}`);
        } catch (error) {
          notice(error.message || 'Could not create the thread', true);
          submit.disabled = false;
        }
      });
    };

    const timelineMessage = message => `
      <div class="issue-timeline-item">
        <span class="issue-avatar ${message.author === 'user' ? 'user-avatar' : 'agent-avatar'}"><i class="${message.author === 'user' ? 'fa-regular fa-user' : 'fa-solid fa-wand-magic-sparkles'}" aria-hidden="true"></i></span>
        <article class="issue-comment ${message.author === 'user' && !message.withdrawn ? 'has-comment-actions' : ''}">
          <header><strong>${escapeHtml(message.author === 'user' ? 'You' : 'Research agent')}</strong><span>${escapeHtml(label(message.type))} · ${escapeHtml(formatDate(message.created))}${message.edited ? ' · edited' : ''}</span></header>
          <div class="rich-text ${message.withdrawn ? 'issue-comment-withdrawn' : ''}">${message.withdrawn ? '<em>This post was withdrawn.</em>' : markdown(message.content)}</div>
          ${message.author === 'user' && !message.withdrawn ? `<span class="issue-comment-actions"><button class="issue-comment-edit" type="button" data-edit-message="${escapeHtml(message.id)}" aria-label="Edit your post" title="Edit post"><i class="fa-solid fa-pen" aria-hidden="true"></i></button><button class="issue-comment-withdraw" type="button" data-withdraw-message="${escapeHtml(message.id)}" aria-label="Withdraw your post" title="Withdraw post"><i class="fa-solid fa-arrow-rotate-left" aria-hidden="true"></i></button></span>` : ''}
        </article>
      </div>`;

    const renderIssueDetail = thread => {
      const labLinks = (thread.related_labs || []).map(id => `<a href="/lab?id=${encodeURIComponent(id)}" data-nav>${escapeHtml(id)}</a>`).join('') || '<span>Project-wide</span>';
      surface.innerHTML = `
        <a class="discussion-back" href="/discussion" data-discussion-back><i class="fa-solid fa-arrow-left" aria-hidden="true"></i> All threads</a>
        <header class="issue-detail-head">
          <h2>${escapeHtml(thread.title)} <span>${escapeHtml(shortId(thread.id))}</span></h2>
          <p><span class="discussion-status discussion-status-${escapeHtml(thread.status)}"><i class="fa-regular ${thread.status === 'open' ? 'fa-circle-dot' : 'fa-circle-check'}" aria-hidden="true"></i> ${escapeHtml(label(thread.status))}</span> ${thread.messages?.length || 0} post${thread.messages?.length === 1 ? '' : 's'} in this conversation</p>
        </header>
        <section class="issue-detail-layout">
          <main class="issue-timeline">
            ${thread.messages.map(timelineMessage).join('')}
            ${thread.status === 'open' ? `
              <form id="issue-reply-form" class="issue-timeline-item issue-reply">
                <span class="issue-avatar user-avatar"><i class="fa-regular fa-user" aria-hidden="true"></i></span>
                <div class="issue-comment issue-reply-card"><label for="issue-reply-body">Add to the conversation</label><div class="issue-editor-toolbar"><span><i class="fa-brands fa-markdown" aria-hidden="true"></i> Write</span><small>Markdown and LaTeX math supported</small></div><textarea id="issue-reply-body" name="message" rows="7" maxlength="12000" placeholder="Reply, redirect the work, ask for evidence, or record a decision…" required></textarea><div class="issue-reply-actions"><button class="button" type="submit"><i class="fa-regular fa-paper-plane" aria-hidden="true"></i> Comment</button></div></div>
              </form>` : '<div class="issue-closed-note"><i class="fa-regular fa-circle-check" aria-hidden="true"></i><span><strong>This thread was closed.</strong><small>The conversation remains part of the research record.</small></span></div>'}
          </main>
          <aside class="issue-metadata">
            <section><h3>Status</h3><span class="discussion-status discussion-status-${escapeHtml(thread.status)}">${escapeHtml(label(thread.status))}</span></section>
            <section><h3>Priority</h3><span class="issue-label issue-label-${escapeHtml(thread.priority)}">${escapeHtml(label(thread.priority))}</span></section>
            <section><h3>Topic</h3><span class="issue-label issue-label-topic">${escapeHtml(label(thread.category || 'scientific'))}</span></section>
            <section><h3>Related Lab</h3><div class="issue-related-labs">${labLinks}</div></section>
            <section><h3>Activity</h3><p>Opened ${escapeHtml(formatDate(thread.created))}</p><p>Updated ${escapeHtml(formatDate(thread.updated))}</p></section>
            <button id="issue-transition" class="button secondary" type="button">${thread.status === 'open' ? 'Close thread' : 'Reopen thread'}</button>
          </aside>
        </section>`;
      surface.querySelector('[data-discussion-back]').addEventListener('click', event => { event.preventDefault(); go('/discussion'); });
      surface.querySelectorAll('[data-nav]').forEach(link => link.addEventListener('click', event => { event.preventDefault(); go(link.getAttribute('href')); }));
      surface.querySelector('#issue-reply-form')?.addEventListener('submit', async event => {
        event.preventDefault();
        const form = event.currentTarget;
        const submit = form.querySelector('[type="submit"]');
        submit.disabled = true;
        try {
          await request(`/api/discussion/threads/${encodeURIComponent(thread.id)}/messages`, 'POST', { message: form.message.value });
          notice('Comment added');
          go(`/discussion?thread=${encodeURIComponent(thread.id)}`);
        } catch (error) {
          notice(error.message || 'Could not add the comment', true);
          submit.disabled = false;
        }
      });
      surface.querySelectorAll('[data-edit-message]').forEach(button => button.addEventListener('click', () => {
        const message = thread.messages.find(item => item.id === button.dataset.editMessage);
        const content = button.closest('.issue-comment').querySelector('.rich-text');
        if (!message || !content || content.dataset.editing) return;
        content.dataset.editing = 'true';
        content.innerHTML = `<form class="issue-inline-editor"><textarea name="message" rows="7" maxlength="12000" required>${escapeHtml(message.content)}</textarea><div><button class="button secondary" type="button" data-cancel-edit>Cancel</button><button class="button" type="submit">Save edit</button></div></form>`;
        const form = content.querySelector('form');
        form.querySelector('[data-cancel-edit]').addEventListener('click', () => go(`/discussion?thread=${encodeURIComponent(thread.id)}`));
        form.addEventListener('submit', async event => {
          event.preventDefault();
          const submit = form.querySelector('[type="submit"]');
          submit.disabled = true;
          try {
            await request(`/api/discussion/threads/${encodeURIComponent(thread.id)}/messages/${encodeURIComponent(message.id)}`, 'PATCH', { message: form.message.value });
            notice('Post updated');
            go(`/discussion?thread=${encodeURIComponent(thread.id)}`);
          } catch (error) {
            notice(error.message || 'Could not update the post', true);
            submit.disabled = false;
          }
        });
        form.message.focus();
      }));
      surface.querySelectorAll('[data-withdraw-message]').forEach(button => button.addEventListener('click', async () => {
        const message = thread.messages.find(item => item.id === button.dataset.withdrawMessage);
        if (!message || !window.confirm('Withdraw this post? The timeline will retain a withdrawn marker.')) return;
        button.disabled = true;
        try {
          await request(`/api/discussion/threads/${encodeURIComponent(thread.id)}/messages/${encodeURIComponent(message.id)}`, 'PATCH', { withdraw: true });
          notice('Post withdrawn');
          go(`/discussion?thread=${encodeURIComponent(thread.id)}`);
        } catch (error) {
          notice(error.message || 'Could not withdraw the post', true);
          button.disabled = false;
        }
      }));
      surface.querySelector('#issue-transition').addEventListener('click', async event => {
        event.currentTarget.disabled = true;
        try {
          const status = thread.status === 'open' ? 'closed' : 'open';
          await request(`/api/discussion/threads/${encodeURIComponent(thread.id)}`, 'PATCH', { status });
          notice(status === 'open' ? 'Thread reopened' : 'Thread closed');
          go(`/discussion?thread=${encodeURIComponent(thread.id)}`);
        } catch (error) {
          notice(error.message || 'Could not update the thread', true);
          event.currentTarget.disabled = false;
        }
      });
      typeset(surface);
    };

    document.querySelector('#discussion-new-thread')?.addEventListener('click', () => go('/discussion?new=1'));
    if (creating) renderNewIssue();
    else if (selected) renderIssueDetail(selected);
    else renderIssueList();
  }

  window.HeraldDiscussionPage = { render };
})();
