// 统一浏览器发现与各平台的渲染后端；离屏检查可明确选择软件渲染。
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

export function findBrowser() {
  if (process.env.CHROME_PATH) {
    if (!fs.existsSync(process.env.CHROME_PATH)) throw new Error('CHROME_PATH 指向的浏览器不存在');
    return process.env.CHROME_PATH;
  }
  const candidates = [
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  ];
  const found = candidates.find(p => fs.existsSync(p));
  if (!found) throw new Error('找不到 Chrome/Edge，请设置 CHROME_PATH');
  return found;
}

export function browserArgs({ software = false, platform = process.platform } = {}) {
  if (software) return ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'];
  const backend = platform === 'win32' ? 'd3d11' : platform === 'darwin' ? 'metal' : 'gl';
  return [`--use-angle=${backend}`, '--enable-gpu', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows'];
}

export function prepareOutput(dir, input) {
  const out = path.resolve(dir);
  // 不清理已有目录；拒绝根目录、用户目录、工作目录、输入文件和符号链接。
  if ([path.parse(out).root, os.homedir(), process.cwd(), path.resolve(input)].includes(out)) throw new Error('验收输出必须使用新的专用目录');
  const relative = path.relative(out, path.resolve(input));
  if (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative)) throw new Error('输出目录不能包含输入文件');
  if (fs.existsSync(out)) {
    if (fs.lstatSync(out).isSymbolicLink() || !fs.statSync(out).isDirectory() || fs.readdirSync(out).length) throw new Error('输出目录已存在且非空或不是普通目录，请换一个目录');
  }
  fs.mkdirSync(out, { recursive: true });
  return out;
}

export function reportFailures(reports, errors = []) {
  const failures = [...errors];
  for (const r of reports) {
    for (const k of ['wallsDropped', 'labelsOutsideRooms', 'freeWallEnds']) if (r[k]?.length) failures.push(`${r.name}：${k} 有 ${r[k].length} 项`);
    if (r.openingsDropped) failures.push(`${r.name}：丢失 ${r.openingsDropped} 个门窗`);
    failures.push(...(r.issues || []).filter(i => /^\[(warn|error)\]/.test(i)));
  }
  return failures;
}
