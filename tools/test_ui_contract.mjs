import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {openBrowser,ROOT} from './browser_ui.mjs';
const browser=await openBrowser(),checks=[];
const check=(name,condition)=>{assert.ok(condition,name);checks.push({name,passed:true});};
try{
 check('exact structural summary parity',await browser.evaluate(`JSON.stringify(BRApp.summary())===JSON.stringify(BR_INPUT.files[BRApp.state.dataset.structural_summary])||BRReference.canonical(BRApp.summary())===BRReference.canonical(BR_INPUT.files[BRApp.state.dataset.structural_summary])`));
 const evidence=await browser.evaluate(`(()=>{const source=BRApp.result(),record=source.credentials.find(item=>item.credential_id===BRApp.state.selected);return {boundedCaption:document.querySelector('#metric-strip [data-definition="step_bounded_radius"] small').textContent,boundedPairs:BRApp.inspect().filter(item=>item.rank[0]<=source.parameters.step_bound).length,universe:record.universe_size,sensitivityCaption:document.querySelector('#metric-strip [data-definition="sensitivity_weighted_radius"] small').textContent,actionCaption:document.querySelector('#metric-strip [data-definition="action_weighted_radius"] small').textContent,exact:record.exact,narrative:BRApp.narrative(),model:source.constraint_model,hash:source.snapshot_hash,engine:source.engine_version,schema:source.schema_version,generated:source.generated_at,provenance:record.explanation.steps[0].provenance};})()`);
 check('bounded metric caption uses bounded pair count',evidence.boundedCaption===`${evidence.boundedPairs} / ${evidence.universe} pairs`);
 check('weighted metric captions identify exact weighted ratios',evidence.sensitivityCaption===`Exact weighted ratio ${evidence.exact.sensitivity}`&&evidence.actionCaption===`Exact weighted ratio ${evidence.exact.action}`);
 check('path narrative retains model and result provenance',[`Illustrative / synthetic`,`Model: ${evidence.model}`,`Snapshot SHA-256: ${evidence.hash}`,`Engine: ${evidence.engine}`,`Schema: ${evidence.schema}`,evidence.generated].every(value=>evidence.narrative.includes(value)));
 check('path narrative retains complete edge provenance',Object.values(evidence.provenance).every(value=>evidence.narrative.includes(value)));
 const clipboard=await browser.evaluate(`(async()=>{
	 const descriptor=Object.getOwnPropertyDescriptor(navigator,'clipboard'),reports=[];
	 try{
		 for(const mode of ['unavailable','denied','available']){
			 let copied;
			 const service=mode==='unavailable'?undefined:{writeText:async text=>{if(mode==='denied')throw new DOMException('Denied for test','NotAllowedError');copied=text;}};
			 Object.defineProperty(navigator,'clipboard',{configurable:true,value:service});
			 const button=document.querySelector('#copy-narrative');button.focus();
			 const expected=BRApp.narrative(),success=await BRApp.copyNarrative(),dialog=document.querySelector('#evidence-dialog'),field=document.querySelector('#narrative-copy');
			 reports.push({mode,success,copied:copied===expected,fallback:dialog.open&&field?.value===expected&&field.selectionStart===0&&field.selectionEnd===expected.length&&document.activeElement===field});
			if(mode==='unavailable')reports.at(-1).audit=(await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations.map(item=>item.id);
			 if(dialog.open)document.querySelector('#close-dialog').click();
			 reports.at(-1).focusRestored=document.activeElement===button;
		 }
	 }finally{if(descriptor)Object.defineProperty(navigator,'clipboard',descriptor);else delete navigator.clipboard;}
	 return reports;
 })()`);
 for(const item of clipboard)check('evidence copy '+item.mode,item.mode==='available'?item.success&&item.copied&&item.focusRestored:!item.success&&item.fallback&&item.focusRestored);
 check('manual evidence-copy dialog has no accessibility violations',clipboard.find(item=>item.mode==='unavailable').audit.length===0);
 const pseudonyms=await browser.evaluate(`(()=>{const source=BRApp.result(),original=source.snapshot.nodes.map(node=>node.name);document.querySelector('#redact').click();const text=BRApp.narrative(),response={stable:text===BRApp.narrative(),namesHidden:original.every(name=>!text.includes(name)),hashRetained:text.includes(source.snapshot_hash),disclosed:text.includes('not anonymous')};document.querySelector('#redact').click();return response;})()`);
 check('pseudonymized narrative is deterministic and explicitly non-anonymous',pseudonyms.stable&&pseudonyms.namesHidden&&pseudonyms.hashRetained&&pseudonyms.disclosed);
 const noPath=await browser.evaluate(`(()=>{
	 const fixture=BR_INPUT.manifest.fixtures.find(item=>item.valid&&BR_INPUT.files[item.models.default].credentials.some(record=>!record.explanation));
	 if(!fixture)throw Error('A valid no-path fixture is required');
	 BRApp.selectView('playground');const picker=document.querySelector('#fixture-select');picker.value=fixture.id;picker.dispatchEvent(new Event('change',{bubbles:true}));
	 const source=BRApp.result(),record=source.credentials.find(item=>!item.explanation);BRApp.state.selected=record.credential_id;BRApp.render();
	 const text=BRApp.narrative(),response={noPath:text.includes('No reachable explanatory path under the selected model.'),qualified:text.includes('Illustrative / synthetic')&&text.includes(source.snapshot_hash)&&text.includes('Model: '+source.constraint_model)};
	 BRApp.selectView('disc');return response;
 })()`);
 check('no-path evidence retains the result context',noPath.noPath&&noPath.qualified);
 await browser.evaluate(`BRApp.selectView('conformance')`);
 const unavailableExport=await browser.evaluate(`(async()=>{let rejected=false;try{await BRApp.exportFigure('svg','double',false);}catch(error){rejected=error.message.includes('No exportable figure');}return {rejected,disabled:[...document.querySelectorAll('#export-svg,#export-png,#export-pdf')].every(button=>button.disabled)};})()`);
 check('views without a figure disable and reject figure exports',unavailableExport.rejected&&unavailableExport.disabled);
 const exportSelection=await browser.evaluate(`(async()=>{
	 BRApp.selectView('disc');let picker=document.querySelector('#figure-kind');if(!picker)return false;
	 picker.value='path';picker.dispatchEvent(new Event('change',{bubbles:true}));
	 const path=await BRApp.exportFigure('svg','single',false),expectedPath=await BRApp.exportFigure('svg','single',false,'path');
	 BRApp.selectView('distribution');picker=document.querySelector('#figure-kind');picker.value='histogram';picker.dispatchEvent(new Event('change',{bubbles:true}));
	 const histogram=await BRApp.exportFigure('svg','single',false),expectedHistogram=await BRApp.exportFigure('svg','single',false,'histogram');
	 BRApp.selectView('disc');return path===expectedPath&&histogram===expectedHistogram;
 })()`);
 check('exported figure follows the explicit figure selector',exportSelection);
 const invalidExport=await browser.evaluate(`(async()=>{const rejected=[];for(const [format,column,message] of [['tiff','single','Unsupported export format'],['svg','poster','Unsupported figure width']]){try{await BRApp.exportFigure(format,column,false,'disc');rejected.push(false);}catch(error){rejected.push(error.message.includes(message));}}return rejected.every(Boolean);})()`);
 check('unsupported export formats and dimensions are rejected',invalidExport);
 const sizes=await browser.evaluate(`(()=>{const svg=BRApp.svg('disc',{compact:true}),parsed=new DOMParser().parseFromString(svg,'image/svg+xml');return {viewBox:parsed.documentElement.getAttribute('viewBox'),hash:parsed.documentElement.textContent.includes(BRApp.result().snapshot_hash.slice(32)),font:svg.includes('data:font/ttf;base64,')};})()`);check('compact figure has embedded font and full hash',sizes.viewBox==='0 0 420 700'&&sizes.hash&&sizes.font);
 await browser.evaluate(`document.querySelector('#step-back').click()`);const step=await browser.evaluate('BRApp.state.step');await browser.evaluate(`document.querySelector('#step-next').click()`);check('step controls advance minimum-cost ring',await browser.evaluate('BRApp.state.step')===step+1);
 await browser.send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
 await browser.evaluate(`document.querySelector('#play').click()`);check('reduced motion retains final reachable state',await browser.evaluate('BRApp.state.playing===false&&BRApp.state.step===Math.max(...BRApp.inspect().map(item=>item.rank[0]))'));
 await browser.evaluate(`BRApp.selectView('models');document.querySelector('[data-model="strict"]').focus();document.querySelector('[data-model="strict"]').click()`);check('model focus remains on selected control',await browser.evaluate(`document.activeElement.dataset.model==='strict'`));
 check('narrative tracks the currently selected model',await browser.evaluate(`BRApp.narrative().includes('Model: strict')&&BRApp.narrative().includes(BRApp.result().snapshot_hash)`));
 const deltas=await browser.evaluate(`({before:BR_INPUT.files[BRApp.state.dataset.models.default].statistics.canonical_radius.share_above_threshold,after:BRApp.result().statistics.canonical_radius.share_above_threshold,table:document.querySelector('#view-content table').textContent})`);check('model statistic table uses default baseline',deltas.table.includes((deltas.after-deltas.before).toFixed(4)));
 await browser.evaluate(`document.querySelector('[data-model="default"]').click();BRApp.selectView('playground');document.querySelector('#fixture-select').value='BR-033';document.querySelector('#fixture-select').dispatchEvent(new Event('change',{bubbles:true}))`);check('invalid fixture suppresses all metric figures',await browser.evaluate(`BRApp.state.editorInvalid&&document.querySelectorAll('#metric-strip button').length===0&&document.querySelectorAll('#view-content .chart-shell svg').length===0`));
 await browser.evaluate(`document.querySelector('#fixture-select').value='BR-001';document.querySelector('#fixture-select').dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('[data-edit="node"]').click()`);check('resource addition changes denominator without adding reach',await browser.evaluate('BRApp.result().credentials[0].absolute_reach===1&&BRApp.result().credentials[0].universe_size===5'));
 await browser.evaluate(`document.querySelector('[data-edit="edge"]').click()`);check('grant addition recomputes reach',await browser.evaluate('BRApp.result().credentials[0].absolute_reach===2'));
 await browser.evaluate(`document.querySelector('[data-edit="constraint"]').click()`);check('device constraint blocks edited grant path',await browser.evaluate('BRApp.result().credentials[0].absolute_reach===0'));
 await browser.evaluate(`BRApp.selectView('whatif');document.querySelector('#add-binding').click();document.querySelector('#add-principal').value='principal-00000';document.querySelector('#add-resource').value='resource-00000';document.querySelector('#add-action').value='read_secret';document.querySelector('#add-form').requestSubmit()`);check('binding addition preserves universe and produces local result',await browser.evaluate(`BRApp.state.preview?.engine_version==='0.1.0-js-reference'&&BRApp.result().universe_size===BRApp.state.baseline.universe_size`));
 await browser.evaluate(`BRApp.state.preview=null;BRApp.state.baseline=null;BRApp.selectView('incidents');document.querySelector('#incident-select').value='circleci-2023';document.querySelector('#incident-select').dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('[data-model="session-theft-aware"]').click()`);check('session theft reconstruction reaches represented resource',await browser.evaluate('BRApp.result().credentials[0].absolute_reach===1'));
 await browser.evaluate(`document.querySelector('#incident-control').click()`);check('fresh independent approval cuts session path',await browser.evaluate('BRApp.result().credentials[0].absolute_reach===0'));
 const audit=await browser.evaluate(`axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}}).then(result=>result.violations.map(item=>({id:item.id,impact:item.impact})))`);
 check('workflow final state has no accessibility findings',audit.length===0);
 check('workflow has no browser exceptions',browser.errors.length===0);
 check('workflow has no network dependencies',browser.requests.filter(url=>/^https?:/.test(url)).length===0);
 const result={checks,passed:checks.length,errors:browser.errors,audit};fs.writeFileSync(path.join(ROOT,'ui/reports/contract-tests.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{await browser.close();}