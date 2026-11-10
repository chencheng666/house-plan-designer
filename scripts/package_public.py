"""制作公开Skill与静态站点发行包，排除本机依赖、验收临时文件和文章后台记录。"""
import argparse,hashlib,json,os,tarfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SKIP={'.git','.venv','node_modules','__pycache__','.DS_Store'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def core_files():
    out=[]
    for name in ['SKILL.md','VERSION.json','LICENSE','README.md','CHANGELOG.md','requirements.txt']:
        out.append(ROOT/name)
    for name in ['assets','scripts','reference','.github']:
        for base,dirs,names in os.walk(ROOT/name):
            dirs[:]=[d for d in dirs if d not in SKIP]
            out.extend(Path(base)/n for n in names if n not in SKIP)
    out.extend(ROOT/name for name in ['docs/architecture.md','docs/upstream-readme.md','docs/publishing.md'] if (ROOT/name).exists())
    return sorted(out)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--release',default='2.0.0-20261110');a=ap.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    files=core_files();manifest={'版本':'2.0.0','算法':'SHA256','范围':'Skill运行源码及使用文档，不含静态站点、部署产物和文章后台记录','文件':{str(p.relative_to(ROOT)):sha(p) for p in files}}
    mf=ROOT/'RELEASE-MANIFEST.json';mf.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    skill=ROOT/'site/downloads/house-plan-designer-skill-v2.0.0.zip'
    with zipfile.ZipFile(skill,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in [*files,mf]:z.write(p,'house-plan-designer/'+str(p.relative_to(ROOT)))
    site=ROOT/'site';rows=[{'path':str(p.relative_to(site)),'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(site.rglob('*')) if p.is_file() and '.DS_Store' not in p.parts]
    meta={'version':'2.0.0','release':a.release,'files':rows};(out/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    archive=out/'house-plan-designer-site-v2.0.0.tar.gz'
    with tarfile.open(archive,'w:gz') as t:
        t.add(out/'manifest.json',arcname='manifest.json',recursive=False)
        for row in rows:t.add(site/row['path'],arcname='site/'+row['path'],recursive=False)
    (out/'checksums.json').write_text(json.dumps({p.name:sha(p) for p in [skill,archive,site/'downloads/d128-designer.html',site/'downloads/d128-drawings.pdf']},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'files':len(rows),'siteArchive':str(archive),'archiveSha256':sha(archive),'skillSha256':sha(skill)},ensure_ascii=False))
if __name__=='__main__':main()
