// 对缺失覆盖项独立补测，生成真实交互和导出证据；不替代完整验收。
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {findBrowser,browserArgs,prepareOutput} from './browser.mjs';
import {testKitchen,testSocket,testPathTrace} from './qa-actions.mjs';
const [file,outArg,...flags]=process.argv.slice(2);
if(!file||!outArg) {console.error('用法：node qa-extra.mjs 设计器.html 新输出目录 [--only=kitchen,socket,pdf,pt]');process.exit(1);}
const only=(flags.find(f=>f.startsWith('--only='))?.slice(7)||'kitchen,socket,pdf,pt').split(',');
if(only.some(v=>!['kitchen','socket','pdf','pt'].includes(v))) throw new Error('未知补测项目');
const out=prepareOutput(outArg,file),shots=path.join(out,'shots'),dl=path.join(out,'downloads');
fs.mkdirSync(shots);fs.mkdirSync(dl);
const browser=await puppeteer.launch({executablePath:findBrowser(),headless:true,protocolTimeout:600000,args:browserArgs(),defaultViewport:{width:1600,height:960}});
const results=[],errors=[];
try {
 const page=await browser.newPage();
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 const cdp=await page.createCDPSession();await cdp.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:dl});
 await page.goto(pathToFileURL(path.resolve(file)).href+'?debug',{waitUntil:'load'});await page.waitForFunction(()=>window.__designer,{timeout:60000});
 const sleep=ms=>new Promise(r=>setTimeout(r,ms));
 const expectDownload=async(trigger,{wait=60000}={})=>{
  const snapshot=()=>Object.fromEntries(fs.readdirSync(dl).map(f=>[f,fs.statSync(path.join(dl,f)).mtimeMs]));
  const before=snapshot();await trigger();const start=Date.now();
  while(Date.now()-start<wait){const found=Object.entries(snapshot()).filter(([f,t])=>!f.endsWith('.crdownload')&&before[f]!==t).map(([f])=>f);if(found.length){await sleep(500);return found;}await sleep(250);}
  throw new Error('导出超时，没有下载到文件');
 };
 const tests={kitchen:['橱柜定制与撤销',()=>testKitchen(page,shots)],socket:['插座属性与撤销',()=>testSocket(page,shots)],pdf:['整套施工图 PDF',async()=>{const files=await expectDownload(async()=>{await page.click('#exportMenu > button');await page.click('#exportMenu [data-exp="pdf"]');},{wait:240000});if(!files.some(f=>f.endsWith('.pdf')))throw new Error('没有导出 PDF');return files.join(',');}],pt:['光线追踪真实采样与保存',()=>testPathTrace(page,expectDownload,{complete:flags.includes('--pt-complete')})]};
 for(const key of only){const [name,fn]=tests[key];const e0=errors.length,start=Date.now();let ok=true,msg='';try{msg=await fn();if(errors.length>e0)throw new Error(errors.slice(e0).join('；'));}catch(e){ok=false;msg=e.message;}
  await page.screenshot({path:path.join(shots,key+'.png')});results.push({key,name,ok,msg,ms:Date.now()-start});console.log(`${ok?'PASS':'FAIL'} ${name}：${msg}`);if(!ok&&key==='pt')break;
 }
} finally {
 await browser.close();
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({mode:'supplement',file,results,errors,passed:results.filter(r=>r.ok).length},null,2));
 fs.writeFileSync(path.join(out,'report.md'),['# 设计器补测报告','','| 项目 | 结果 | 说明 |','|---|---|---|',...results.map(r=>`| ${r.name} | ${r.ok?'通过':'失败'} | ${r.msg.replaceAll('|','/')} |`)].join('\n'));
}
process.exitCode=results.length!==only.length||results.some(r=>!r.ok)||errors.length?2:0;
