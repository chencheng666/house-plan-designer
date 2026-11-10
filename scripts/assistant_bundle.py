"""把可维护的设计助手模块打进单文件，不改写上游模板文件。"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWN_TEMPLATE_SHA256 = {'ba6aec8637389e9c5e506ad6d3d8934c7bc28764ab84c695ba3f625cfde278d2'}
BRIDGE_START = 'location.search.includes("debug")&&(window.__designer={mep:'

def inject_assistant(html, spec, spec_path, required=True, template_source=None):
    start = html.find(BRIDGE_START)
    if start < 0:
        if required:
            raise ValueError('模板接口不匹配，设计助手未注入；请核对上游版本，不可静默交付缺功能版本')
        return html
    if hashlib.sha256((template_source or html).encode()).hexdigest() not in KNOWN_TEMPLATE_SHA256:
        raise ValueError('未知模板哈希，需复核Three.js构造器、桥接及分享接口后再更新适配器')
    end = html.find('});</script>', start)
    if end < 0 or html.find(BRIDGE_START, start + 1) >= 0:
        raise ValueError('模板接口数量或结束标记不匹配')
    bridge = html[start:end + 3]
    bridge = bridge.replace('location.search.includes("debug")&&(window.__designer=', 'window.__HPD_BRIDGE__=', 1)
    bridge = bridge[:-2] + ';' if bridge.endswith(');') else bridge
    # 构造器在原模块内导出，真实模型和分区继续使用同一个 Three.js 实例。
    bridge += 'window.__HPD_BRIDGE__.on=Jt;'
    bridge += 'if(location.search.includes("debug"))window.__designer=window.__HPD_BRIDGE__;'
    bridge += 'window.__HPD_THREE__={GLTFLoader:SR,Object3D:M0,Mesh:xe,BufferGeometry:zt,Float32BufferAttribute:_t,Box3:F0,MeshStandardMaterial:a0,CanvasTexture:ji,materials:bo,elecNames:Object.fromEntries(Object.entries(vt).map(([k,v])=>[k,v.name]))};'
    html = html[:start] + bridge + html[end + 3:]
    # 原生分享文件也带助手资产，避免跨设备退回占位柜体。
    old = 'function ND(){if(!qc)'
    if html.count(old) != 1 or html.count('time:Date.now(),models:e},i=JSON.stringify(t)') != 1:
        raise ValueError('分享导出接口不匹配，无法保证模型与贴图随文件迁移')
    html = html.replace(old, 'async function ND(){if(!qc)', 1).replace('time:Date.now(),models:e},i=JSON.stringify(t)', 'time:Date.now(),models:e,assistant:window.HPD?await window.HPD.projectPackage():null},i=JSON.stringify(t)', 1)
    source = json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    project = spec.get('projectId') or hashlib.sha256(str(Path(spec_path).resolve()).encode()).hexdigest()[:20]
    manifest = {'version': '2.0.0', 'projectId': project, 'revision': hashlib.sha256(source.encode()).hexdigest(), 'seed': spec.get('assistant', {})}
    css = (ROOT / 'assets/assistant/assistant.css').read_text(encoding='utf-8')
    core = (ROOT / 'assets/assistant/core.mjs').read_text(encoding='utf-8')
    ui = (ROOT / 'assets/assistant/ui.mjs').read_text(encoding='utf-8')
    safe = lambda text: re.sub(r'</script', r'<\\/script', text, flags=re.I)
    payload = '<style id="hpd-style">' + css + '</style>'
    payload += '<script id="hpd-manifest">window.__HPD_MANIFEST__=' + json.dumps(manifest, ensure_ascii=False).replace('<', '\\u003c') + '</script>'
    payload += '<script type="module" id="hpd-core">' + safe(core) + '</script>'
    payload += '<script type="module" id="hpd-ui">' + safe(ui) + '</script>'
    return html.replace('</body>', payload + '</body>', 1)
