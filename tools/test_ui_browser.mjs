import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {openBrowser,ROOT} from './browser_ui.mjs';
const folder=path.join(ROOT,'ui/reports/screenshots');fs.mkdirSync(folder,{recursive:true});
const report={browser:null,view_checks:[],accessibility:[],regressions:[],interaction:[],network_requests:[],errors:[]};
const browser=await openBrowser();
try{
 report.browser=browser.version;
 for(const view of ['disc','treemap','distribution','models','whatif','privacy','playground','incidents','conformance']){
  const state=await browser.evaluate(`(()=>{BRApp.selectView('${view}');return{view:BRApp.state.view,svg:document.querySelectorAll('#view-content svg').length,heading:document.querySelector('#view-heading').textContent,overflow:document.documentElement.scrollWidth>innerWidth};})()`);
  assert.equal(state.view,view);assert.equal(state.overflow,false);report.view_checks.push(state);
  const audit=await browser.evaluate(`axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}}).then(result=>({violations:result.violations.map(item=>({id:item.id,impact:item.impact,nodes:item.nodes.map(node=>({target:node.target,html:node.html.slice(0,250)}))})),passes:result.passes.length}))`);
  report.accessibility.push({view,viewport:'desktop',...audit});
  await browser.evaluate('scrollTo(0,0);document.activeElement.blur();');
  const first=await browser.screenshot(path.join(folder,view+'-desktop.png'));
  await browser.evaluate('BRApp.render();document.activeElement.blur();');
  const second=await browser.screenshot(path.join(folder,view+'-desktop-repeat.png'));
  report.regressions.push({view,viewport:'desktop',byte_identical:first.equals(second),first_sha256:createHash('sha256').update(first).digest('hex'),second_sha256:createHash('sha256').update(second).digest('hex')});
 }
 await browser.evaluate(`BRApp.selectView('disc');document.querySelector('[data-model="strict"]').click();`);
 report.interaction.push(await browser.evaluate(`({test:'model-switch',model:BRApp.result().constraint_model,selected_pairs:BRApp.result().credentials.find(item=>item.credential_id===BRApp.state.selected)?.absolute_reach})`));
 await browser.evaluate(`document.querySelector('[data-model="default"]').click();document.querySelector('[data-node]').dispatchEvent(new MouseEvent('click',{bubbles:true}));`);
 assert.equal(await browser.evaluate('document.querySelector("#evidence-dialog").open'),true);report.interaction.push({test:'provenance-dialog',passed:true});
 await browser.evaluate(`document.querySelector('#close-dialog').click();document.querySelector('#agent-lens').click();`);
 assert.equal(await browser.evaluate('BRApp.filtered().every(item=>item.principal_type!=="human_user")'),true);report.interaction.push({test:'nhi-filter',passed:true});
 await browser.evaluate(`document.querySelector('#agent-lens').click();BRApp.selectView('whatif');`);
 await browser.evaluate(`BRApp.removeBinding('shared-2')`);
 report.interaction.push(await browser.evaluate(`({test:'binding-removal',before:BRApp.state.baseline.statistics.canonical_radius.p95,after:BRApp.result().statistics.canonical_radius.p95,universe_fixed:BRApp.state.baseline.universe_size===BRApp.result().universe_size})`));
 await browser.evaluate(`BRApp.state.preview=null;BRApp.state.baseline=null;BRApp.selectView('disc');`);
 await browser.send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
 for(const view of ['disc','treemap','distribution','models','whatif','privacy','playground','incidents','conformance']){
  await browser.evaluate(`BRApp.selectView('${view}');scrollTo(0,0);document.activeElement.blur();`);
  assert.equal(await browser.evaluate('document.documentElement.scrollWidth<=innerWidth'),true,view+' mobile overflow');
  const first=await browser.screenshot(path.join(folder,view+'-mobile.png'));await browser.evaluate('BRApp.render();document.activeElement.blur();');const second=await browser.screenshot(path.join(folder,view+'-mobile-repeat.png'));
  report.regressions.push({view,viewport:'mobile',byte_identical:first.equals(second),first_sha256:createHash('sha256').update(first).digest('hex'),second_sha256:createHash('sha256').update(second).digest('hex')});
  const audit=await browser.evaluate(`axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}}).then(result=>({violations:result.violations.map(item=>({id:item.id,impact:item.impact,nodes:item.nodes.map(node=>({target:node.target,html:node.html.slice(0,200)}))})),passes:result.passes.length}))`);
  report.accessibility.push({view,viewport:'mobile',...audit});
 }
 report.network_requests=browser.requests.filter(url=>/^https?:/.test(url));report.errors=browser.errors;
 report.summary={viewports:2,view_checks:report.view_checks.length,accessibility_runs:report.accessibility.length,critical:report.accessibility.reduce((sum,item)=>sum+item.violations.filter(rule=>rule.impact==='critical').length,0),violations:report.accessibility.reduce((sum,item)=>sum+item.violations.length,0),visual_regressions:report.regressions.length,identical:report.regressions.filter(item=>item.byte_identical).length,network_requests:report.network_requests.length,script_errors:report.errors.length};
 fs.writeFileSync(path.join(ROOT,'ui/reports/browser-tests.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report.summary));
 assert.equal(report.summary.violations,0,'Visual lab accessibility violations');
 assert.equal(report.summary.identical,report.summary.visual_regressions,'Repeated rendering changed screenshots');
 assert.deepEqual(report.errors,[],'Visual lab browser exceptions');
 assert.deepEqual(report.network_requests,[],'Offline lab performed a network request');
}finally{await browser.close();}