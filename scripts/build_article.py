"""将已审核正文与真实图片排成可复制到公众号的HTML，图注和外链保留明文。"""
import argparse,html,re
from pathlib import Path
IMAGES={'01':'01-overview.png','02':'02-floor-plan.png','03':'03-assistant.png','04':'04-path-traced.png','05':'05-architecture.png'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--out',required=True);ap.add_argument('--image-base',required=True);a=ap.parse_args()
    chunks=Path(a.source).read_text().strip().split('\n\n');title=chunks.pop(0);parts=[]
    parts.append('<p style="font-size:12px;letter-spacing:2px;color:#80906e;margin:0 0 26px">户型设计助手 2.0 / 开源增强版</p>')
    for c in chunks:
        m=re.match(r'【配图(\d\d)】(.+)',c,re.S)
        if m:
            url=a.image_base.rstrip('/')+'/'+IMAGES[m[1]]
            parts.append(f'<section style="margin:28px 0"><img src="{html.escape(url,quote=True)}" style="display:block;width:100%;height:auto;border-radius:6px" alt="{html.escape(m[2],quote=True)}"><p style="font-size:12px;line-height:1.8;color:#829078;margin:9px 0 0;text-align:center">{html.escape(m[2])}</p></section>');continue
        m=re.match(r'(\d\d) / (.+)',c)
        if m:
            parts.append(f'<section style="margin:38px 0 22px;border-top:1px solid #dce3d2;padding-top:18px"><p style="font-size:11px;letter-spacing:2px;color:#9d895e;margin:0 0 8px">{m[1]} / 开源设计手记</p><h2 style="font-size:22px;line-height:1.5;color:#265644;margin:0;font-weight:600">{html.escape(m[2])}</h2></section>');continue
        text=html.escape(c).replace('\n','<br>')
        text=re.sub(r'https://[^<\s]+',lambda m:f'<a href="{m[0]}" style="color:#28614d;word-break:break-all;text-decoration:underline">{m[0]}</a>',text)
        if c.startswith('“按这张'):parts.append(f'<section style="background:#edf2e4;border-left:3px solid #8ba575;padding:17px 20px;margin:22px 0;font-size:15px;line-height:1.9;color:#496448">{text}</section>')
        else:parts.append(f'<p style="font-size:16px;line-height:1.95;letter-spacing:.3px;color:#435646;margin:0 0 19px;text-align:justify;word-break:break-word">{text}</p>')
    body='<section style="max-width:760px;margin:auto;padding:26px 22px 40px;font-family:PingFang SC,Microsoft YaHei,sans-serif;background:#fffef9">'+''.join(parts)+'</section>'
    output='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title></head><body style="margin:0;background:#f4f5ef">'+body+'</body></html>'
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(output);print({'标题':title,'段落':len(chunks),'配图':len(IMAGES),'输出':str(p)})
if __name__=='__main__':main()
