(function () {
  const escape = value => String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  })[character]);
  const matchPresentation = {
    exact: { label: 'Exact match', icon: 'fa-bullseye' },
    direct: { label: 'Direct hit', icon: 'fa-link' },
    conceptual: { label: 'Conceptually related', icon: 'fa-wand-magic-sparkles' }
  };

  function note(result, compact = false) {
    if (!result) return '';
    const presentation = matchPresentation[result.match_type] || matchPresentation.direct;
    return `<span class="search-match search-match-${escape(result.match_type)} ${compact ? 'compact' : ''}"><i class="fa-solid ${presentation.icon}" aria-hidden="true"></i><b>${presentation.label}</b>${compact ? '' : `<small>${escape(result.reason || '')}</small>`}</span>`;
  }

  function resultMap(payload) {
    return new Map((payload?.results || []).map((result, rank) => [result.entity_id, { ...result, rank }]));
  }

  function localFilter(items, query) {
    const terms = String(query).trim().toLowerCase().match(/[a-z0-9+()._/-]+|[\u3400-\u9fff]+/g) || [];
    if (!terms.length) return [...items];
    return items.filter(item => {
      const text = JSON.stringify(item).toLowerCase();
      return terms.every(term => text.includes(term));
    });
  }

  function bind({ scope, input, clear, limit = 100, onUpdate }) {
    let timer = 0;
    let sequence = 0;
    let controller = null;
    const control = input.closest('.search-control');
    const emit = payload => onUpdate({ ...payload, query: input.value.trim(), resultMap: resultMap(payload) });
    const setBusy = busy => control?.classList.toggle('searching', busy);

    const run = () => {
      window.clearTimeout(timer);
      controller?.abort();
      sequence += 1;
      const currentSequence = sequence;
      const query = input.value.trim();
      if (!query) {
        setBusy(false);
        emit({ mode: 'browse', results: [], complex_query: false });
        return;
      }
      setBusy(true);
      emit({ mode: 'pending', results: [], complex_query: false });
      timer = window.setTimeout(async () => {
        controller = new AbortController();
        const fetchRanked = async refine => {
          const params = new URLSearchParams({ q: query, scope, limit: String(limit), refine: String(refine) });
          const response = await fetch(`/api/search?${params}`, { cache: 'no-store', signal: controller.signal });
          if (!response.ok) throw new Error('Search unavailable');
          return response.json();
        };
        try {
          const payload = await fetchRanked(false);
          if (currentSequence !== sequence || input.value.trim() !== query) return;
          setBusy(false);
          emit(payload);
          if (!payload.complex_query || payload.mode === 'local') return;
          setBusy(true);
          emit({ ...payload, mode: 'refining' });
          const refined = await fetchRanked(true);
          if (currentSequence !== sequence || input.value.trim() !== query) return;
          setBusy(false);
          emit(refined);
        } catch (error) {
          if (error.name === 'AbortError' || currentSequence !== sequence) return;
          setBusy(false);
          emit({ mode: 'unavailable', results: [], complex_query: false });
        }
      }, 180);
    };

    input.addEventListener('input', run);
    clear?.addEventListener('click', () => {
      input.value = '';
      input.focus();
      run();
    });
    return { run, destroy: () => { window.clearTimeout(timer); controller?.abort(); } };
  }

  window.HeraldSearch = { bind, note, resultMap, localFilter };
})();
