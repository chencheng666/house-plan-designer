import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { browserArgs, prepareOutput, reportFailures } from '../browser.mjs';

test('非空目录、输入目录和链接不会被清理', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), '户型回归-'));
  try {
    const input = path.join(root, 'input.html'); fs.writeFileSync(input, '原文件');
    const out = path.join(root, '已有结果'); fs.mkdirSync(out);
    const sentinel = path.join(out, '保留.txt'); fs.writeFileSync(sentinel, '用户资料');
    assert.throws(() => prepareOutput(out, input));
    assert.equal(fs.readFileSync(sentinel, 'utf8'), '用户资料');
    assert.throws(() => prepareOutput(root, input));
    const link = path.join(root, '链接'); fs.symlinkSync(out, link, 'dir');
    assert.throws(() => prepareOutput(link, input));
    const fresh = path.join(root, '新结果'); assert.equal(prepareOutput(fresh, input), fresh);
  } finally { fs.rmSync(root, { recursive: true }); }
});

test('浏览器按平台选择渲染后端', () => {
  for (const [platform, expected] of [['darwin', 'metal'], ['win32', 'd3d11'], ['linux', 'gl']]) assert.ok(browserArgs({ platform }).includes('--use-angle=' + expected));
  assert.ok(browserArgs({ software: true }).includes('--use-angle=swiftshader'));
});

test('警告、丢失的门窗和页面错误进入失败清单，信息提示可保留', () => {
  assert.equal(reportFailures([{ issues: ['[info] 说明'] }]).length, 0);
  assert.equal(reportFailures([{ name: '一层', issues: ['[warn] 挡窗'], openingsDropped: 1 }], ['页面错误']).length, 3);
});

test('立面点位标签错开并保留全部说明及安装高度', async () => {
  const vm = await import('node:vm');
  const { fileURLToPath } = await import('node:url');
  const template = fs.readFileSync(fileURLToPath(new URL('../../assets/template.html', import.meta.url)), 'utf8');
  const start = template.indexOf('function hpdElevationLabels('), end = template.indexOf('function U9(',start);
  assert.ok(start > 0);
  const draws=[];
  const ctx={save(){},restore(){},beginPath(){},moveTo(){},lineTo(){},stroke(){},fillRect(){},fillText(text,x,y,width){draws.push({text,x,y,width});}};
  const sandbox={lt:'sans-serif'};vm.createContext(sandbox);vm.runInContext(template.slice(start,end),sandbox);
  const labels=Array.from({length:6},(_,i)=>({x:360,y:200+i,text:`插座${i} H300`}));
  sandbox.hpdElevationLabels(ctx,labels,1000,500,1,500,380);
  assert.equal(draws.length,6);
  for(let i=1;i<draws.length;i++) assert.ok(draws[i].y-draws[i-1].y>=18);
  assert.ok(draws.every(d=>d.x>500&&d.x+d.width<=1000&&d.y>=84&&d.y<=380));
  assert.ok(draws.every(d=>d.text.includes('H300')));
});
