// 为交互验收准备实际测试对象，并验证属性修改及撤销，避免遮挡和测试顺序造成漏测。
import path from 'node:path';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const must = (condition, message) => { if (!condition) throw new Error(message); };
export async function clickMM(page, x, y) {
  const point = await page.evaluate(({x,y}) => { const v = __designer.view, r = document.querySelector('#c2d').getBoundingClientRect(); return [r.x+x*v.s+v.ox, r.y+y*v.s+v.oy]; }, {x,y});
  await page.mouse.click(...point);
  await sleep(120);
}
export async function selectFurniture(page, predicate) {
  await page.evaluate(() => { __designer.setLayer('layout'); __designer.setTool('select'); __designer.fit2D(); });
  const candidates = await page.evaluate(source => __designer.app.plan.furniture.filter(eval(source)), predicate);
  // 中心可能被房间名覆盖，沿家具局部坐标取多个内部点，仍通过真实鼠标点选。
  for (const f of candidates) for (const [u,v] of [[0,0],[-.3,0],[.3,0],[0,-.3],[0,.3]]) {
    const a = f.rot*Math.PI/180;
    await clickMM(page, f.x+Math.cos(a)*f.w*u-Math.sin(a)*f.d*v, f.y+Math.sin(a)*f.w*u+Math.cos(a)*f.d*v);
    const selected = await page.evaluate(() => __designer.app.sel);
    if (selected.kind === 'furn' && selected.id === f.id) return f;
  }
  if (candidates.length) throw new Error('存在候选家具，但所有内部点均无法选中');
  return null;
}
export async function testKitchen(page, shots) {
  const f = await selectFurniture(page, "f => ['counter','lCounter','uCounter'].includes(f.type)");
  must(f, '验收户型缺少橱柜，请使用含橱柜的测试样例');
  const before = await page.evaluate(id => JSON.stringify(__designer.app.plan.furniture.find(f=>f.id===id)), f.id);
  for (const shape of ['L','U','I']) {
    await page.select('#kShape', shape); await sleep(350);
    const actual = await page.evaluate(id => __designer.app.plan.furniture.find(f=>f.id===id).kit.shape, f.id);
    must(actual === shape, `橱柜造型未变为 ${shape}`);
    if (shots) await page.screenshot({path:path.join(shots, `橱柜_${shape}.png`)});
  }
  for (let i=0;i<3;i++) { await page.click('#undoBtn'); await sleep(150); }
  const restored = await page.evaluate(id => JSON.stringify(__designer.app.plan.furniture.find(f=>f.id===id)), f.id);
  must(restored === before, '橱柜连续撤销后未恢复原始属性');
  return 'L / U / I 均实际生效，三次撤销完整恢复';
}
export async function testSocket(page, shots) {
  await page.evaluate(() => { __designer.setLayer('mep'); __designer.setTool('select'); __designer.fit2D(); });
  if (!await page.evaluate(() => __designer.app.plan.elec.some(e=>e.kind==='socket'))) {
    await page.click('#leftPanel .tabs [data-tab="mep"]'); await page.click('#autoElec'); await sleep(400);
    const ok = await page.$('.modal [data-ok]'); if (ok) await ok.click(); await sleep(800);
  }
  const sockets = await page.evaluate(() => __designer.app.plan.elec.filter(e=>e.kind==='socket'));
  must(sockets.length, '自动布置后仍没有插座');
  let chosen;
  for (const e of sockets) {
    await clickMM(page,e.x,e.y);
    const selected = await page.evaluate(() => __designer.app.sel);
    if (selected.kind === 'elec' && selected.id === e.id) {chosen=e;break;}
  }
  must(chosen,'存在插座但无法点选');
  const before = await page.evaluate(id=>JSON.stringify(__designer.app.plan.elec.find(e=>e.id===id)),chosen.id);
  const target = await page.evaluate(() => [...document.querySelector('#eKind').options].map(o=>o.value).find(v=>v==='socketUSB'));
  must(target,'插座属性菜单缺少 socketUSB');
  await page.select('#eKind',target); await sleep(250);
  must(await page.evaluate(({id,target})=>__designer.app.plan.elec.find(e=>e.id===id)?.kind===target,{id:chosen.id,target}), '插座类型修改未生效');
  if(shots) await page.screenshot({path:path.join(shots,'插座_修改后.png')});
  await page.click('#undoBtn'); await sleep(200);
  must(await page.evaluate(({id,before})=>JSON.stringify(__designer.app.plan.elec.find(e=>e.id===id))===before,{id:chosen.id,before}), '插座撤销后未完整恢复');
  return `准备 ${sockets.length} 个插座；socket → socketUSB 生效，撤销完整恢复`;
}
export async function testPathTrace(page, expectDownload, { complete = false } = {}) {
  await page.evaluate(async () => { await __designer.setView('3d'); document.querySelector('#rendMode').value='pt'; document.querySelector('#resIn').value='1920x1080'; });
  await sleep(1500);
  must(!await page.evaluate(() => __designer.S3.fp.active), '光追验收要求先退出漫游');
  let samples=0, last='', lastLog=0, finished=false;
  const files = await expectDownload(async () => {
    await page.click('#renderBtn');
    const start=Date.now();
    while(Date.now()-start<360000) {
      const state=await page.evaluate(()=>({text:document.querySelector('#ptProg span').textContent,on:document.querySelector('#ptProg').classList.contains('on'),toast:document.querySelector('#toast')?.textContent}));
      last=state.text;
      const match=last.match(/已采样\s+(\d+)\s*\//); if(match) samples=Number(match[1]);
      if(Date.now()-lastLog>15000) {console.log('光线追踪进度：'+last);lastLog=Date.now();}
      if(complete && !state.on && /光线追踪渲染图已导出/.test(state.toast)) {finished=true;break;}
      if(!complete && samples>=20) break;
      if(!state.on && /失败/.test(state.toast)) throw new Error(state.toast);
      await sleep(1000);
    }
    must(samples>=(complete?16:20), '光线追踪真实采样不足：'+last);
    if(complete) must(finished, '光线追踪未自动完成：'+last);
    else { const button=await page.$('#ptProg button'); await button.click(); }
  }, {wait:120000});
  must(files.some(f=>f.includes('光线追踪')&&f.endsWith('.png')),'没有生成光线追踪 PNG，可能降级为实时渲染');
  await page.evaluate(()=>document.querySelector('#rendMode').value='raster');
  return `${samples} 次真实采样，${complete ? '自动完成' : '提前结束'}保存：${files.join(',')}`;
}
