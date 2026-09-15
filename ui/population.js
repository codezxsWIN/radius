(function(root){
 'use strict';
 const cache=new Map();
 function aggregate(records){const groups=new Map();for(const record of records){const bin=Math.min(19,Math.floor(record.canonical_radius*20)),key=record.principal_type+':'+bin;if(!groups.has(key))groups.set(key,{credential_id:key,principal_id:key,name:record.principal_type.replaceAll('_',' ')+` / ${bin*.05}..${(bin+1)*.05}`,principal_type:record.principal_type,absolute_reach:0,universe_size:record.universe_size,canonical_radius:0,count:0,bin});const group=groups.get(key);group.absolute_reach+=record.absolute_reach;group.canonical_radius=Math.max(group.canonical_radius,record.canonical_radius);group.count++;}return[...groups.values()];}
 function layout(records,width,height){const hierarchy=d3.hierarchy({children:records.filter(record=>record.absolute_reach>0)}).sum(record=>record.absolute_reach??0).sort((left,right)=>right.value-left.value||(left.data.credential_id??'').localeCompare(right.data.credential_id??''));d3.treemap().size([width,height]).padding(0).round(false)(hierarchy);return hierarchy.leaves().map(leaf=>({...leaf.data,x:leaf.x0,y:leaf.y0,width:leaf.x1-leaf.x0,height:leaf.y1-leaf.y0}));}
 function mount(canvas,overlay,result,records,tokens,onSelect){
  const start=performance.now(),aggregated=records.length>10000,shown=aggregated?aggregate(records):records,width=840,height=500,ratio=Math.min(2,devicePixelRatio||1);
  canvas.width=overlay.width=width*ratio;canvas.height=overlay.height=height*ratio;
  const key=result.snapshot_hash+':'+result.constraint_model+':'+records.length+':'+records[0]?.credential_id+':'+records.at(-1)?.credential_id;
  const rectangles=cache.get(key)??layout(shown,width,height);cache.set(key,rectangles);
  const context=canvas.getContext('2d'),highlight=overlay.getContext('2d');context.scale(ratio,ratio);highlight.scale(ratio,ratio);context.fillStyle='#fff';context.fillRect(0,0,width,height);
  for(const item of rectangles){context.fillStyle=tokens.color.categorical[item.principal_type];context.fillRect(item.x,item.y,item.width,item.height);if(item.width>5&&item.height>5){context.strokeStyle='#fff';context.lineWidth=.5;context.strokeRect(item.x,item.y,item.width,item.height);}}
  let current=null;
  const hover=(x,y)=>{current=rectangles.find(item=>x>=item.x&&x<item.x+item.width&&y>=item.y&&y<item.y+item.height);highlight.clearRect(0,0,width,height);if(current){highlight.strokeStyle='#111';highlight.lineWidth=2;highlight.strokeRect(current.x+1,current.y+1,Math.max(0,current.width-2),Math.max(0,current.height-2));}return current;};
  overlay.addEventListener('pointermove',event=>{const box=overlay.getBoundingClientRect(),item=hover((event.clientX-box.left)/box.width*width,(event.clientY-box.top)/box.height*height);const info=document.querySelector('#canvas-info');if(info)info.textContent=item?`${item.name}: ${item.absolute_reach} summed pairs${aggregated?`; ${item.count} credentials in this type/radius cell`:''}`:'No reached pair in this area.';});
  overlay.addEventListener('click',()=>{if(current)onSelect(current,aggregated);});
  overlay.addEventListener('keydown',event=>{if(event.key==='Enter'){const item=current??rectangles[0];if(item)onSelect(item,aggregated);}});
  const evidence={credential_count:records.length,rendered_marks:rectangles.length,aggregated,initial_layout_draw_ms:performance.now()-start,hover};root.BRPopulation.last=evidence;return evidence;
 }
 root.BRPopulation={aggregate,layout,mount,last:null};
})(globalThis);