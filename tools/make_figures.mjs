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
     const source=await browser.evaluate(`BRApp.exportFigure('svg','${column}',false,'${view}').then(source=>{globalThis.BR_EXPORT_SOURCE=source;return source;})`);
   const repeated=await browser.evaluate(`BRApp.exportFigure('svg','${column}',false,'${view}')`);assert.equal(source,repeated,view+' SVG byte determinism');
     const geometry=await browser.evaluate(`(async()=>{
        const parsed=new DOMParser().parseFromString(BR_EXPORT_SOURCE,'image/svg+xml');if(parsed.querySelector('parsererror'))throw Error('Invalid exported SVG');
        const figure=parsed.documentElement,viewBox=figure.getAttribute('viewBox').split(/\\s+/).map(Number),widthMm=parseFloat(figure.getAttribute('width')),heightMm=parseFloat(figure.getAttribute('height'));
        const host=document.createElement('div');host.style.cssText='position:fixed;left:-10000px;top:0';const root=document.importNode(figure,true);host.attachShadow({mode:'open'}).append(root);document.body.append(host);
        try{
         await document.fonts.ready;const bounds=root.getBoundingClientRect(),texts=[...root.querySelectorAll('text')];
         const clipped=texts.filter(text=>{const box=text.getBoundingClientRect();return box.width>0&&(box.left<bounds.left-1||box.right>bounds.right+1||box.top<bounds.top-1||box.bottom>bounds.bottom+1);}).map(text=>text.textContent);
         const minFontPoints=Math.min(...texts.map(text=>parseFloat(getComputedStyle(text).fontSize)*widthMm/viewBox[2]*72/25.4));
         const hash=BRApp.result().snapshot_hash,content=figure.textContent;
        const labelBoxes=[...root.querySelectorAll('g[data-node] text')].map(text=>text.getBBox());
        const labelCrossings=[...root.querySelectorAll('[data-witness-edge]')].filter(edge=>{for(let distance=0;distance<=edge.getTotalLength();distance+=2){const point=edge.getPointAtLength(distance);if(labelBoxes.some(box=>point.x>box.x-1&&point.x<box.x+box.width+1&&point.y>box.y-1&&point.y<box.y+box.height+1))return true;}return false;}).map(edge=>edge.getAttribute('data-witness-edge'));
        return {widthMm,heightMm,viewBox,clipped,labelCrossings,minFontPoints,embeddedFont:BR_EXPORT_SOURCE.includes('data:font/ttf;base64,'),fullHash:content.includes(hash.slice(0,32))&&content.includes(hash.slice(32)),qualified:content.includes('Illustrative')&&content.includes(BRApp.result().constraint_model),rasterDpi:BR_INPUT.tokens.figure.rasterDpi};
        }finally{host.remove();}
     })()`);
     assert.equal(geometry.widthMm,column==='single'?88.9:182,view+' physical width');
     assert.ok(Math.abs(geometry.heightMm-geometry.widthMm*geometry.viewBox[3]/geometry.viewBox[2])<0.0001,view+' physical aspect ratio');
     assert.deepEqual(geometry.clipped,[],view+' clipped SVG text');
    assert.deepEqual(geometry.labelCrossings,[],view+' connector crosses a station label');
     assert.ok(geometry.minFontPoints>=5.99,view+' minimum six-point figure text');
     assert.ok(geometry.embeddedFont&&geometry.fullHash&&geometry.qualified,view+' portable font and provenance');
     const record={view,column,files:[],snapshot:await browser.evaluate('BRApp.result().snapshot_hash'),validation:{svg_repeat_identical:true,...geometry}};
   for(const format of ['svg','png','pdf']){
    const value=format==='svg'?source:await browser.evaluate(`BRApp.exportFigure('${format}','${column}',false,'${view}')`);
    const bytes=format==='svg'?Buffer.from(value):Buffer.from(value,'base64'),name=`${view}-${column}.${format}`;
        if(format==='png'){
         assert.deepEqual(bytes.subarray(0,8),Buffer.from([137,80,78,71,13,10,26,10]));
         const width=bytes.readUInt32BE(16),height=bytes.readUInt32BE(20);
         assert.equal(width,Math.round(geometry.widthMm/25.4*geometry.rasterDpi),name+' pixel width');
         assert.equal(height,Math.round(geometry.heightMm/25.4*geometry.rasterDpi),name+' pixel height');
         const painted=await browser.evaluate(`(async()=>{const image=new Image();image.src='data:image/png;base64,${value}';await image.decode();const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;const context=canvas.getContext('2d');context.drawImage(image,0,0);const pixels=context.getImageData(0,0,canvas.width,canvas.height).data;let count=0;for(let offset=0;offset<pixels.length;offset+=16)if(pixels[offset]<245||pixels[offset+1]<245||pixels[offset+2]<245)count++;return count;})()`);
         assert.ok(painted>100,name+' nonblank raster');record.validation.png={width,height,painted_samples:painted};
        }
        if(format==='pdf'){
         const text=bytes.toString('latin1');assert.equal(text.slice(0,5),'%PDF-');assert.ok(text.trimEnd().endsWith('%%EOF'),name+' complete PDF');
         const mediaBox=/\/MediaBox\s*\[\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*\]/.exec(text);
         assert.ok(mediaBox,name+' PDF page dimensions');
         const widthMm=(Number(mediaBox[3])-Number(mediaBox[1]))*25.4/72,heightMm=(Number(mediaBox[4])-Number(mediaBox[2]))*25.4/72;
         assert.ok(Math.abs(widthMm-geometry.widthMm)<0.01&&Math.abs(heightMm-geometry.heightMm)<0.01,name+' physical PDF size');
         assert.ok(text.includes('/FontFile2'),name+' embedded TrueType font');record.validation.pdf={widthMm,heightMm,embedded_font:true};
        }
    fs.writeFileSync(path.join(folder,name),bytes);record.files.push({name,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
   }
   outputs.push(record);console.log(view+' '+column+' exported');
  }
 }
 assert.deepEqual(browser.errors,[],'No browser exceptions during figure export');
 assert.deepEqual(browser.requests.filter(url=>/^https?:/.test(url)),[],'No external figure dependencies');
 fs.writeFileSync(path.join(folder,'manifest.json'),JSON.stringify({synthetic:true,renderer:'Visual Vocabulary v0.1',outputs,errors:browser.errors},null,2)+'\n');
 const captions=['# Paper 1 Figure Captions','','All figures are illustrative synthetic engine outputs, not observed enterprise risk. Single-column width88.9mm; double-column182mm. Open fonts and complete stamps are embedded.',''];
 for(const record of outputs)captions.push(`## ${record.view} / ${record.column}`,'',`Source snapshot: \`${record.snapshot}\`. SVG/PNG/PDF use the same shared tokens and renderer. ${record.view==='disc'?'Disc area encodes canonical radius; rings encode minimum escalation cost; points encode unique resource-action pairs.':record.view==='path'?'Stations and edges show the chosen shortest-escalation witness; dashed segments are explicit illustrative assumptions.':record.view==='treemap'?'Area encodes absolute credential reach; color is principal type; p95 outline is not a risk class.':record.view==='lorenz'?'Cumulative summed credential-pair exposure, not the union of exposed resources.':record.view==='histogram'?'Fixed canonical-radius bins by principal type; threshold is a declared analytic parameter.':record.view==='models'?'Default versus strict reach under different attacker assumptions, not estimated attack probabilities.':record.view==='whatif'?'One evaluated binding removal, fixed universe; not a globally optimal remediation plan.':'Exact structural count silhouette; the local payload is not anonymous and no submission occurs.'}`,'');
 fs.writeFileSync(path.join(folder,'CAPTIONS.md'),captions.join('\n'));console.log(JSON.stringify({figures:outputs.length,files:outputs.reduce((sum,item)=>sum+item.files.length,0),svg_repeat_checks:outputs.length,script_errors:browser.errors.length}));
}finally{await browser.close();}