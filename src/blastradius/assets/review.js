(() => {
  'use strict';
  const configuration = JSON.parse(document.getElementById('review-data').textContent);
  const snapshot = configuration.mode === 'snapshot';
  if (!snapshot) document.getElementById('first-lesson-link').href = '/learn';
  const byId = id => document.getElementById(id);
  const element = (tag, content, className) => {
    const node = document.createElement(tag);
    if (content !== undefined) node.textContent = String(content);
    if (className) node.className = className;
    return node;
  };
  const icon = name => {
    const graphic = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    graphic.setAttribute('class', 'icon');
    graphic.setAttribute('aria-hidden', 'true');
    const reference = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    reference.setAttribute('href', '#br-' + name);
    graphic.append(reference);
    return graphic;
  };
  const text = (id, value) => { byId(id).textContent = String(value); };
  const status = message => text('activity', message);
  const locationText = location => `${location.path}:${location.start_line}:${location.start_column}`;
  const resourceName = finding => finding.impact.resource_arn.split(':secret:')[1] || finding.impact.resource_arn;
  const jobName = finding => finding.authorization?.workflow.job_id || finding.path[0].source.name.replace('OIDC request in job ', '');
  const trustFor = finding => finding.authorization?.trust;
  const controlFor = finding => finding.remediation.control_id;
  const matrixText = matrix => Object.entries(matrix || {}).map(([key, value]) => `${key}=${String(value).replace(/^arn:aws:iam::\d+:role\//, '')}`).join(', ');
  const identityStates = {'unresolved': 'Unresolved', 'declared-request': 'Declared role', 'matched-trust': 'Matched declared trust'};
  let current = null;
  let selected = 0;
  let selectedNode = 2;
  let sourceMode = 'local';
  let busy = false;
  let activeOperation = null;
  let lastInput = null;
  let controls = new Set();
  let comparison = null;
  let comparisonPending = false;
  let revision = 0;
  let offlineSimulated = false;
  let declaration = '';
  let identityPage = 0;
  const identityPageSize = 20;

  function error(message) {
    text('error-message', message);
    byId('error').hidden = false;
  }

  function toggleSource(visible) {
    byId('source-panel').hidden = !visible;
    byId('source-toggle').setAttribute('aria-expanded', String(visible));
  }

  function setBusy(value) {
    busy = value;
    document.body.classList.toggle('busy', value);
    byId('review-main').setAttribute('aria-busy', String(value));
    for (const button of document.querySelectorAll('#source-panel button, #source-panel input, #rescan, #reset')) button.disabled = value;
    byId('cancel-analysis').hidden = !value;
    byId('cancel-analysis').disabled = false;
    if (!value) setMode(sourceMode);
  }

  async function request(route, data, raw = false, signal) {
    const response = await fetch('/api/' + route, {method: 'POST', credentials: 'omit', cache: 'no-store', redirect: 'error', headers: {'Content-Type': 'application/json', 'X-BlastRadius-Token': configuration.token}, body: JSON.stringify(data), signal});
    if (!response.ok) {
      const failure = await response.json();
      const error = new Error(failure.error || 'The local request could not be completed.');
      error.cancelled = failure.cancelled === true;
      throw error;
    }
    return raw ? response : response.json();
  }

  function setMode(mode) {
    sourceMode = mode;
    for (const button of document.querySelectorAll('[data-mode]')) button.setAttribute('aria-pressed', String(button.dataset.mode === mode));
    for (const group of ['local', 'github']) {
      byId(group + '-fields').hidden = group !== mode;
      for (const input of byId(group + '-fields').querySelectorAll('input')) input.disabled = group !== mode || busy;
    }
    byId('repository-url').required = mode === 'github';
  }

  function showView(view, focus = false) {
    document.querySelector('.baseline-totals').hidden = view !== 'paths';
    for (const button of document.querySelectorAll('[data-view]')) {
      const active = button.dataset.view === view;
      button.setAttribute('aria-selected', String(active));
      button.tabIndex = active ? 0 : -1;
      byId(button.dataset.view + '-view').hidden = !active;
      if (focus && active) button.focus();
    }
  }

  function clearView() {
    current = null;
    comparison = null;
    controls = new Set();
    revision += 1;
    offlineSimulated = false;
    byId('report').hidden = true;
    byId('export-bar').hidden = true;
    byId('rescan').hidden = true;
    byId('empty-state').hidden = false;
    byId('error').hidden = true;
    document.body.classList.remove('has-result');
    text('context-label', 'Investigation workspace');
    text('repository-name', 'Repository review');
    text('source-ref', 'No source selected');
    text('footer-hash', 'No snapshot');
    status('');
    document.title = 'Blast Radius | Repository Review';
  }

  async function cancelAnalysis() {
    const operation = activeOperation;
    if (!operation) return;
    operation.cancelRequested = true;
    byId('cancel-analysis').disabled = true;
    status('Cancellation requested; waiting for the next safe checkpoint.');
    try { await request('cancel', {operation_id: operation.id}); } catch {}
  }

  function saveExample() {
    if (snapshot) return;
    try {
      if (current?.repository.is_example && lastInput?.source === 'example') sessionStorage.setItem('br-example-review', JSON.stringify({version: 1, example: lastInput.example || 'single', controls: [...controls], hash: current.analysis_hash}));
      else sessionStorage.removeItem('br-example-review');
    } catch {}
  }

  async function analyze(data, saved = null) {
    if (busy || comparisonPending) return;
    clearView();
    setBusy(true);
    const operation = {id: crypto.randomUUID(), cancelRequested: false, polling: false, controller: new AbortController()};
    activeOperation = operation;
    const deadline = setTimeout(cancelAnalysis, 120000);
    const clientDeadline = setTimeout(() => operation.controller.abort(), 135000);
    const progress = setInterval(async () => {
      if (activeOperation !== operation || operation.polling) return;
      operation.polling = true;
      try {
        if (operation.cancelRequested) await request('cancel', {operation_id: operation.id});
        else { const update = await request('status', {operation_id: operation.id}); if (activeOperation === operation && update.state === 'running') status(update.stage); }
      } catch {} finally { operation.polling = false; }
    }, 750);
    status(data.source === 'github' ? 'Resolving immutable commit and reading declarations...' : 'Reading repository declarations...');
    try {
      const response = await request('analyze', {...data, operation_id: operation.id}, false, operation.controller.signal);
      if (operation.cancelRequested) { await request('clear', {}); status('Analysis cancelled. No result retained.'); return; }
      lastInput = {...data};
      showResult(response);
      if (saved?.hash === response.analysis_hash && Array.isArray(saved.controls) && saved.controls.length <= 128 && saved.controls.every(identifier => response.controls.some(control => control.id === identifier))) {
        controls = new Set(saved.controls);
        if (controls.size) await recompute();
      }
      saveExample();
      toggleSource(false);
      status('Snapshot ready.');
    } catch (failure) {
      if (failure.cancelled) status(failure.message);
      else { error(failure.name === 'AbortError' ? 'Client deadline reached. Cancellation was requested; no result is being displayed.' : failure.message === 'Failed to fetch' ? 'The local review service is unavailable.' : failure.message); status('Analysis not completed.'); }
      toggleSource(true);
    } finally { clearInterval(progress); clearTimeout(deadline); clearTimeout(clientDeadline); activeOperation = null; setBusy(false); }
  }

  async function copy(value) {
    try { await navigator.clipboard.writeText(value); status('Copied.'); }
    catch { status('Clipboard access is unavailable in this browser.'); }
  }

  function sourceLocation(location) {
    const row = element('div', undefined, 'source-location');
    row.append(icon('file-code'));
    const source = current.repository.input;
    const slug = current.repository.slug;
    let label = element('span', locationText(location));
    if (source && /^[a-f0-9]{40}$/i.test(source.commit_sha || '') && /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(slug)) {
      label = element('a', locationText(location));
      label.href = 'https://github.com/' + slug.split('/').map(encodeURIComponent).join('/') + '/blob/' + source.commit_sha + '/' + location.path.split('/').map(encodeURIComponent).join('/') + '#L' + location.start_line;
      label.target = '_blank';
      label.rel = 'noopener noreferrer';
    }
    row.append(label);
    const button = element('button');
    button.type = 'button';
    button.title = 'Copy source location';
    button.setAttribute('aria-label', 'Copy ' + locationText(location));
    button.append(icon('copy'));
    button.addEventListener('click', () => copy(locationText(location)));
    row.append(button);
    return row;
  }

  function facts(container, entries) {
    container.replaceChildren();
    for (const [label, value] of entries) if (value !== undefined) container.append(element('dt', label), element('dd', Array.isArray(value) ? value.join(', ') : value));
  }

  function findingState(finding) {
    if (snapshot) return offlineSimulated && finding === current.findings[selected] && finding.remediation.path_broken ? (finding.unmodeled_alternatives?.length ? 'incomplete' : 'blocked') : 'reachable';
    if (controls.size && (!comparison || comparisonPending)) return 'unknown';
    const state = comparison?.finding_states.find(item => item.finding_id === finding.id);
    if (state && !state.reachable) return state.remaining_access_unknown ? 'incomplete' : 'blocked';
    if (state && controls.has(controlFor(finding))) return 'alternate';
    return 'reachable';
  }

  function filteredFindings() {
    const query = byId('finding-search').value.toLocaleLowerCase();
    const filter = byId('finding-status').value;
    return current.findings.map((finding, index) => ({finding, index})).filter(({finding}) => {
      const searchable = [finding.impact.resource_arn, jobName(finding), finding.authorization?.workflow.name, finding.authorization?.workflow.role_arn, ...finding.path.map(step => step.target.name)].join(' ').toLocaleLowerCase();
      const state = findingState(finding);
      return searchable.includes(query) && (filter === 'all' || (filter === 'blocked' ? ['blocked', 'incomplete'].includes(state) : ['reachable', 'alternate'].includes(state)));
    }).sort((left, right) => {
      const leftKey = jobName(left.finding) + '\n' + left.finding.impact.resource_arn;
      const rightKey = jobName(right.finding) + '\n' + right.finding.impact.resource_arn;
      return leftKey < rightKey ? -1 : leftKey > rightKey ? 1 : left.index - right.index;
    });
  }

  function renderQueue() {
    const focused = document.activeElement?.dataset.finding;
    const scroll = {left: byId('finding-list').scrollLeft, top: byId('finding-list').scrollTop};
    const visible = filteredFindings();
    text('queue-count', `${visible.length} / ${current.findings.length}`);
    byId('queue-empty').hidden = visible.length > 0;
    if (visible.length && !visible.some(item => item.index === selected)) selected = visible[0].index;
    byId('finding-list').replaceChildren();
    for (const {finding, index} of visible) {
      const row = element('li');
      const button = element('button', undefined, 'finding-choice');
      const state = findingState(finding);
      button.type = 'button';
      button.dataset.finding = String(index);
      button.dataset.state = state;
      button.setAttribute('aria-pressed', String(index === selected));
      const top = element('span', undefined, 'queue-item-top');
      top.append(element('span', 'PATH ' + String(index + 1).padStart(2, '0')), element('span', state === 'unknown' ? 'Not recomputed' : state === 'incomplete' ? 'Remaining access unknown' : state === 'blocked' ? 'Blocked in model' : state === 'alternate' ? 'Alternate trust' : 'Declared access', 'path-status'));
      const job = element('span', undefined, 'queue-job');
      job.append(icon('code'), element('span', jobName(finding)));
      button.append(top, element('strong', resourceName(finding), 'queue-resource'), job);
      if (Object.keys(finding.authorization?.workflow.matrix || {}).length) button.append(element('small', matrixText(finding.authorization.workflow.matrix), 'queue-matrix'));
      button.addEventListener('click', () => { selected = index; selectedNode = 2; offlineSimulated = false; renderQueue(); renderFinding(); });
      button.addEventListener('keydown', event => {
        if (!['ArrowDown', 'ArrowUp'].includes(event.key)) return;
        event.preventDefault();
        navigateFinding(event.key === 'ArrowDown' ? 1 : -1, true);
      });
      row.append(button);
      byId('finding-list').append(row);
    }
    byId('findings-section').classList.toggle('filtered-detail', visible.length === 0);
    if (focused) byId('finding-list').querySelector(`[data-finding="${focused}"]`)?.focus({preventScroll: true});
    byId('finding-list').scrollTo(scroll);
  }

  function navigateFinding(direction, focusQueue = false) {
    const visible = filteredFindings();
    const position = visible.findIndex(item => item.index === selected);
    const next = visible[position + direction];
    if (!next) return;
    selected = next.index;
    selectedNode = 2;
    offlineSimulated = false;
    renderQueue();
    renderFinding();
    if (focusQueue) byId('finding-list').querySelector(`[data-finding="${selected}"]`)?.focus();
  }

  function renderEvidence() {
    const finding = current.findings[selected];
    const step = finding.path[Math.max(0, selectedNode - 1)];
    const evidence = step.evidence;
    const authorization = finding.authorization;
    const titles = ['OIDC request', 'Workflow identity', 'Trust conditions', 'Permission statement', 'Resource capability'];
    text('evidence-title', titles[selectedNode]);
    text('evidence-kind', step.kind.replaceAll('_', ' '));
    const locations = [evidence.location, ...(evidence.supporting_locations || [])];
    const unique = new Map(locations.map(location => [locationText(location), location]));
    byId('source-locations').replaceChildren(...[...unique.values()].map(sourceLocation));
    let normalized = {from: step.source.name, to: step.target.name, confidence: evidence.confidence};
    let entries = [['Confidence', evidence.confidence], ['From', step.source.name], ['To', step.target.name]];
    if (authorization) {
      const workflow = authorization.workflow;
      const trust = authorization.trust;
      const permission = authorization.permission;
      if (selectedNode < 2) {
        normalized = {job: evidence.base_job_id || evidence.job_id, ...(Object.keys(evidence.matrix || {}).length ? {matrix: evidence.matrix} : {}), branches: evidence.branches, permissions: {'id-token': 'write'}, 'role-to-assume': evidence.role_arn, audience: evidence.audience};
        entries = [['Workflow', workflow.name], ['Action ref', evidence.action_reference], ['Evidence', 'Repository-verified configuration']];
      } else if (selectedNode === 2) {
        normalized = {Effect: 'Allow', Action: 'sts:AssumeRoleWithWebIdentity', Condition: {StringEquals: {'token.actions.githubusercontent.com:aud': trust.audience}}};
        if (['StringEquals', 'StringLike'].includes(trust.operator)) {
          normalized.Condition[trust.operator] ||= {};
          normalized.Condition[trust.operator]['token.actions.githubusercontent.com:sub'] = trust.subjects;
        }
        const alternatives = (current.controls || []).filter(control => control.id !== trust.id && control.role_name === workflow.role_arn.split('/').pop() && control.jobs.some(job => job.id === finding.path[0].target.id));
        entries = [['Requested role', workflow.role_arn], ['Provider account', trust.provider_accounts], ['Subject match', 'Exact declared branch subject'], ['Other matching trusts', alternatives.length], ['Confidence', 'Declared configuration']];
      } else {
        normalized = {Effect: 'Allow', Action: permission.provider_action, Resource: permission.resource_arn};
        entries = [['Capability', permission.provider_action], ['Source profile', 'Finite literal resource grant'], ['Confidence', 'Declared configuration']];
      }
    }
    declaration = JSON.stringify(normalized, null, 2);
    text('evidence-declaration', declaration);
    facts(byId('evidence-facts'), entries);
  }

  function renderPath() {
    const finding = current.findings[selected];
    const labels = ['OIDC', 'Job', 'Role', 'Policy', 'Secret'];
    const glyphs = ['fingerprint', 'code', 'key', 'file-code', 'server'];
    const workflow = finding.authorization?.workflow;
    const names = ['GitHub token', jobName(finding), workflow?.role_arn.split('/').pop() || finding.path[1].target.name.replace('AWS IAM role: ', ''), 'Read secret', resourceName(finding)];
    const nodes = [finding.path[0].source, ...finding.path.map(step => step.target)];
    byId('path').replaceChildren();
    nodes.forEach((node, index) => {
      const row = element('li');
      const button = element('button', undefined, 'node');
      button.type = 'button';
      button.dataset.node = String(index);
      button.setAttribute('aria-pressed', String(selectedNode === index));
      button.setAttribute('aria-label', labels[index] + ': ' + node.name);
      button.title = node.name;
      const glyph = element('span', undefined, 'node-glyph');
      glyph.append(icon(glyphs[index]));
      button.append(glyph, element('span', labels[index], 'node-label'), element('strong', names[index], 'node-name'));
      button.addEventListener('click', () => {
        selectedNode = index;
        for (const sibling of byId('path').querySelectorAll('button')) sibling.setAttribute('aria-pressed', String(sibling === button));
        renderEvidence();
      });
      row.append(button);
      byId('path').append(row);
    });
    renderEvidence();
  }

  function renderFinding() {
    if (!current?.findings.length) return;
    const finding = current.findings[selected];
    const visible = filteredFindings();
    const position = visible.findIndex(item => item.index === selected);
    text('finding-position', `${position + 1} / ${visible.length}`);
    byId('previous-finding').disabled = position <= 0;
    byId('next-finding').disabled = position >= visible.length - 1;
    text('selected-resource', resourceName(finding));
    const workflow = finding.authorization?.workflow;
    text('selected-job', `${workflow?.name || 'Workflow'} / ${workflow?.base_job_id || jobName(finding)}${Object.keys(workflow?.matrix || {}).length ? ' / ' + matrixText(workflow.matrix) : ''}`);
    text('impact-action', finding.impact.action);
    text('assumption', finding.start_condition);
    text('remediation-description', finding.remediation.description);
    const state = findingState(finding);
    text('finding-state', state === 'unknown' ? 'Change-set impact not recomputed' : state === 'incomplete' ? 'Modeled path removed; remaining access unknown' : state === 'blocked' ? 'Blocked among modeled routes' : state === 'alternate' ? 'Reachable through an alternate trust' : 'Declared capability');
    const alternatives = finding.unmodeled_alternatives || [];
    byId('alternative-warning').hidden = alternatives.length === 0;
    text('alternative-warning', `${alternatives.length} unmodeled alternative trust(s). Remaining access is unknown: ${alternatives.map(item => (item.subjects || []).join(', ') + ' at ' + locationText(item.location)).join('; ')}`);
    byId('selected-finding').classList.toggle('simulated', state === 'blocked');
    const trust = trustFor(finding);
    text('selected-control-location', trust ? locationText(trust.location) : 'Selected path trust');
    const staged = snapshot ? offlineSimulated : controls.has(controlFor(finding));
    text('stage-label', snapshot ? (offlineSimulated ? 'Show baseline' : 'Simulate removal') : (staged ? 'Undo simulation' : 'Simulate removal'));
    byId('after').setAttribute('aria-pressed', String(staged));
    byId('after').disabled = !snapshot && !controlFor(finding);
    let outcome = 'Current result: this declared path reaches the secret.';
    if (comparisonPending) outcome = 'Recomputing the selected change set...';
    else if (state === 'unknown') outcome = 'Comparison unavailable. No impact result is being claimed.';
    else if (state === 'incomplete') outcome = 'Blocked among modeled routes; remaining access unknown. The excluded alternatives were not removed.';
    else if (state === 'blocked') outcome = snapshot ? `Model only: ${finding.remediation.before_absolute_reach} -> ${finding.remediation.after_absolute_reach} reachable secrets. No policy change applied.` : 'Blocked among modeled routes. Deployed access and workload impact remain unverified.';
    else if (state === 'alternate') outcome = 'The selected removal leaves another declared trust path.';
    else if (controls.size) outcome = 'This path remains reachable after the selected removals.';
    else if (snapshot && offlineSimulated) outcome = 'The saved removal leaves an alternate modeled path.';
    text('simulation-result', outcome);
    renderPath();
    renderChanges();
  }

  function renderChanges() {
    if (!current) return;
    saveExample();
    const baseline = {reachable_findings: current.findings.length, reachable_secrets: current.summary.declared_reachable_secrets, reachable_jobs: new Set(current.findings.map(finding => finding.path[0].target.id)).size};
    const before = comparison?.before || baseline;
    const after = comparison?.after || baseline;
    const unavailable = !snapshot && (comparisonPending || controls.size > 0 && !comparison);
    text('change-count', snapshot ? (offlineSimulated ? 1 : 0) : controls.size);
    text('after-label', (snapshot ? offlineSimulated : controls.size > 0) ? 'After modeled removal' : 'Current model');
    text('before-reach', snapshot ? current.findings[selected]?.remediation.before_absolute_reach || 0 : before.reachable_findings);
    text('after-reach', snapshot ? (offlineSimulated ? current.findings[selected].remediation.after_absolute_reach : current.findings[selected]?.remediation.before_absolute_reach || 0) : unavailable ? '-' : after.reachable_findings);
    text('secret-delta', `${before.reachable_secrets} -> ${unavailable ? '-' : after.reachable_secrets}`);
    text('job-delta', `${before.reachable_jobs} -> ${unavailable ? '-' : after.reachable_jobs}`);
    text('comparison-label', snapshot ? 'Selected job / reachable secrets' : 'Reachable paths');
    text('change-status', snapshot ? 'Saved single-statement comparison.' : comparisonPending ? 'Recomputing all modeled jobs...' : unavailable ? 'Comparison unavailable. No impact result.' : controls.size ? `${comparison.blocked_findings} of ${current.findings.length} paths blocked in the model.` : 'No trust removals selected.');
    byId('changes-panel').setAttribute('aria-busy', String(comparisonPending));
    byId('export-plan').disabled = !controls.size || comparisonPending || !comparison;
    byId('before').disabled = snapshot ? !offlineSimulated : !controls.size;
    byId('rescan').disabled = comparisonPending || busy;
    byId('reset').disabled = comparisonPending || busy;
    for (const button of document.querySelectorAll('#source-panel button')) button.disabled = comparisonPending || busy;
    byId('offline-note').hidden = !snapshot;
    if (snapshot) {
      byId('changes-panel').querySelector('.impact-foot').hidden = true;
      byId('job-impact').replaceChildren();
      return;
    }
    const focused = document.activeElement?.dataset.control;
    byId('control-list').replaceChildren();
    for (const control of current.controls || []) {
      const label = element('label', undefined, 'control-choice');
      const checkbox = element('input');
      checkbox.type = 'checkbox';
      checkbox.dataset.control = control.id;
      checkbox.checked = controls.has(control.id);
      const description = element('span', undefined, 'control-copy');
      description.append(element('span', control.role_name, 'control-role'), element('span', control.subjects.map(subject => subject.split(':ref:refs/heads/')[1] || subject).join(', '), 'control-branch'), element('span', `${control.jobs.length} job(s) / ${control.location.path}:${control.location.start_line}`, 'control-meta'));
      checkbox.setAttribute('aria-label', `Remove ${control.role_name} trust for ${control.subjects.join(', ')} at line ${control.location.start_line}`);
      checkbox.addEventListener('change', () => stageControl(control.id, checkbox.checked));
      label.append(checkbox, description);
      byId('control-list').append(label);
    }
    if (focused) [...byId('control-list').querySelectorAll('input')].find(input => input.dataset.control === focused)?.focus({preventScroll: true});
    byId('job-impact').replaceChildren();
    if (comparison?.jobs.length && !comparisonPending) {
      byId('job-impact').append(element('h3', 'Reachable secrets by job'));
      const table = element('table');
      const header = element('tr');
      for (const name of ['Job', 'Before', 'After']) { const cell = element('th', name); cell.scope = 'col'; header.append(cell); }
      const head = element('thead'); head.append(header); table.append(head);
      const body = element('tbody');
      for (const job of comparison.jobs) {
        const row = element('tr');
        row.append(element('td', job.name.replace(/^GitHub Actions job: /, '')), element('td', job.before_reachable_secrets), element('td', job.after_reachable_secrets));
        body.append(row);
      }
      table.append(body);
      byId('job-impact').append(table);
    }
  }

  function stageControl(identifier, checked) {
    if (!current || snapshot || busy) return;
    if (checked) controls.add(identifier); else controls.delete(identifier);
    revision += 1;
    comparison = null;
    byId('error').hidden = true;
    recompute();
  }

  async function recompute() {
    if (comparisonPending || !current || snapshot) return;
    const baseline = current;
    const requestedRevision = revision;
    comparisonPending = true;
    renderChanges();
    renderFinding();
    try {
      const result = await request('simulate', {analysis_hash: baseline.analysis_hash, controls: [...controls].sort()});
      if (current === baseline && requestedRevision === revision) comparison = result;
    } catch (failure) {
      if (current === baseline && requestedRevision === revision) error(failure.message);
    } finally {
      comparisonPending = false;
      if (current === baseline && requestedRevision !== revision) recompute();
      else if (current === baseline) { renderQueue(); renderFinding(); }
    }
  }

  function renderFiles() {
    const query = byId('file-search').value.toLocaleLowerCase();
    byId('source-files').replaceChildren();
    for (const file of current.source_files || []) {
      if (!file.path.toLocaleLowerCase().includes(query)) continue;
      const row = element('tr');
      const source = element('td', file.path);
      source.append(element('small', `${file.size} bytes / SHA ${file.sha256.slice(0, 12)}`));
      const state = element('td');
      state.append(element('span', {parsed: 'Parsed', partial: 'Partial', unparsed: 'Unparsed'}[file.status] || file.status, 'file-state ' + file.status));
      const sourceKind = { workflow: 'GitHub Actions', cloudformation: 'CloudFormation', terraform: 'Terraform JSON' }[file.kind] || file.kind;
      row.append(source, element('td', sourceKind), state, element('td', file.fact_count), element('td', file.diagnostic_count));
      byId('source-files').append(row);
    }
    if (!byId('source-files').children.length) { const row = element('tr'); const cell = element('td', 'No source files in this view.'); cell.colSpan = 5; row.append(cell); byId('source-files').append(row); }
  }

  function renderIdentities() {
    const query = byId('identity-search').value.toLocaleLowerCase();
    const filter = byId('identity-status').value;
    const groups = new Map();
    let variants = 0;
    for (const identity of current.identity_requests || []) {
      const references = identity.references.map(reference => `${reference.context}.${reference.name}`);
      const searchable = [identity.workflow_name, identity.base_job_id, identity.role_arn, identity.action_reference, references.join(' '), matrixText(identity.matrix)].join(' ').toLocaleLowerCase();
      if (!searchable.includes(query) || filter !== 'all' && identity.status !== filter) continue;
      const key = JSON.stringify([identity.location, identity.base_job_id, identity.role_arn, identity.status, identity.reason_codes]);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(identity);
      variants += 1;
    }
    const grouped = [...groups.values()].sort((left, right) => {
      const leftKey = left[0].location.path + '/' + left[0].base_job_id;
      const rightKey = right[0].location.path + '/' + right[0].base_job_id;
      return leftKey < rightKey ? -1 : leftKey > rightKey ? 1 : left[0].location.start_line - right[0].location.start_line || left[0].location.start_column - right[0].location.start_column;
    });
    const pages = Math.max(1, Math.ceil(grouped.length / identityPageSize));
    identityPage = Math.max(0, Math.min(identityPage, pages - 1));
    text('identity-result-count', `${variants} request variants / ${grouped.length} declarations`);
    text('identity-page', `Page ${identityPage + 1} of ${pages}`);
    byId('identity-previous').disabled = identityPage === 0;
    byId('identity-next').disabled = identityPage >= pages - 1;
    const gapTitles = new Map((current.evidence_gaps || []).map(gap => [gap.code, gap.title]));
    byId('identity-rows').replaceChildren();
    for (const group of grouped.slice(identityPage * identityPageSize, (identityPage + 1) * identityPageSize)) {
      const identity = group[0];
      const row = element('tr');
      row.dataset.identityStatus = identity.status;
      const job = element('td');
      job.append(element('strong', identity.base_job_id), element('small', identity.workflow_name), element('small', `id-token: ${identity.token_permission}`));
      const role = element('td');
      if (identity.role_arn) role.append(element('code', identity.role_arn));
      else {
        const references = [...new Set(identity.references.map(reference => `${reference.context}.${reference.name}`))];
        for (const reference of references) role.append(element('code', reference));
        if (!references.length) role.append(element('span', 'No supported literal role'));
      }
      role.append(element('small', identity.action_kind === 'local-action' ? 'Local action / not evaluated' : identity.action_reference));
      const matrix = element('td');
      matrix.append(element('span', identity.matrix_status === 'unresolved' ? 'Not expanded' : `${group.length} variant${group.length === 1 ? '' : 's'}`));
      const axes = new Set(group.flatMap(item => Object.keys(item.matrix || {})));
      for (const axis of axes) matrix.append(element('small', `${axis}: ${[...new Set(group.map(item => String(item.matrix[axis] ?? '-')))].join(', ')}`));
      const state = element('td');
      state.append(element('span', identityStates[identity.status] || identity.status, 'identity-state ' + identity.status));
      for (const code of identity.reason_codes) state.append(element('small', gapTitles.get(code) || code.replaceAll('_', ' ').toLowerCase()));
      const source = element('td');
      source.append(sourceLocation(identity.location));
      if (identity.supporting_locations?.length) {
        const details = element('details');
        details.append(element('summary', 'Resolved from source'));
        for (const supporting of identity.supporting_locations) details.append(sourceLocation(supporting));
        source.append(details);
      }
      row.append(job, role, matrix, state, source);
      byId('identity-rows').append(row);
    }
    if (!grouped.length) {
      const row = element('tr'); const cell = element('td', 'No identity requests match this view.'); cell.colSpan = 5; row.append(cell); byId('identity-rows').append(row);
    }
  }

  function renderEvidenceGaps() {
    const gaps = current.evidence_gaps || [];
    text('evidence-gap-count', `${gaps.length} categories`);
    byId('evidence-gap-list').replaceChildren();
    for (const gap of gaps) {
      const entry = element('section', undefined, 'evidence-gap');
      const heading = element('div');
      heading.append(element('h4', gap.title), element('code', gap.code));
      const body = element('div');
      body.append(element('p', gap.evidence_needed));
      const references = [...new Set(gap.references.map(reference => `${reference.context}.${reference.name}`))];
      if (references.length) body.append(element('p', references.join(' / '), 'gap-references'));
      if (gap.locations.length) {
        const details = element('details');
        details.append(element('summary', `${gap.locations.length} source location${gap.locations.length === 1 ? '' : 's'}`));
        for (const source of gap.locations) details.append(sourceLocation(source));
        body.append(details);
      }
      entry.append(heading, body);
      byId('evidence-gap-list').append(entry);
    }
    if (!gaps.length) byId('evidence-gap-list').append(element('p', 'No additional evidence gaps were emitted within the selected profile. Deployed access remains unverified.', 'caveat'));
  }

  function showResult(result) {
    current = result;
    selected = -1;
    selectedNode = 2;
    controls = new Set();
    comparison = null;
    offlineSimulated = false;
    revision += 1;
    byId('report').hidden = false;
    document.body.classList.add('has-result');
    byId('empty-state').hidden = true;
    byId('export-bar').hidden = false;
    byId('rescan').hidden = snapshot;
    byId('error').hidden = true;
    byId('finding-search').value = '';
    byId('finding-status').value = 'all';
    byId('file-search').value = '';
    byId('identity-search').value = '';
    byId('identity-status').value = 'all';
    identityPage = 0;
    text('repository-name', result.repository.slug);
    text('context-label', result.repository.is_example ? 'Bundled example / not a live repository' : 'Repository investigation');
    const source = result.repository.input;
    text('source-ref', source ? `GitHub / ${source.requested_ref} / ${source.commit_sha}` : `Local snapshot / ${result.repository.snapshot_hash.slice(0, 16)}`);
    text('footer-hash', 'Analysis ' + result.analysis_hash.slice(0, 16));
    document.title = result.repository.slug + ' | Blast Radius';
    text('finding-count', result.summary.finding_count);
    text('secret-count', result.summary.declared_reachable_secrets);
    text('job-count', new Set(result.findings.map(finding => finding.path[0].target.id)).size);
    text('parsed-count', result.coverage.parsed_files);
    text('diagnostic-count', result.diagnostics.length);
    text('identity-count', (result.identity_requests || []).length);
    byId('findings-section').classList.toggle('single-finding', result.findings.length === 1);
    byId('change-options').open = !snapshot && result.findings.length > 1;
    byId('evidence-details').open = false;
    const identitySummary = result.identity_summary || {};
    text('identity-headline', `${identitySummary.workflow_jobs || 0} declared jobs / ${identitySummary.expanded_job_variants || 0} expanded variants`);
    text('identity-conclusion', result.conclusion);
    byId('identity-totals').replaceChildren();
    for (const [key, label] of [['identity_requests', 'Identity request variants'], ['unresolved_requests', 'Unresolved requests'], ['matched_trust_requests', 'Matched declared trusts'], ['unresolved_matrix_jobs', 'Unexpanded matrices']]) {
      const group = element('div'); group.append(element('dt', label), element('dd', identitySummary[key] || 0)); byId('identity-totals').append(group);
    }
    renderIdentities();
    renderEvidenceGaps();
    byId('no-proof').hidden = result.findings.length > 0;
    byId('findings-section').hidden = result.findings.length === 0;
    text('no-proof-message', result.conclusion);
    renderQueue();
    if (result.findings.length) renderFinding();
    byId('coverage').replaceChildren();
    text('coverage-headline', `${result.coverage.selected_files} selected / ${result.coverage.inventory_files ?? result.coverage.selected_files} inventoried files. ${result.coverage.out_of_profile_files ?? 0} outside the source profile.`);
    for (const [key, label] of [['inventory_files', 'Inventoried files'], ['selected_files', 'Selected files'], ['parsed_files', 'Parsed files'], ['unsupported_files', 'Unparsed files'], ['out_of_profile_files', 'Outside profile'], ['skipped_entries', 'Skipped entries'], ['terraform_hcl_files', 'Terraform HCL / not assessed']]) {
      if (result.coverage[key] === undefined) continue;
      const group = element('div'); group.append(element('dt', label), element('dd', result.coverage[key])); byId('coverage').append(group);
    }
    renderFiles();
    text('diagnostics-total', result.diagnostics.length);
    byId('diagnostics').replaceChildren();
    byId('diagnostics-panel').open = result.diagnostics.length > 0;
    for (const diagnostic of result.diagnostics) {
      const row = element('li'); row.append(element('strong', diagnostic.code), element('p', diagnostic.message));
      if (diagnostic.location) row.append(element('small', locationText(diagnostic.location)));
      byId('diagnostics').append(row);
    }
    if (!result.diagnostics.length) byId('diagnostics').append(element('li', 'No parser diagnostics within this profile.'));
    const skipped = [...(result.skipped_inputs || []), ...(source?.archive_extraction?.skipped || [])];
    text('skipped-total', skipped.length);
    byId('skipped-inputs').replaceChildren();
    for (const item of skipped) { const row = element('li'); row.append(element('strong', item.path), element('p', item.reason)); byId('skipped-inputs').append(row); }
    if (!skipped.length) byId('skipped-inputs').append(element('li', 'No acquisition skips recorded.'));
    const metadata = [['Analysis hash', result.analysis_hash], ['Source snapshot', result.repository.snapshot_hash], ['Evidence hash', result.repository.evidence_hash], ['Profile', result.profile]];
    if (source) metadata.push(['Resolved commit', source.commit_sha], ['Requested ref', source.requested_ref]);
    facts(byId('snapshot-details'), metadata);
    showView(!result.findings.length && result.identity_requests?.length ? 'identities' : 'paths');
  }

  function download(contents, format, plan = false) {
    const types = {json: 'application/json', sarif: 'application/sarif+json', md: 'text/markdown', html: 'text/html'};
    const blob = contents instanceof Blob ? contents : new Blob([contents], {type: types[format] + ';charset=utf-8'});
    const address = URL.createObjectURL(blob);
    const anchor = element('a');
    anchor.href = address;
    anchor.download = 'blast-radius-' + (plan ? 'change-request-' : '') + current.repository.slug.replace(/[^A-Za-z0-9_.-]/g, '-') + '.' + format;
    document.body.append(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(address), 1000);
  }

  for (const button of document.querySelectorAll('[data-mode]')) button.addEventListener('click', () => setMode(button.dataset.mode));
  for (const button of document.querySelectorAll('[data-view]')) {
    button.addEventListener('click', () => showView(button.dataset.view));
    button.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const views = ['paths', 'identities', 'coverage'];
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? views.length - 1 : (views.indexOf(button.dataset.view) + (event.key === 'ArrowRight' ? 1 : -1) + views.length) % views.length;
      showView(views[next], true);
    });
  }
  byId('source-toggle').addEventListener('click', () => toggleSource(byId('source-panel').hidden));
  byId('source-toggle').setAttribute('aria-label', 'Repository source');
  byId('source-toggle').title = 'Choose repository source';
  byId('rescan').addEventListener('click', () => { if (lastInput) analyze(lastInput); });
  byId('cancel-analysis').addEventListener('click', cancelAnalysis);
  byId('source-form').addEventListener('submit', event => {
    event.preventDefault();
    analyze(sourceMode === 'local' ? {source: 'local', path: byId('repository-path').value.trim(), slug: byId('repository-slug').value.trim()} : {source: 'github', url: byId('repository-url').value.trim(), ref: byId('repository-ref').value.trim() || null});
  });
  byId('example').addEventListener('click', () => analyze({source: 'example'}));
  byId('example-shared').addEventListener('click', () => analyze({source: 'example', example: 'shared'}));
  byId('review-coverage').addEventListener('click', () => showView('coverage', true));
  byId('finding-search').addEventListener('input', () => { renderQueue(); renderFinding(); });
  byId('finding-status').addEventListener('change', () => { renderQueue(); renderFinding(); });
  byId('file-search').addEventListener('input', renderFiles);
  byId('identity-search').addEventListener('input', () => { identityPage = 0; renderIdentities(); });
  byId('identity-status').addEventListener('change', () => { identityPage = 0; renderIdentities(); });
  byId('identity-previous').addEventListener('click', () => { identityPage -= 1; renderIdentities(); });
  byId('identity-next').addEventListener('click', () => { identityPage += 1; renderIdentities(); });
  byId('previous-finding').addEventListener('click', () => navigateFinding(-1));
  byId('next-finding').addEventListener('click', () => navigateFinding(1));
  byId('copy-declaration').addEventListener('click', () => copy(declaration));
  byId('before').addEventListener('click', () => {
    if (snapshot) { offlineSimulated = false; renderQueue(); renderFinding(); }
    else { controls.clear(); comparison = null; revision += 1; recompute(); }
  });
  byId('after').addEventListener('click', () => {
    if (snapshot) { offlineSimulated = !offlineSimulated; renderQueue(); renderFinding(); }
    else { const identifier = controlFor(current.findings[selected]); stageControl(identifier, !controls.has(identifier)); }
  });
  byId('reset').addEventListener('click', async () => {
    try { await request('clear', {}); lastInput = null; clearView(); saveExample(); byId('source-form').reset(); setMode('local'); toggleSource(true); byId('repository-path').focus(); }
    catch (failure) { error(failure.message); }
  });
  byId('export').addEventListener('click', async () => {
    if (!current) return;
    const format = byId('export-format').value;
    byId('export').disabled = true;
    try {
      if (snapshot) download(configuration.exports[format], format);
      else { const response = await request('export', {format, analysis_hash: current.analysis_hash}, true); download(await response.blob(), format); }
      status('Baseline report prepared.');
    } catch (failure) { error(failure.message); }
    finally { byId('export').disabled = false; }
  });
  byId('export-plan').addEventListener('click', async () => {
    if (!current || snapshot || comparisonPending || !controls.size) return;
    const format = byId('plan-format').value;
    byId('export-plan').disabled = true;
    try {
      const response = await request('export-plan', {format, analysis_hash: current.analysis_hash, controls: [...controls].sort()}, true);
      download(await response.blob(), format, true);
      status('Proposed change request prepared. Nothing applied.');
    } catch (failure) { error(failure.message); }
    finally { renderChanges(); }
  });
  if (snapshot) {
    document.body.classList.add('snapshot');
    text('session-label', 'Saved snapshot');
    byId('export-format').querySelector('[value=html]').remove();
    showResult(configuration.result);
  } else {
    try { const saved = JSON.parse(sessionStorage.getItem('br-example-review')); if (saved?.version === 1 && ['single', 'shared'].includes(saved.example)) analyze({source: 'example', example: saved.example}, saved); } catch {}
  }
  addEventListener('beforeunload', event => { if (activeOperation) cancelAnalysis(); if (busy || (!snapshot && current && !current.repository.is_example)) { event.preventDefault(); event.returnValue = ''; } });
})();