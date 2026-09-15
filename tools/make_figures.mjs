import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {openBrowser,ROOT} from './browser_ui.mjs';
const folder=path.join(ROOT,'figures');fs.mkdirSync(folder,{recursive:true});
const browser=await openBrowser();const outputs=[];
try{
 for(const view of ['disc','path','treemap','lorenz','histogram','models','whatif','privacy']){
  await browser.evaluate(`BRApp.selectView('${['path'].includes(view)?'disc':['lorenz','histogram'].includes(view)?'distribution':view}');`);
  if(view==='models')await browser.evaluate(`document.querySelector('[data-model="strict"]').click()`);
  if(view==='whatif')await browser.evaluate(`document.querySelector('[data-model="default"]').click();BRApp.removeBinding('shared-2')`);
  for(const column of ['single','double']){
   const source=await browser.evaluate(`BRApp.exportFigure('svg','${column}',false,'${view}')`);
   const repeated=await browser.evaluate(`BRApp.exportFigure('svg','${column}',false,'${view}')`);assert.equal(source,repeated,view+' SVG byte determinism');
   const record={view,column,files:[],snapshot:await browser.evaluate('BRApp.result().snapshot_hash')};
   for(const format of ['svg','png','pdf']){
    const value=format==='svg'?source:await browser.evaluate(`BRApp.exportFigure('${format}','${column}',false,'${view}')`);
    const bytes=format==='svg'?Buffer.from(value):Buffer.from(value,'base64'),name=`${view}-${column}.${format}`;
    if(format==='png')assert.equal(bytes.subarray(1,4).toString(),'PNG');
    if(format==='pdf')assert.equal(bytes.subarray(0,5).toString(),'%PDF-');
    fs.writeFileSync(path.join(folder,name),bytes);record.files.push({name,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
   }
   outputs.push(record);console.log(view+' '+column+' exported');
  }
 }
 fs.writeFileSync(path.join(folder,'manifest.json'),JSON.stringify({synthetic:true,renderer:'Visual Vocabulary v0.1',outputs,errors:browser.errors},null,2)+'\n');
 const captions=['# Paper 1 Figure Captions','','All figures are illustrative synthetic engine outputs, not observed enterprise risk. Single-column width88.9mm; double-column182mm. Open fonts and complete stamps are embedded.',''];
 for(const record of outputs)captions.push(`## ${record.view} / ${record.column}`,'',`Source snapshot: \`${record.snapshot}\`. SVG/PNG/PDF use the same shared tokens and renderer. ${record.view==='disc'?'Disc area encodes canonical radius; rings encode minimum escalation cost; points encode unique resource-action pairs.':record.view==='path'?'Stations and edges show the chosen shortest-escalation witness; dashed segments are explicit illustrative assumptions.':record.view==='treemap'?'Area encodes absolute credential reach; color is principal type; p95 outline is not a risk class.':record.view==='lorenz'?'Cumulative summed credential-pair exposure, not the union of exposed resources.':record.view==='histogram'?'Fixed canonical-radius bins by principal type; threshold is a declared analytic parameter.':record.view==='models'?'Default versus strict reach under different attacker assumptions, not estimated attack probabilities.':record.view==='whatif'?'One evaluated binding removal, fixed universe; not a globally optimal remediation plan.':'Exact structural count silhouette; the local payload is not anonymous and no submission occurs.'}`,'');
 fs.writeFileSync(path.join(folder,'CAPTIONS.md'),captions.join('\n'));console.log(JSON.stringify({figures:outputs.length,files:outputs.reduce((sum,item)=>sum+item.files.length,0),svg_repeat_checks:outputs.length,script_errors:browser.errors.length}));
}finally{await browser.close();}