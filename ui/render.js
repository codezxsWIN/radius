(function (root) {
  'use strict';
  let tokens, font = '';
  const escape = value => String(value ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  const numeric = value => { if (value == null) return null; const parts = String(value).split('/'); return Number(parts[0]) / Number(parts[1] ?? 1); };
  const fixed = value => Number(value).toFixed(3);
  const percent = value => value == null ? 'undefined' : (numeric(value) * 100).toFixed(2) + '%';
  const label = value => String(value).replaceAll('_', ' ');
  const text = (x, y, value, extra = '') => `<text x="${fixed(x)}" y="${fixed(y)}" ${extra}>${escape(value)}</text>`;
  function wrap(value,limit){const lines=[];let line='';for(const word of String(value).split(' ')){if(line.length+word.length+1>limit&&line){lines.push(line);line=word;}else line+=(line?' ':'')+word;}if(line)lines.push(line);return lines;}
  function configure(value, fontData = '') { tokens = value; font = fontData; }
  function stamp(result, options = {}) {
    return `Illustrative | ${result.snapshot_hash} | engine ${result.engine_version} | schema ${result.schema_version} | ${result.constraint_model} | k=${result.parameters.step_bound}, threshold=${result.parameters.threshold} | ${result.generated_at} | ${tokens.version}${options.redacted ? ' | pseudonyms' : ''}`;
  }
  function frame(title, description, body, result, options = {}) {
    const width = options.width ?? (options.compact?420:tokens.figure.width), height = options.height ?? (options.compact?700:tokens.figure.height);
    const stampLines = [
      `Illustrative | ${result.constraint_model} | ${tokens.version} | ${options.redacted ? 'pseudonyms' : 'original synthetic names'}`,
      `Snapshot ${result.snapshot_hash}`,
      `Engine ${result.engine_version} | schema ${result.schema_version} | k=${result.parameters.step_bound} | threshold=${result.parameters.threshold} | ${result.generated_at}`
    ];
    const footer=options.compact?[`Illustrative / ${result.constraint_model}`,`Snapshot ${result.snapshot_hash.slice(0,32)}`,result.snapshot_hash.slice(32),`Engine ${result.engine_version} / schema ${result.schema_version}`,`k=${result.parameters.step_bound}; threshold=${result.parameters.threshold}`,result.generated_at,`${tokens.version}${options.redacted?' / pseudonyms':''}`]:stampLines;
    const footerHeight=footer.length*16+24;
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="group" aria-label="${escape(title)}" data-view="${escape(options.view ?? '')}"><title>${escape(title)}</title><desc>${escape(description)} ${escape(stamp(result, options))}</desc><defs><style>${font ? `@font-face{font-family:'Atkinson Hyperlegible';src:url(data:font/ttf;base64,${font}) format('truetype');}` : ''}text{font-family:'Atkinson Hyperlegible',sans-serif;font-size:14px;fill:${tokens.color.ink};letter-spacing:0} .small{font-size:12px;fill:${tokens.color.muted}} .title{font-size:22px} .mark:focus{outline:3px solid ${tokens.color.focus};outline-offset:4px} .grid{stroke:${tokens.color.line};stroke-width:1} .axis{stroke:${tokens.color.muted};stroke-width:1}</style><pattern id="uncertain" patternUnits="userSpaceOnUse" width="7" height="7"><path d="M0 7L7 0" stroke="${tokens.color.unknown}" stroke-width="1"/></pattern></defs><rect width="100%" height="100%" fill="${tokens.color.surface}"/>${text(28, 36, title, 'class="title"')}${wrap(description,options.compact?54:110).map((line,index)=>text(28,58+index*16,line,'class="small"')).join('')}${body}<path d="M28 ${height-footerHeight}H${width-28}" class="grid"/>${footer.map((line,index) => text(28, height-footerHeight+20+index*16, line, 'class="small"')).join('')}</svg>`;
  }
  function discGeometry(radius, maxStep, reach,referenceRadius=tokens.figure.fullDiscRadius) {
    const outer = referenceRadius * Math.sqrt(numeric(radius));
    const groups = new Map();
    for (const item of reach) { const step = item.rank[0]; if (!groups.has(step)) groups.set(step, []); groups.get(step).push(item); }
    const marks = [];
    for (const [step, items] of [...groups].sort((left,right) => left[0]-right[0])) {
      items.sort((left,right) => JSON.stringify(left.pair).localeCompare(JSON.stringify(right.pair), 'en'));
      items.forEach((item,index) => { const angle = 2*Math.PI*index/items.length - Math.PI/2; const distance = outer * (step+0.86)/(maxStep+1); marks.push({...item, x:distance*Math.cos(angle), y:distance*Math.sin(angle)}); });
    }
    return {outer, marks};
  }
  function disc(result, options) {
    const record = options.record ?? result.credentials[0];
    if (!record) return frame('Credential reach', 'No credential population', '', result, options);
    const reach = options.reach ?? [], maxStep = Math.max(0, ...reach.map(item=>item.rank[0]));
    const referenceRadius=options.compact?150:tokens.figure.fullDiscRadius;
    const geometry = discGeometry(record.canonical_radius, maxStep, reach,referenceRadius), centerX = options.compact?210:320, centerY = options.compact?255:294;
    const nodes = new Map(result.snapshot.nodes.map(node=>[node.id,node]));
    const scrub = options.step ?? maxStep;
    let body = `<circle cx="${centerX}" cy="${centerY}" r="${referenceRadius}" fill="none" stroke="${tokens.color.line}" stroke-dasharray="4 5"/>`;
    body += `<circle data-role="blast-disc" data-radius="${numeric(record.canonical_radius)}" cx="${centerX}" cy="${centerY}" r="${fixed(geometry.outer)}" fill="#edf0f1" stroke="${tokens.color.ink}" stroke-width="1.5"/>`;
    for (let step=0;step<=maxStep;step++) {
      const ring = geometry.outer*(step+1)/(maxStep+1);
      body += `<circle cx="${centerX}" cy="${centerY}" r="${fixed(ring)}" fill="none" stroke="${tokens.color.line}"/>${text(centerX+ring+6,centerY-8,`k${step}`,'class="small"')}`;
    }
    for (const item of geometry.marks) {
      const node = nodes.get(item.pair[0]), sensitivity = Number(node.sensitivity), visible = item.rank[0] <= scrub;
      const name = options.names?.[node.id] ?? node.name;
      const color = tokens.color.sensitivity[Math.min(4,Math.floor(sensitivity*5))];
      const caption = `${name} / ${item.pair[1]}; first step ${item.rank[0]}; sensitivity ${sensitivity}`;
      body += `<circle class="mark" role="button" tabindex="0" aria-label="${escape(caption)}" data-node="${escape(node.id)}" data-action="${escape(item.pair[1])}" data-step="${item.rank[0]}" cx="${fixed(centerX+item.x)}" cy="${fixed(centerY+item.y)}" r="5" fill="${visible?color:tokens.color.surface}" stroke="${visible?tokens.color.ink:tokens.color.line}" stroke-width="1.2"><title>${escape(caption)}</title></circle>`;
    }
    if(options.compact){body+=text(28,446,percent(record.canonical_radius),'style="font-size:30px"')+text(227,441,`${record.absolute_reach} / ${record.universe_size} pairs`)+text(227,463,`${reach.filter(item=>item.rank[0]<=scrub).length} through k${scrub}`,'class="small"')+text(28,491,'Area = canonical radius. One point = one pair.','class="small"');tokens.color.sensitivity.forEach((color,index)=>{body+=`<rect x="${28+index*66}" y="515" width="66" height="12" fill="${color}"/>`;});body+=text(28,548,'Sensitivity 0')+text(350,548,'1');}
    else{body += text(560,150,percent(record.canonical_radius),'style="font-size:38px"') + text(560,179,`${record.absolute_reach} / ${record.universe_size} pairs`);body += text(560,212,'Disc area = canonical radius','class="small"') + text(560,240,`${reach.filter(item=>item.rank[0]<=scrub).length} pairs through k${scrub}`,'class="small"');body += text(560,286,'Sensitivity','class="small"');tokens.color.sensitivity.forEach((color,index)=>{body+=`<rect x="${560+index*40}" y="300" width="40" height="12" fill="${color}"/>`;});body += text(560,333,'0')+text(755,333,'1')+text(560,368,'One point = one reachable pair','class="small"')+text(560,391,'Outer guide = full universe','class="small"');}
    return frame('Credential reach',options.names?.[record.principal_id] ?? record.name,body,result,{...options,view:'disc'});
  }
  function pathView(result, options = {}) {
    const record=options.record ?? result.credentials[0], explanation=record?.explanation;
    if (!explanation) return frame('Explanatory path','No reachable witness under this model',text(30,130,'No path is invented for a blocked or zero-reach credential.'),result,{...options,view:'path',height:310});
    const nodes=new Map(result.snapshot.nodes.map(node=>[node.id,node]));
    const edges=explanation.steps, ids=[edges[0].source,...edges.map(edge=>edge.target)];
    const columns=options.compact?2:4, rows=Math.ceil(ids.length/columns), height=(options.compact?290:230)+rows*122;
    const position=index=>({x:(options.compact?60:65)+(index%columns)*(options.compact?205:220),y:132+Math.floor(index/columns)*122});
    let body='';
    edges.forEach((edge,index)=>{
      const start=position(index),end=position(index+1), escalation=['can_assume','can_read_secret'].includes(edge.kind) || (edge.kind==='assigned' && nodes.get(edge.target)?.eligible);
      const approximate=Boolean(options.approximations?.[edge.id]);
      const middle=(start.y+end.y)/2;
      const geometry=start.y===end.y?`M${start.x} ${start.y}H${end.x}`:`M${start.x} ${start.y}V${middle}H${end.x}V${end.y}`;
      body+=`<path d="${geometry}" fill="none" stroke="${escalation?tokens.color.accent:tokens.color.muted}" stroke-width="${escalation?4:2}" ${approximate?'stroke-dasharray="7 5"':''}/>`;
      body+=text(start.y===end.y?(start.x+end.x)/2-36:options.compact?150:300,start.y===end.y?start.y-18:middle-8,label(edge.kind),'class="small"');
      if ((edge.constraints??[]).length) body+=`<path d="M${start.x+80} ${start.y-12}v24" stroke="${tokens.color.accent}" stroke-width="4"/>`;
    });
    ids.forEach((id,index)=>{
      const node=nodes.get(id),point=position(index), name=options.names?.[id]??node?.name??id;
      body+=`<g class="mark" role="button" tabindex="0" aria-label="${escape(name+' provenance')}" data-node="${escape(id)}"><circle cx="${point.x}" cy="${point.y}" r="9" fill="${tokens.color.surface}" stroke="${tokens.color.ink}" stroke-width="2"/>${text(point.x-36,point.y+29,name.length>25?name.slice(0,23)+'..':name,'style="font-size:12px"')}${text(point.x-36,point.y+47,label(node?.kind??''),'class="small"')}<title>${escape(name)}</title></g>`;
    });
    return frame('Explanatory path',`${explanation.escalation_steps} escalation steps / ${explanation.graph_hops} graph hops / ${explanation.action}`,body,result,{...options,view:'path',height});
  }
  function treemap(result,options={}) {
    const records=options.records??result.credentials, nonzero=records.filter(record=>record.absolute_reach>0);
    const count=records.length, p95=result.statistics.canonical_radius.p95;
    if (!nonzero.length) return frame('Credential population','All credentials have zero reach',text(28,130,'Zero-area credentials are listed in the data table.'),result,{...options,view:'treemap'});
    const hierarchy=root.d3.hierarchy({children:nonzero}).sum(record=>record.absolute_reach??0).sort((left,right)=>right.value-left.value || (left.data.credential_id??'').localeCompare(right.data.credential_id??''));
    root.d3.treemap().size([options.compact?364:784,options.compact?400:390]).padding(0).round(false)(hierarchy);
    let body='';
    for (const leaf of hierarchy.leaves()) {
      const record=leaf.data,x=28+leaf.x0,y=95+leaf.y0,width=leaf.x1-leaf.x0,height=leaf.y1-leaf.y0,color=tokens.color.categorical[record.principal_type];
      const outline=record.canonical_radius>=p95;
      const name=options.names?.[record.principal_id]??record.name;
      body+=`<g class="mark" role="button" tabindex="0" aria-label="${escape(name+', '+record.absolute_reach+' reachable pairs'+(outline?', at or above tenant p95':''))}" data-credential="${escape(record.credential_id)}"><rect data-reach="${record.absolute_reach}" x="${fixed(x)}" y="${fixed(y)}" width="${fixed(width)}" height="${fixed(height)}" fill="${color}" stroke="white" stroke-width="1"/>`;
      if(outline&&width>6&&height>6)body+=`<rect x="${fixed(x+3)}" y="${fixed(y+3)}" width="${fixed(width-6)}" height="${fixed(height-6)}" fill="none" stroke="#101820" stroke-width="2"/>`;
      if(width>90&&height>48)body+=text(x+10,y+22,name.replace(/^Fictional /,'').slice(0,Math.max(6,Math.floor(width/8)-2)),`style="fill:${record.principal_type==='human_user'?'#ffffff':'#101820'};font-size:12px"`)+text(x+10,y+41,`${record.absolute_reach} pairs`,`style="fill:${record.principal_type==='human_user'?'#ffffff':'#101820'};font-size:13px"`);
      body+=`<title>${escape(name)}: ${record.absolute_reach}/${record.universe_size}; ${percent(record.canonical_radius)}</title></g>`;
    }
    body+=wrap(`${count-nonzero.length} zero-area credentials in table. Outline: radius >= ${percent(p95)} tenant p95.`,options.compact?54:110).map((line,index)=>text(28,options.compact?526+index*16:514+index*16,line,'class="small"')).join('');
    return frame('Credential population','Area = absolute reach; color = principal type; overlapping reach is counted per credential.',body,result,{...options,view:'treemap'});
  }
  function lorenz(result,options={}) {
    const values=(options.records??result.credentials).map(record=>record.absolute_reach).sort((left,right)=>left-right),sum=values.reduce((total,value)=>total+value,0),count=values.length;
    const left=options.compact?55:80,top=options.compact?110:95,width=options.compact?315:660,height=options.compact?300:350;
    let cumulative=0,body='';
    const points=[[left,top+height]];
    values.forEach((value,index)=>{cumulative+=value;points.push([left+(index+1)/count*width,top+height-(sum?cumulative/sum:0)*height]);});
    [0,.25,.5,.75,1].forEach(value=>{body+=`<path d="M${left} ${top+height-value*height}H${left+width}" class="grid"/>${text(left-44,top+height-value*height+4,Math.round(value*100)+'%','class="small"')}${text(left+value*width-9,top+height+24,Math.round(value*100)+'%','class="small"')}`;});
    body+=`<path d="M${left} ${top+height}L${left+width} ${top}" stroke="${tokens.color.muted}" stroke-dasharray="5 5" fill="none"/><path d="${points.map((point,index)=>(index?'L':'M')+point.join(' ')).join('')}" fill="none" stroke="${tokens.color.accent}" stroke-width="3"/>`;
    const topCount=Math.ceil(count*.1),share=sum?values.slice(-topCount).reduce((total,value)=>total+value,0)/sum:0;
    const gini=sum&&count?values.reduce((total,value,index)=>total+(2*(index+1)-count-1)*value,0)/(count*sum):count?0:null;
    body+=wrap(`Gini ${gini==null?'undefined':gini.toFixed(4)} | top ${topCount}/${count} credentials hold ${percent(share)} of summed reach.`,options.compact?47:110).map((line,index)=>text(options.compact?28:80,options.compact?470+index*20:494+index*20,line)).join('');body+=text(options.compact?28:80,options.compact?538:516,options.compact?'Axes: credentials / summed credential-pair reach.':'Horizontal: cumulative credentials. Vertical: cumulative credential-pair reach.','class="small"');
    return frame('Privilege distribution','Lorenz curve; summed credential reach is not unique tenant surface.',body,result,{...options,view:'lorenz'});
  }
  function histogram(result,options={}) {
    const kinds=Object.keys(tokens.color.categorical).filter(kind=>kind!=='group'),records=options.records??result.credentials;
    const bins=Array.from({length:10},()=>Object.fromEntries(kinds.map(kind=>[kind,0])));
    records.forEach(record=>bins[Math.min(9,Math.floor(record.canonical_radius*10))][record.principal_type]++);
    const maximum=Math.max(1,...bins.flatMap(bin=>Object.values(bin))),left=options.compact?50:64,top=110,width=options.compact?335:710,height=options.compact?300:345;
    const scale=value=>(options.log?Math.log1p(value)/Math.log1p(maximum):value/maximum)*height;
    let body='';
    for(let count=0;count<=maximum;count+=Math.max(1,Math.ceil(maximum/4))) body+=`<path d="M${left} ${top+height-scale(count)}H${left+width}" class="grid"/>${text(left-28,top+height-scale(count)+4,count,'class="small"')}`;
    bins.forEach((bin,index)=>{
      kinds.forEach((kind,typeIndex)=>{const barWidth=width/10/6,x=left+index*width/10+typeIndex*barWidth,y=top+height-scale(bin[kind]);body+=`<rect role="img" aria-label="${label(kind)}; bin ${index/10} to ${(index+1)/10}; ${bin[kind]} credentials" x="${fixed(x)}" y="${fixed(y)}" width="${fixed(barWidth-1)}" height="${fixed(scale(bin[kind]))}" fill="${tokens.color.categorical[kind]}"><title>${escape(label(kind))}: ${bin[kind]}</title></rect>`;});
      body+=text(left+index*width/10,top+height+24,(index/10).toFixed(1),'class="small"');
    });
    const threshold=numeric(result.parameters.threshold),x=left+threshold*width;
    body+=`<path d="M${x} ${top-10}V${top+height}" stroke="${tokens.color.ink}" stroke-dasharray="5 4"/>${text(x+7,top-17,`Threshold ${percent(threshold)}`,'class="small"')}`;
    body+=wrap(`Vertical: credential count${options.log?' on log(1 + count) scale':''}. Horizontal: canonical radius; final bin includes 1.`,options.compact?52:110).map((line,index)=>text(options.compact?28:64,options.compact?475+index*18:514+index*18,line,'class="small"')).join('');
    return frame('Radius histogram','Grouped by principal type; each count comes from this result population.',body,result,{...options,view:'histogram'});
  }
  function comparison(before,after,options={}) {
    const originals=new Map(before.credentials.map(record=>[record.credential_id,record]));
    const rows=(options.records??after.credentials).map(record=>({record,before:originals.get(record.credential_id)?.canonical_radius??0,after:record.canonical_radius})).sort((left,right)=>Math.abs(right.after-right.before)-Math.abs(left.after-left.before)||left.record.credential_id.localeCompare(right.record.credential_id)).slice(0,options.compact?7:12);
    let body='';
    rows.forEach((item,index)=>{
      const y=108+index*(options.compact?57:31),name=options.names?.[item.record.principal_id]??item.record.name;
      body+=text(28,y+9,name.replace(/^Fictional /,'').slice(0,options.compact?42:26),'style="font-size:12px"');
      const x=options.compact?28:247,barY=options.compact?y+24:y-7,barWidth=options.compact?215:370;
      body+=`<rect x="${x}" y="${barY}" width="${fixed(item.before*barWidth)}" height="8" fill="#bac4c8"/><rect x="${x}" y="${barY+10}" width="${fixed(item.after*barWidth)}" height="8" fill="${item.after>item.before?tokens.color.increase:tokens.color.decrease}"/>`;
      body+=text(options.compact?258:641,options.compact?y+36:y+9,`${percent(item.before)} / ${percent(item.after)}`,'class="small"')+(options.compact?'':text(765,y+9,((item.after-item.before)*100).toFixed(1),'class="small"'));
    });
    body+=wrap('Grey: before. Colored: after. All credentials and percentage-point deltas are in the data table.',options.compact?54:110).map((line,index)=>text(28,options.compact?535+index*16:514+index*16,line,'class="small"')).join('');
    return frame(options.title??'Counterfactual reach',`${before.constraint_model} baseline / ${after.constraint_model} comparison`,body,after,{...options,view:options.view??'whatif'});
  }
  function silhouette(result,summary,options={}) {
    const entries=Object.entries(summary.node_counts),maximum=Math.max(1,...entries.map(([,count])=>count));
    let body='';
    entries.forEach(([kind,count],index)=>{const y=130+index*60;body+=text(32,y+17,label(kind))+`<rect x="${options.compact?135:160}" y="${y}" width="${fixed(count/maximum*(options.compact?220:540))}" height="25" fill="${tokens.color.muted}"/>`+text(options.compact?367:715,y+18,count);});
    body+=wrap('No names, IDs, paths or credential values. Exact structure can still identify a tenant.',options.compact?50:110).map((line,index)=>text(32,470+index*18,line,options.compact?'class="small"':'')).join('')+text(32,options.compact?535:500,options.compact?'Local dry run. Not anonymous. No submission.':'Local dry run only. Submission disabled. This payload is not anonymous.','class="small"');
    return frame('Structural silhouette','This is everything in the local dry-run payload; no submission occurs.',body,result,{...options,view:'privacy'});
  }
  const api = {configure,escape,numeric,percent,label,text,frame,stamp,discGeometry,disc,pathView,treemap,lorenz,histogram,comparison,silhouette};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.BRVisual = api;
})(typeof globalThis === 'undefined' ? this : globalThis);