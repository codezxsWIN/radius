import {spawn} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';

export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export async function openBrowser(width=1440,height=1000){
  const browserPath=process.env.BR_BROWSER??['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(value=>fs.existsSync(value));
  if(!browserPath)throw Error('No installed Chromium browser; set BR_BROWSER explicitly.');
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'br-visual-browser-'));
  const processHandle=spawn(browserPath,['--headless=new','--remote-debugging-port=0','--user-data-dir='+profile,'--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--disable-sync','--disable-extensions','--force-device-scale-factor=1','--hide-scrollbars','about:blank'],{stdio:['ignore','ignore','pipe']});
  const endpoint=await new Promise((resolve,reject)=>{let text='';const timeout=setTimeout(()=>reject(Error('Browser startup timeout')),20000);processHandle.stderr.on('data',chunk=>{text+=chunk;const match=/DevTools listening on (ws:\/\/[^\s]+)/.exec(text);if(match){clearTimeout(timeout);resolve(match[1]);}});processHandle.on('error',reject);processHandle.on('exit',code=>{if(!text.includes('DevTools listening'))reject(Error('Browser exited '+code));});});
  const socket=new WebSocket(endpoint);await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
  let sequence=0;const pending=new Map(),listeners=new Map();
  socket.addEventListener('message',event=>{const message=JSON.parse(event.data);if(message.id){const item=pending.get(message.id);if(item){pending.delete(message.id);clearTimeout(item.timeout);message.error?item.reject(Error(JSON.stringify(message.error))):item.resolve(message.result);}}else for(const callback of listeners.get(message.method)??[])callback(message.params,message.sessionId);});
  const call=(method,params={},sessionId)=>new Promise((resolve,reject)=>{const id=++sequence,timeout=setTimeout(()=>{pending.delete(id);reject(Error(method+' timed out'));},120000);pending.set(id,{resolve,reject,timeout});socket.send(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})}));});
  const {targetId}=await call('Target.createTarget',{url:'about:blank'}),{sessionId}=await call('Target.attachToTarget',{targetId,flatten:true});
  const send=(method,params={})=>call(method,params,sessionId);
  const on=(method,callback)=>{if(!listeners.has(method))listeners.set(method,[]);listeners.get(method).push(callback);};
  await send('Page.enable');await send('Runtime.enable');await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
  const errors=[],requests=[];on('Runtime.exceptionThrown',({exceptionDetails})=>errors.push(exceptionDetails.exception?.description??exceptionDetails.text));on('Network.requestWillBeSent',({request})=>requests.push(request.url));
  const evaluate=async expression=>{const response=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture:true});if(response.exceptionDetails)throw Error(response.exceptionDetails.exception?.description??response.exceptionDetails.text);return response.result.value;};
  const navigate=async(url=pathToFileURL(path.join(ROOT,'ui/index.html')).href)=>{const loaded=new Promise(resolve=>{const callback=()=>{listeners.set('Page.loadEventFired',(listeners.get('Page.loadEventFired')??[]).filter(item=>item!==callback));resolve();};on('Page.loadEventFired',callback);});await send('Page.navigate',{url});await loaded;await evaluate('document.fonts.ready.then(()=>Boolean(globalThis.BRApp))');};
  await navigate();
  return {send,evaluate,navigate,errors,requests,version:await call('Browser.getVersion'),async screenshot(filename){const {data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});const bytes=Buffer.from(data,'base64');if(filename){fs.mkdirSync(path.dirname(filename),{recursive:true});fs.writeFileSync(filename,bytes);}return bytes;},async close(){try{await call('Browser.close');}catch{}socket.close();processHandle.kill();try{fs.rmSync(profile,{recursive:true,force:true,maxRetries:3,retryDelay:100});}catch{}}};
}