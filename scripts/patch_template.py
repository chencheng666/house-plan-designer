"""对已知上游模板应用可重复的局部修复；遇到未知模板版本先停止，避免误改打包产物。"""
import argparse
import hashlib
from pathlib import Path

MARKER = 'HPD_PATCH_20261028'
ORIGINAL_SHA = '88bc43feea9ddb3b4cfc1cee58369ca0fb985a9dcfc21d43986d0e1a85a5f9e1'
HELPER = '/* HPD_PATCH_20261028 */\n// 立面图点位说明统一放在墙面右侧，保留引线及真实安装高度。\nfunction hpdElevationLabels(ctx,labels,width,height,scale,wallRight,bottom){\n if(!labels.length)return;\n const top=84*scale,limit=Math.min(height-25*scale,bottom),gap=Math.min(18*scale,(limit-top)/Math.max(1,labels.length-1));\n labels.sort((a,b)=>a.y-b.y);\n let previous=top-gap;\n for(const label of labels){label.ly=Math.max(top,label.y,previous+gap);previous=label.ly;}\n const overflow=Math.max(0,previous-limit);\n for(const label of labels)label.ly-=overflow;\n const lx=Math.min(width-240*scale,wallRight+30*scale);\n ctx.save();ctx.font=`500 ${Math.min(11*scale,gap*.7)}px ${lt}`;ctx.textAlign="left";ctx.textBaseline="middle";\n for(const label of labels){\n  ctx.strokeStyle="#8a929c";ctx.lineWidth=.7*scale;ctx.beginPath();ctx.moveTo(label.x+8*scale,label.y);ctx.lineTo(lx-8*scale,label.ly);ctx.lineTo(lx-3*scale,label.ly);ctx.stroke();\n  ctx.fillStyle="rgba(255,255,255,.94)";ctx.fillRect(lx-2*scale,label.ly-gap*.42,width-lx-12*scale,gap*.84);\n  ctx.fillStyle="#414b5a";ctx.fillText(label.text,lx,label.ly,width-lx-20*scale);\n }\n ctx.restore();\n}\n'

def patch_template(file):
    file = Path(file)
    source = file.read_text(encoding='utf-8')
    if MARKER in source:
        return False
    if hashlib.sha256(source.encode()).hexdigest() != ORIGINAL_SHA:
        raise ValueError('模板版本未知，请复核上游差异后更新补丁')
    replacements = [
        ('function U9(n,e,t,i,s=1){', HELPER + 'function U9(n,e,t,i,s=1){'),
        ('d=150*s,y=120*s,b=90*s,g=150*s,v=', 'd=150*s,y=320*s,b=90*s,g=150*s,v='),
        ('for(const O of E.plan.elec){if(!vt[O.kind].wall)', 'const hpdLabels=[];for(const O of E.plan.elec){if(!vt[O.kind].wall)'),
        ('n.fillText(`${vt[O.kind].name} H${O.h}`,W+14*s,H)}const B=', 'hpdLabels.push({x:W,y:H,text:`${vt[O.kind].name} H${O.h}`})}hpdElevationLabels(n,hpdLabels,t,i,s,p+h*v,m);const B='),
        ('t(Math.floor(Math.min(1,j)*i),i,(performance.now()-C)/1e3,A.isCompiling)', 't(Math.floor(A.samples),i,(performance.now()-C)/1e3,A.isCompiling)'),
    ]
    for old,new in replacements:
        if source.count(old) != 1:
            raise ValueError('补丁定位不唯一，未写入模板：' + old[:60])
        source = source.replace(old,new,1)
    file.write_text(source,encoding='utf-8')
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template', nargs='?', default=Path(__file__).resolve().parent.parent/'assets/template.html')
    args = parser.parse_args()
    print('已应用模板补丁' if patch_template(args.template) else '模板补丁已存在')
