"""
把 HouseSpec（户型描述 JSON）注入设计器模板，生成单文件 HTML。

用法:
  python build.py spec.json -o 输出.html [--template ../assets/template.html] [--no-underlay]

spec.json 里可选的 "underlay": {"image": "原图路径", "mmPerPx": 17.65, "x": -4410, "y": -1340}
  会把原图作为底图打包进去（默认隐藏，可在左侧“户型”面板勾选显示，用来对照）。
  x, y = 图片左上角在户型坐标系里的位置（mm）。analyze.py 生成的 draft.json 已经算好。
"""
import argparse, base64, hashlib, html as html_tools, io, json, math, os, re, sys
from PIL import Image
from assistant_bundle import inject_assistant

sys.stdout.reconfigure(encoding='utf-8')
here = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('spec')
ap.add_argument('-o', '--out', required=True)
ap.add_argument('--template', default=os.path.join(here, '..', 'assets', 'template.html'))
ap.add_argument('--no-underlay', action='store_true')
ap.add_argument('--no-assistant', action='store_true', help='仅在诊断旧模板时禁用助手')
a = ap.parse_args()

def validate_spec(spec):
    if not isinstance(spec, dict):
        raise ValueError('户型必须是 JSON 对象')
    if 'name' in spec and not isinstance(spec['name'], str):
        raise ValueError('户型名称必须是字符串')
    floors = spec.get('floors', [spec])
    if not isinstance(floors, list) or not floors:
        raise ValueError('楼层数组不能为空')
    def number(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    def point(v):
        return isinstance(v, list) and len(v) == 2 and all(number(n) for n in v)
    for i, floor in enumerate(floors):
        if not isinstance(floor, dict) or not isinstance(floor.get('walls'), list) or not floor['walls']:
            raise ValueError(f'第 {i + 1} 层必须有墙体数组且不能为空')
        if 'height' in floor and (not number(floor['height']) or floor['height'] <= 0):
            raise ValueError(f'第 {i + 1} 层层高必须为正数')
        for j, wall in enumerate(floor['walls']):
            if not isinstance(wall, dict) or not point(wall.get('a')) or not point(wall.get('b')) or wall['a'] == wall['b']:
                raise ValueError(f'第 {i + 1} 层墙 {j + 1} 的端点无效或长度为零')
            if 't' in wall and (not number(wall['t']) or wall['t'] <= 0):
                raise ValueError(f'第 {i + 1} 层墙 {j + 1} 的厚度必须为正数')
            for opening in wall.get('openings', []):
                if not isinstance(opening, dict) or not all(number(opening.get(k)) for k in ('from', 'to')) or opening['from'] == opening['to']:
                    raise ValueError(f'第 {i + 1} 层墙 {j + 1} 的洞口坐标无效')

try:
    with open(a.spec, encoding='utf-8') as f:
        spec = json.load(f, parse_constant=lambda v: (_ for _ in ()).throw(ValueError(f'不允许非有限数值 {v}')))
    validate_spec(spec)
except (ValueError, OSError) as e:
    ap.error(str(e))

def pack_underlay(ul):
    p = ul['image'] if os.path.isabs(ul['image']) else os.path.join(os.path.dirname(os.path.abspath(a.spec)), ul['image'])
    im = Image.open(p).convert('RGB')
    w, h = im.size
    # 底图压成 JPEG，长边不超过 1600，控制文件体积
    k = min(1, 1600 / max(w, h))
    if k < 1: im = im.resize((round(w * k), round(h * k)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=85)
    return {'src': 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode(),
            'imgW': im.size[0], 'imgH': im.size[1], 'mmPerPx': ul['mmPerPx'] / k, 'x': ul.get('x', 0), 'y': ul.get('y', 0)}

preset = {'spec': spec}
if 'floors' in spec:
    # 整栋楼：每层可以有自己的底图（原图里这一层的那张平面）
    uls = [fl.pop('underlay', None) for fl in spec['floors']]
    if any(uls) and not a.no_underlay: preset['underlays'] = [pack_underlay(u) if u else None for u in uls]
else:
    ul = spec.pop('underlay', None)
    if ul and not a.no_underlay: preset['underlay'] = pack_underlay(ul)
body = json.dumps(preset, ensure_ascii=False, separators=(',', ':'))
preset['id'] = hashlib.sha1(body.encode()).hexdigest()[:12]  # 户型变了 id 就变，浏览器不会拿旧存档覆盖新户型

html = open(a.template, encoding='utf-8').read()
template_source = html
# 去掉模板里可能残留的预设，再紧跟 <meta charset> 插入（charset 必须留在文件开头）
html = re.sub(r'<script id="__preset">.*?</script>', '', html, count=1, flags=re.S)
m = re.search(r'<meta charset[^>]*>', html, re.I)
if not m:
    ap.error('模板缺少 meta charset，无法注入户型')
js = json.dumps(preset, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
html = html[:m.end()] + f'<script id="__preset">window.__PRESET__={js}</script>' + html[m.end():]
name = spec.get('name')
if name: html = re.sub(r'<title>.*?</title>', lambda _: f'<title>{html_tools.escape(name)} · 装修设计器</title>', html, count=1, flags=re.S)
if not a.no_assistant:
    try:
        html = inject_assistant(html, spec, a.spec, required=(os.path.abspath(a.template) == os.path.abspath(ap.get_default('template')) or len(template_source) > 100000), template_source=template_source)
    except ValueError as e:
        ap.error(str(e))
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
open(a.out, 'w', encoding='utf-8').write(html)
fl = spec.get('floors') or [spec]
print(json.dumps({'out': os.path.abspath(a.out), 'kb': round(len(html.encode()) / 1024), 'floors': len(fl), 'walls': sum(len(f.get('walls', [])) for f in fl),
                  'rooms': sum(len(f.get('rooms', [])) for f in fl), 'underlay': 'underlay' in preset or 'underlays' in preset}, ensure_ascii=False))
