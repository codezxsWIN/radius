import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),tokens=JSON.parse(fs.readFileSync(path.join(root,'ui/tokens.json'),'utf8'));
const matrices={protanopia:[[.152286,1.052583,-.204868],[.114503,.786281,.099216],[-.003882,-.048116,1.051998]],deuteranopia:[[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]],tritanopia:[[1.255528,-.076749,-.178779],[-.078411,.930809,.147602],[.004733,.691367,.303900]]};
const linear=value=>value<=.04045?value/12.92:((value+.055)/1.055)**2.4;
const gamma=value=>value<=.0031308?12.92*value:1.055*value**(1/2.4)-.055;
const rgb=hex=>hex.match(/[0-9a-f]{2}/gi).map(value=>linear(parseInt(value,16)/255));
const hex=values=>'#'+values.map(value=>Math.round(Math.max(0,Math.min(1,gamma(value)))*255).toString(16).padStart(2,'0')).join('');
const transform=(color,matrix)=>matrix.map(row=>Math.max(0,Math.min(1,row.reduce((sum,value,index)=>sum+value*rgb(color)[index],0))));
const lab=values=>{const xyz=[[.4124564,.3575761,.1804375],[.2126729,.7151522,.0721750],[.0193339,.1191920,.9503041]].map(row=>row.reduce((sum,value,index)=>sum+value*values[index],0));const reference=[.95047,1,1.08883],f=xyz.map((value,index)=>{const ratio=value/reference[index];return ratio>.008856?Math.cbrt(ratio):7.787*ratio+16/116;});return[116*f[1]-16,500*(f[0]-f[1]),200*(f[1]-f[2])];};
const delta=(first,second)=>Math.hypot(...first.map((value,index)=>value-second[index]));
const categories=Object.entries(tokens.color.categorical).filter(([name])=>name!=='group');
const report={method:'Machado et al. 2009 severity100 matrices; linear sRGB; CIE76 Delta E diagnostic',source:'https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html',criterion:'Categorical minimum DeltaE >=10; sequential lightness must increase. Labels and icons remain mandatory, not color alone.',simulations:{}};
for(const [name,matrix] of Object.entries(matrices)){
  const colors=categories.map(([kind,color])=>({kind,color:hex(transform(color,matrix)),lab:lab(transform(color,matrix))}));let minimum=Infinity,pair=[];
  colors.forEach((first,index)=>colors.slice(index+1).forEach(second=>{const distance=delta(first.lab,second.lab);if(distance<minimum){minimum=distance;pair=[first.kind,second.kind];}}));
  const sensitivity=tokens.color.sensitivity.map(color=>({color:hex(transform(color,matrix)),lightness:lab(transform(color,matrix))[0]}));
  report.simulations[name]={categorical_min_delta_e:minimum,closest_pair:pair,categorical_pass:minimum>=10,sensitivity_lightness_monotonic:sensitivity.every((item,index)=>!index||item.lightness>sensitivity[index-1].lightness),categories:colors,sensitivity};
}
const luminance=color=>rgb(color).reduce((sum,value,index)=>sum+value*[.2126,.7152,.0722][index],0);
report.text_contrast=Object.fromEntries(['ink','muted','accent','focus'].map(key=>[key,(luminance(tokens.color.surface)+.05)/(luminance(tokens.color[key])+.05)]));
report.all_criteria_pass=Object.values(report.simulations).every(item=>item.categorical_pass&&item.sensitivity_lightness_monotonic)&&report.text_contrast.ink>=4.5&&report.text_contrast.muted>=4.5;
fs.mkdirSync(path.join(root,'ui/reports'),{recursive:true});fs.writeFileSync(path.join(root,'ui/reports/color-vision.json'),JSON.stringify(report,null,2)+'\n');
let svg='<svg xmlns="http://www.w3.org/2000/svg" width="900" height="380"><rect width="100%" height="100%" fill="white"/>';
Object.entries({original:{categories:categories.map(([kind,color])=>({kind,color})),sensitivity:tokens.color.sensitivity.map(color=>({color}))},...report.simulations}).forEach(([name,value],row)=>{svg+=`<text x="20" y="${30+row*85}" font-family="sans-serif" font-size="16">${name}</text>`;[...value.categories,...value.sensitivity].forEach((item,index)=>{svg+=`<rect x="${170+index*65}" y="${10+row*85}" width="60" height="44" fill="${item.color}"/><text x="${170+index*65}" y="${69+row*85}" font-family="sans-serif" font-size="10">${index<5?['human','service','managed','workload','agent'][index]:['0','.2','.4','.6','.8'][index-5]}</text>`;});});svg+='</svg>';fs.writeFileSync(path.join(root,'ui/reports/color-vision.svg'),svg);
console.log(JSON.stringify({pass:report.all_criteria_pass,simulations:Object.fromEntries(Object.entries(report.simulations).map(([name,value])=>[name,{minimum_delta_e:value.categorical_min_delta_e,monotonic:value.sensitivity_lightness_monotonic}])),text_contrast:report.text_contrast}));
if(!report.all_criteria_pass)process.exitCode=1;