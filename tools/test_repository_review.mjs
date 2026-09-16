import assert from 'node:assert/strict';
import {spawn, spawnSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {openBrowser, ROOT} from './browser_ui.mjs';

const python = process.env.BR_PYTHON ?? [path.join(ROOT, '.venv/Scripts/python.exe'), path.join(ROOT, '.venv/bin/python')].find(filename => fs.existsSync(filename));
assert(python, 'Set BR_PYTHON to the installed analyzer interpreter.');
const artifacts = path.join(ROOT, 'results/repository-review-browser');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'br-review-check-'));
fs.mkdirSync(artifacts, {recursive: true});
fs.writeFileSync(path.join(temporary, 'broken.cfn.json'), '{');
const alternativeRepository = path.join(temporary, 'alternative-case');
fs.cpSync(path.join(ROOT, 'tests/fixtures/repositories/aws-oidc-path'), alternativeRepository, {recursive: true});
const alternativeTemplate = path.join(alternativeRepository, 'infra/identity.template.json');
const alternativeDocument = JSON.parse(fs.readFileSync(alternativeTemplate, 'utf8'));
const alternateTrusts = alternativeDocument.Resources.GitHubProductionRole.Properties.AssumeRolePolicyDocument.Statement;
const broadTrust = structuredClone(alternateTrusts[0]);
delete broadTrust.Condition.StringEquals['token.actions.githubusercontent.com:sub'];
broadTrust.Condition.StringLike = {'token.actions.githubusercontent.com:sub': 'repo:acme/payments:*'};
alternateTrusts.push(broadTrust);
fs.writeFileSync(alternativeTemplate, JSON.stringify(alternativeDocument));
const identityRepository = path.join(temporary, 'identity-case');
fs.mkdirSync(path.join(identityRepository, '.github/workflows'), {recursive: true});
const identitySteps = Array.from({length: 23}, (unused, index) => ({uses: 'aws-actions/configure-aws-credentials@v4', with: {'role-to-assume': '${{ secrets.DEPLOY_ROLE_' + String(index + 1).padStart(2, '0') + ' }}'}}));
fs.writeFileSync(path.join(identityRepository, '.github/workflows/deploy.yml'), JSON.stringify({on: {push: {branches: ['main']}}, permissions: {'id-token': 'write'}, jobs: {deploy: {strategy: {matrix: {os: ['ubuntu', 'windows']}}, steps: identitySteps}}}));
const service = spawn(python, ['-I', '-B', '-m', 'blastradius', 'review', '--port', '0', '--no-open'], {cwd: os.tmpdir(), stdio: ['ignore', 'pipe', 'pipe']});
let browser;
let serviceErrors = '';
service.stderr.on('data', data => { serviceErrors += data; });
const audits = [];

try {
  const address = await new Promise((resolve, reject) => {
    const deadline = setTimeout(() => reject(Error('Review service did not start: ' + serviceErrors)), 20000);
    service.stdout.on('data', data => {
      const match = /http:\/\/127\.0\.0\.1:\d+\//.exec(String(data));
      if (match) { clearTimeout(deadline); resolve(match[0]); }
    });
    service.on('error', reject);
    service.on('exit', code => { if (code) reject(Error('Review service exited: ' + serviceErrors)); });
  });
  browser = await openBrowser(1440, 1080);
  const discardWarnings = [];
  browser.on('Page.javascriptDialogOpening', dialog => {
    discardWarnings.push(dialog.type);
    browser.send('Page.handleJavaScriptDialog', {accept: true});
  });
  await browser.navigate(address);
  browser.errors.length = 0;
  browser.requests.length = 0;

  const waitFor = async predicate => browser.evaluate(`new Promise((resolve,reject)=>{
    const ready=()=>Boolean(${predicate});
    if(ready()){resolve(true);return;}
    const observer=new MutationObserver(()=>{if(ready()){observer.disconnect();clearTimeout(deadline);resolve(true);}});
    const deadline=setTimeout(()=>{observer.disconnect();reject(Error('UI state did not settle'));},20000);
    observer.observe(document.body,{subtree:true,attributes:true,childList:true,characterData:true});
  })`);
  const audit = async name => {
    await browser.evaluate(fs.readFileSync(path.join(ROOT, 'ui/vendor/axe.min.js'), 'utf8') + '\n;true');
    const violations = await browser.evaluate(`axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}}).then(result=>result.violations.map(item=>({id:item.id,impact:item.impact,nodes:item.nodes.map(node=>node.target)})))`);
    const layout = await browser.evaluate(`({width:innerWidth,overflow:document.documentElement.scrollWidth>innerWidth,clipped:[...document.querySelectorAll('.node')].filter(node=>node.scrollHeight>node.clientHeight+1).map(node=>node.getAttribute('aria-label')),font:document.fonts.check('16px Atkinson')})`);
    assert.equal(layout.overflow, false, name + ' overflows');
    assert.deepEqual(layout.clipped, [], name + ' clips path nodes');
    assert.equal(layout.font, true, name + ' has no bundled font');
    assert.deepEqual(violations, [], name + ': ' + JSON.stringify(violations));
    audits.push({name, width: layout.width, violations: 0});
  };

  assert.equal(await browser.evaluate(`document.getElementById('report').hidden`), true);
  await audit('desktop-empty');
  await browser.evaluate(`globalThis.__savedFetch=fetch;globalThis.fetch=(url,options)=>{
    if(String(url).endsWith('/analyze'))return new Promise(resolve=>{globalThis.__pendingAnalysis=resolve;});
    if(String(url).endsWith('/status'))return Promise.resolve(new Response(JSON.stringify({state:'running',stage:'Parsing source declarations'}),{status:200}));
    if(String(url).endsWith('/cancel')){globalThis.__pendingAnalysis(new Response(JSON.stringify({error:'Analysis cancelled. No partial result was retained.',cancelled:true}),{status:409}));return Promise.resolve(new Response('{}',{status:202}));}
    return globalThis.__savedFetch(url,options);
  };document.getElementById('example').click();`);
  await waitFor(`document.body.classList.contains('busy') && !document.getElementById('cancel-analysis').hidden`);
  await browser.evaluate(`document.getElementById('cancel-analysis').click()`);
  await waitFor(`!document.body.classList.contains('busy')`);
  assert.equal(await browser.evaluate(`document.getElementById('report').hidden`), true);
  assert.match(await browser.evaluate(`document.getElementById('activity').textContent`), /cancelled/);
  await browser.evaluate(`globalThis.fetch=globalThis.__savedFetch`);
  await browser.evaluate(`document.getElementById('example').click()`);
  await waitFor(`!document.body.classList.contains('busy') && !document.getElementById('report').hidden`);
  assert.equal(await browser.evaluate(`document.getElementById('finding-count').textContent`), '1');
  assert.match(await browser.evaluate(`document.getElementById('context-label').textContent`), /Bundled example/);
  assert.equal(await browser.evaluate(`document.getElementById('findings-section').classList.contains('single-finding')`), true);
  assert.equal(await browser.evaluate(`getComputedStyle(document.querySelector('.finding-queue')).display`), 'none');
  assert.equal(await browser.evaluate(`document.getElementById('evidence-details').open`), false);
  assert.equal(await browser.evaluate(`document.getElementById('stage-label').textContent`), 'Simulate removal');
  assert((await browser.evaluate(`document.querySelector('.titlebar').getBoundingClientRect().height`)) < 100);
  await audit('desktop-example');
  await browser.screenshot(path.join(artifacts, 'desktop.png'));
  await browser.evaluate(`document.querySelector('[data-node="4"]').click()`);
  assert.match(await browser.evaluate(`document.getElementById('source-locations').textContent`), /identity.template.json:32:17/);
  await browser.evaluate(`document.getElementById('after').click()`);
  await waitFor(`document.getElementById('changes-panel').getAttribute('aria-busy') === 'false'`);
  assert.equal(await browser.evaluate(`document.getElementById('after-reach').textContent`), '0');
  assert.equal(await browser.evaluate(`document.querySelectorAll('.simulated').length`), 1);
  await browser.navigate(address);
  await waitFor(`!document.body.classList.contains('busy') && document.getElementById('after-reach').textContent === '0'`);
  assert.equal(await browser.evaluate(`document.getElementById('change-count').textContent`), '1');
  assert.equal(await browser.evaluate(`document.getElementById('context-label').textContent.includes('Bundled example')`), true);

  await browser.evaluate(`globalThis.__download=null;const originalClick=HTMLAnchorElement.prototype.click;HTMLAnchorElement.prototype.click=function(){if(this.download){globalThis.__filename=this.download;}else{originalClick.call(this);}};const originalURL=URL.createObjectURL;URL.createObjectURL=blob=>{globalThis.__download=blob;return originalURL(blob);};`);
  for (const format of ['json', 'md', 'sarif', 'html']) {
    await browser.evaluate(`globalThis.__download=null;document.getElementById('export-format').value=${JSON.stringify(format)};document.getElementById('export').click();`);
    await waitFor(`globalThis.__download && !document.getElementById('export').disabled`);
    const contents = await browser.evaluate(`globalThis.__download.text()`);
    assert(contents.length > 100);
    assert((await browser.evaluate(`globalThis.__filename`)).endsWith('.' + format));
    fs.writeFileSync(path.join(artifacts, 'analysis.' + format), contents);
    if (format === 'json') assert.equal(JSON.parse(contents).findings[0].remediation.after_absolute_reach, 0);
    if (format === 'sarif') assert.equal(JSON.parse(contents).runs[0].results[0].kind, 'review');
  }
  await browser.evaluate(`document.getElementById('source-toggle').click();document.getElementById('repository-path').value=${JSON.stringify(alternativeRepository)};document.getElementById('repository-slug').value='acme/payments';document.getElementById('source-form').requestSubmit()`);
  await waitFor(`!document.body.classList.contains('busy') && !document.getElementById('alternative-warning').hidden`);
  assert.match(await browser.evaluate(`document.getElementById('alternative-warning').textContent`), /repo:acme\/payments:\*/);
  await browser.evaluate(`document.getElementById('after').click()`);
  await waitFor(`document.getElementById('changes-panel').getAttribute('aria-busy') === 'false'`);
  assert.equal(await browser.evaluate(`document.getElementById('after-reach').textContent`), '0');
  assert.match(await browser.evaluate(`document.getElementById('simulation-result').textContent`), /remaining access unknown/);
  assert.equal(await browser.evaluate(`getComputedStyle(document.getElementById('alternative-warning')).display === 'none'`), false);
  await audit('unmodeled-alternative');
  await browser.evaluate(`document.getElementById('source-toggle').click();document.getElementById('example-shared').click()`);
  await waitFor(`!document.body.classList.contains('busy') && document.getElementById('finding-count').textContent === '5'`);
  assert.equal(await browser.evaluate(`document.querySelectorAll('#control-list input').length`), 3);
  assert.equal(await browser.evaluate(`document.getElementById('job-count').textContent`), '3');
  await browser.evaluate(`document.querySelectorAll('#finding-list button')[1].click();document.querySelector('[data-node="2"]').click()`);
  assert.match(await browser.evaluate(`document.getElementById('evidence-declaration').textContent`), /token.actions.githubusercontent.com:sub/);
  await audit('desktop-shared-baseline');
  await browser.screenshot(path.join(artifacts, 'shared-baseline.png'));
  await browser.evaluate(`document.querySelector('#control-list input[aria-label*="github-production"]').click()`);
  await waitFor(`document.getElementById('changes-panel').getAttribute('aria-busy') === 'false' && document.getElementById('change-count').textContent === '1'`);
  assert.equal(await browser.evaluate(`document.getElementById('after-reach').textContent`), '5');
  assert.match(await browser.evaluate(`document.getElementById('change-status').textContent`), /0 of 5 paths blocked/);
  await browser.evaluate(`document.querySelector('#control-list input[aria-label*="github-production"]:not(:checked)').click()`);
  await waitFor(`document.getElementById('changes-panel').getAttribute('aria-busy') === 'false' && document.getElementById('change-count').textContent === '2'`);
  assert.equal(await browser.evaluate(`document.getElementById('after-reach').textContent`), '1');
  assert.equal(await browser.evaluate(`document.querySelectorAll('.finding-choice[data-state="blocked"]').length`), 4);
  assert.equal(await browser.evaluate(`document.querySelectorAll('#job-impact tbody tr').length`), 3);
  await browser.evaluate(`document.getElementById('finding-status').value='blocked';document.getElementById('finding-status').dispatchEvent(new Event('change'));document.getElementById('finding-search').value='database';document.getElementById('finding-search').dispatchEvent(new Event('input'));`);
  assert.equal(await browser.evaluate(`document.querySelectorAll('#finding-list button').length`), 2);
  await browser.evaluate(`document.getElementById('finding-search').value='not-present';document.getElementById('finding-search').dispatchEvent(new Event('input'));`);
  assert.equal(await browser.evaluate(`document.getElementById('queue-empty').hidden`), false);
  await browser.evaluate(`document.getElementById('finding-search').value='';document.getElementById('finding-search').dispatchEvent(new Event('input'));document.getElementById('finding-status').value='all';document.getElementById('finding-status').dispatchEvent(new Event('change'));`);
  for (const format of ['md', 'json']) {
    await browser.evaluate(`globalThis.__download=null;document.getElementById('plan-format').value=${JSON.stringify(format)};document.getElementById('export-plan').click()`);
    await waitFor(`globalThis.__download && !document.getElementById('export-plan').disabled`);
    const contents = await browser.evaluate(`globalThis.__download.text()`);
    fs.writeFileSync(path.join(artifacts, 'change-request.' + format), contents);
    if (format === 'json') { assert.equal(JSON.parse(contents).blocked_findings, 4); assert.equal(JSON.parse(contents).applied, false); }
    else assert.match(contents, /Reachable findings: 5 -> 1/);
  }
  await audit('desktop-shared-change-set');
  await browser.screenshot(path.join(artifacts, 'shared-change-set.png'));
  await browser.evaluate(`document.querySelector('#control-list input[aria-label*="github-publisher"]').click();document.querySelector('#control-list input[aria-label*="github-publisher"]').click()`);
  await waitFor(`document.getElementById('changes-panel').getAttribute('aria-busy') === 'false' && document.getElementById('change-count').textContent === '2'`);
  assert.equal(await browser.evaluate(`document.getElementById('after-reach').textContent`), '1');
  await browser.evaluate(`globalThis.__originalFetch=globalThis.fetch;globalThis.fetch=(url,options)=>String(url).endsWith('/simulate')?Promise.reject(Error('Synthetic comparison outage')):globalThis.__originalFetch(url,options);document.querySelector('#control-list input[aria-label*="github-publisher"]').click()`);
  await waitFor(`document.getElementById('changes-panel').getAttribute('aria-busy') === 'false' && !document.getElementById('error').hidden`);
  assert.equal(await browser.evaluate(`document.getElementById('after-reach').textContent`), '-');
  assert.equal(await browser.evaluate(`document.getElementById('export-plan').disabled`), true);
  assert.equal(await browser.evaluate(`document.querySelectorAll('.finding-choice[data-state="unknown"]').length`), 5);
  await browser.evaluate(`globalThis.fetch=globalThis.__originalFetch;document.querySelector('#control-list input[aria-label*="github-publisher"]').click()`);
  await waitFor(`document.getElementById('changes-panel').getAttribute('aria-busy') === 'false' && document.getElementById('after-reach').textContent === '1'`);
  await browser.evaluate(`document.getElementById('tab-coverage').click()`);
  assert.equal(await browser.evaluate(`document.querySelectorAll('#source-files tr').length`), 2);
  await browser.evaluate(`document.getElementById('file-search').value='identity';document.getElementById('file-search').dispatchEvent(new Event('input'))`);
  assert.equal(await browser.evaluate(`document.querySelectorAll('#source-files tr').length`), 1);
  await audit('desktop-file-coverage');
  await browser.screenshot(path.join(artifacts, 'coverage.png'));
  await browser.evaluate(`document.getElementById('file-search').value='';document.getElementById('file-search').dispatchEvent(new Event('input'));document.getElementById('tab-paths').click()`);
  await browser.send('Emulation.setDeviceMetricsOverride', {width: 1280, height: 900, deviceScaleFactor: 1, mobile: false});
  await audit('laptop-shared-change-set');
  await browser.send('Emulation.setDeviceMetricsOverride', {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
  await audit('mobile-shared-change-set');
  await browser.evaluate(`document.getElementById('review-main').scrollIntoView()`);
  await browser.screenshot(path.join(artifacts, 'mobile.png'));
  await browser.send('Emulation.setDeviceMetricsOverride', {width: 320, height: 740, deviceScaleFactor: 1, mobile: true});
  await audit('small-mobile-shared-change-set');
  await browser.evaluate(`document.getElementById('tab-coverage').click()`);
  await audit('small-mobile-file-coverage');
  await browser.send('Emulation.setDeviceMetricsOverride', {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
  await browser.evaluate(`document.querySelector('[data-mode="local"]').click();document.getElementById('repository-path').value=${JSON.stringify(temporary)};document.getElementById('repository-slug').value='acme/empty';document.getElementById('source-form').requestSubmit();`);
  await waitFor(`!document.body.classList.contains('busy') && !document.getElementById('report').hidden`);
  assert.equal(await browser.evaluate(`document.getElementById('finding-count').textContent`), '0');
  assert.match(await browser.evaluate(`document.getElementById('no-proof-message').textContent`), /not evidence/);
  assert.equal(await browser.evaluate(`document.getElementById('diagnostics-panel').open`), true);
  await audit('mobile-no-proof');
  await browser.evaluate(`document.getElementById('repository-path').value=${JSON.stringify(path.join(temporary, 'missing'))};document.getElementById('source-form').requestSubmit();`);
  await waitFor(`!document.body.classList.contains('busy') && !document.getElementById('error').hidden`);
  assert.equal(await browser.evaluate(`document.getElementById('export-bar').hidden`), true);
  await audit('mobile-error');
  await browser.evaluate(`document.getElementById('repository-path').value=${JSON.stringify(identityRepository)};document.getElementById('repository-slug').value='acme/identity-case';document.getElementById('source-form').requestSubmit()`);
  await waitFor(`!document.body.classList.contains('busy') && document.getElementById('repository-name').textContent === 'acme/identity-case' && !document.getElementById('report').hidden`);
  assert.equal(await browser.evaluate(`document.getElementById('identity-count').textContent`), '46');
  assert.equal(await browser.evaluate(`document.getElementById('tab-identities').getAttribute('aria-selected')`), 'true');
  assert.match(await browser.evaluate(`document.getElementById('identity-rows').textContent`), /secrets.DEPLOY_ROLE/);
  assert.match(await browser.evaluate(`document.getElementById('evidence-gap-list').textContent`), /No supported IAM role declarations/);
  assert.match(await browser.evaluate(`document.getElementById('identity-conclusion').textContent`), /not evidence/);
  assert.equal(await browser.evaluate(`document.querySelectorAll('#identity-rows tr[data-identity-status]').length`), 20);
  await browser.evaluate(`document.getElementById('identity-next').click()`);
  assert.equal(await browser.evaluate(`document.querySelectorAll('#identity-rows tr[data-identity-status]').length`), 3);
  assert.match(await browser.evaluate(`document.getElementById('identity-page').textContent`), /Page 2 of 2/);
  assert.equal(await browser.evaluate(`document.getElementById('identity-next').disabled`), true);
  await browser.evaluate(`document.getElementById('identity-previous').click()`);
  assert.equal(await browser.evaluate(`document.querySelectorAll('#identity-rows tr[data-identity-status]').length`), 20);
  await browser.evaluate(`document.getElementById('tab-identities').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}))`);
  assert.equal(await browser.evaluate(`document.getElementById('tab-coverage').getAttribute('aria-selected')`), 'true');
  await browser.evaluate(`document.getElementById('tab-coverage').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowLeft',bubbles:true}))`);
  assert.equal(await browser.evaluate(`document.getElementById('tab-identities').getAttribute('aria-selected')`), 'true');
  await audit('mobile-unresolved-identities');
  await browser.send('Emulation.setDeviceMetricsOverride', {width: 320, height: 740, deviceScaleFactor: 1, mobile: true});
  await audit('small-mobile-unresolved-identities');
  await browser.send('Emulation.setDeviceMetricsOverride', {width: 1440, height: 1080, deviceScaleFactor: 1, mobile: false});
  await audit('desktop-unresolved-identities');
  await browser.screenshot(path.join(artifacts, 'identities.png'));
  await browser.evaluate(`document.getElementById('identity-search').value='DEPLOY_ROLE_23';document.getElementById('identity-search').dispatchEvent(new Event('input'))`);
  assert.equal(await browser.evaluate(`document.querySelectorAll('#identity-rows tr[data-identity-status]').length`), 1);
  assert.match(await browser.evaluate(`document.getElementById('identity-result-count').textContent`), /2 request variants \/ 1 declarations/);
  await browser.evaluate(`document.getElementById('identity-search').value='not-present';document.getElementById('identity-search').dispatchEvent(new Event('input'))`);
  assert.equal(await browser.evaluate(`document.querySelectorAll('#identity-rows tr[data-identity-status]').length`), 0);
  await browser.evaluate(`document.getElementById('identity-search').value='';document.getElementById('identity-search').dispatchEvent(new Event('input'));document.getElementById('identity-status').value='matched-trust';document.getElementById('identity-status').dispatchEvent(new Event('change'))`);
  assert.equal(await browser.evaluate(`document.querySelectorAll('#identity-rows tr[data-identity-status]').length`), 0);
  assert(browser.requests.filter(address => /^https?:/.test(address)).every(request => request.startsWith(address)), 'Unexpected external browser request');
  assert.deepEqual(browser.errors, []);

  await browser.send('Emulation.setDeviceMetricsOverride', {width: 1440, height: 1080, deviceScaleFactor: 1, mobile: false});
  browser.requests.length = 0;
  await browser.navigate(pathToFileURL(path.join(artifacts, 'analysis.html')).href);
  await audit('offline-snapshot');
  assert.equal(await browser.evaluate(`document.getElementById('finding-count').textContent`), '1');
  assert.equal(await browser.evaluate(`document.getElementById('after-label').textContent`), 'Current model');
  await browser.evaluate(`document.getElementById('after').click()`);
  assert.equal(await browser.evaluate(`document.getElementById('after-reach').textContent`), '0');
  assert.equal(await browser.evaluate(`document.getElementById('stage-label').textContent`), 'Show baseline');
  assert.match(await browser.evaluate(`document.getElementById('simulation-result').textContent`), /Model only: 1 -> 0 reachable secrets/);
  assert.equal(browser.requests.some(request => /^https?:/.test(request)), false, 'Offline report made a network request');
  assert(discardWarnings.includes('beforeunload'), 'Leaving a real-source review must warn about losing the visible session');
  assert.deepEqual(browser.errors, []);
  assert.equal(serviceErrors, '');
  const report = {audits, exports: ['json', 'md', 'sarif', 'html'], change_request_exports: ['md', 'json'], evidence_selection: true, queue_filtering: true, file_coverage: true, unresolved_identity_evidence: true, identity_filtering: true, simulation: '1 -> 0', alternate_trust: '5 -> 5', shared_change_set: '5 -> 1', offline_network_requests: 0, page_errors: browser.errors};
  fs.writeFileSync(path.join(artifacts, 'checks.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  if (browser) await browser.close();
  if (service.pid) {
    if (process.platform === 'win32') spawnSync('taskkill', ['/pid', String(service.pid), '/t', '/f'], {stdio: 'ignore'});
    else service.kill('SIGTERM');
  }
  fs.rmSync(temporary, {recursive: true, force: true});
}