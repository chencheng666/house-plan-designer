#!/usr/bin/env python3
"""在现有腾讯云站点新建独立静态路径，保护原路由、版本指针与游戏服务。"""
import argparse,hashlib,json,os,re,shutil,subprocess,tarfile,time
try:
    import fcntl
except ImportError:
    fcntl=None
from pathlib import Path
BASE=Path('/opt/house-plan-designer')
MAIN=Path('/www/server/panel/vhost/nginx/html_www.daguojueqi.site.conf')
EXT=Path('/www/server/panel/vhost/nginx/extension/www.daguojueqi.site/40-house-plan-designer.conf')
NGINX='/www/server/nginx/sbin/nginx'
ORIGIN='https://www.daguojueqi.site'
PREFIX='/house-plan-designer/'
SERVICES=['great-powers-domestic','great-powers-domestic-six']
LINKS=['/opt/jiuji/current','/opt/jiuji/official/current']
PAGES=['/','/play/','/candidate/','/downloads/','/resume/','/jiuji/','/jiuji/official/']
CONFIG='''# 户型设计助手独立静态路由；不修改原站、九级与大国崛起。
location = /house-plan-designer { return 302 /house-plan-designer/; }
location ^~ /house-plan-designer/ {
    alias /opt/house-plan-designer/current/;
    index index.html;
    autoindex off;
    add_header Cache-Control "no-cache" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Access-Control-Allow-Origin "*" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' data: blob:; worker-src 'self' blob:; font-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'self'; form-action 'none'" always;
    limit_except GET { deny all; }
}
'''
def sha(data):return hashlib.sha256(data).hexdigest()
def run(args,timeout=25):
    r=subprocess.run(args,capture_output=True,timeout=timeout)
    if r.returncode:raise RuntimeError((r.stderr or r.stdout).decode(errors='replace'))
    return r.stdout

def atomic(p,body):
    tmp=p.with_name(p.name+'.house-plan-next');tmp.write_bytes(body);tmp.chmod(0o644);os.replace(tmp,p)

def switch(target):
    link=BASE/'current-next'
    if link.exists() or link.is_symlink():raise RuntimeError('发现未完成切换指针，停止覆盖')
    link.symlink_to(target);os.replace(link,BASE/'current')

def read_url(path):return run(['curl','-fsS','--max-time','12','--resolve','www.daguojueqi.site:443:127.0.0.1',ORIGIN+path])

def validate_members(members):
    for m in members:
        p=Path(m.name)
        if p.is_absolute() or '..' in p.parts or not m.isfile() or not (m.name=='manifest.json' or m.name.startswith('site/')):raise ValueError('发行包含不允许的路径或类型：'+m.name)

def snapshot():
    configs=[MAIN,*[p for p in sorted(EXT.parent.glob('*.conf')) if p!=EXT]]
    health={}
    for svc,port in zip(SERVICES,[8088,8089]):
        state=run(['systemctl','show',svc,'-p','MainPID','-p','ActiveState']).decode().strip();data=json.loads(run(['curl','-fsS','--max-time','5',f'http://127.0.0.1:{port}/api/health']))
        if 'MainPID=0' in state or not data.get('ok'):raise RuntimeError('原有游戏健康检查未通过')
        health[svc]={'state':state,'version':data.get('version'),'build':data.get('build')}
    return {'configs':{str(p):sha(p.read_bytes()) for p in configs},'links':{p:str(Path(p).resolve()) for p in LINKS},'services':health,'pages':{p:sha(read_url(p)) for p in PAGES}}

def deploy(a):
    if fcntl is None or not hasattr(os,'geteuid') or os.geteuid()!=0 or not MAIN.is_file() or 'www.daguojueqi.site' not in MAIN.read_text():raise RuntimeError('服务器身份或站点归属不匹配')
    if not re.fullmatch(r'[A-Za-z0-9.-]+',a.release):raise RuntimeError('无效发布编号')
    archive=Path(a.archive)
    if not re.fullmatch(r'[a-f0-9]{64}',a.sha256) or sha(archive.read_bytes())!=a.sha256:raise RuntimeError('发布包摘要不一致')
    BASE.mkdir(exist_ok=True)
    locks=[Path('/opt/great-powers/deploy.lock').open('a'),Path('/opt/jiuji/deploy.lock').open('a'),(BASE/'deploy.lock').open('a')]
    for lock in locks:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if shutil.disk_usage(BASE).free<150_000_000:raise RuntimeError('剩余磁盘空间不足')
    if EXT.exists() and not EXT.read_text().startswith('# 户型设计助手独立静态路由'):raise RuntimeError('同名配置不是本工具管理的路由，停止覆盖')
    current=BASE/'current'
    if current.exists() and not current.is_symlink():raise RuntimeError('当前目录不是受管理的链接')
    old=str(current.resolve()) if current.is_symlink() else None
    if old and not old.startswith(str(BASE/'releases')+'/'):raise RuntimeError('旧版本不在本工具发布目录')
    release=BASE/'releases'/a.release;backup=BASE/'backups'/a.release
    if release.exists() or backup.exists():raise RuntimeError('发布编号已存在，先读回状态，不重复覆盖')
    before=snapshot();old_config=EXT.read_bytes() if EXT.exists() else None;changed=old_config!=CONFIG.encode();backup.mkdir(parents=True)
    (backup/'previous.json').write_text(json.dumps({'previous':old,'configExisted':old_config is not None,'before':before},ensure_ascii=False,indent=2))
    if old_config is not None:(backup/'40-house-plan-designer.conf').write_bytes(old_config)
    release.mkdir(parents=True)
    with tarfile.open(archive) as t:
        validate_members(t.getmembers());t.extractall(release)
    mf=json.loads((release/'manifest.json').read_text());rows=mf['files']
    if mf['release']!=a.release:raise RuntimeError('发行包发布编号不匹配')
    for r in rows:
        p=Path(r['path'])
        if p.is_absolute() or '..' in p.parts or sha((release/'site'/p).read_bytes())!=r['sha256']:raise RuntimeError('文件校验失败：'+str(p))
    names={r['path'] for r in rows}
    if not {'index.html','assets/site.css','demo/index.html','version.json','downloads/d128-designer.html'}.issubset(names):raise RuntimeError('缺少站点必要文件')
    for p in release.rglob('*'):p.chmod(0o755 if p.is_dir() else 0o644)
    applied=False;reloaded=False
    try:
        switch(release/'site');applied=True
        if changed:atomic(EXT,CONFIG.encode())
        run([NGINX,'-t'])
        if changed:run([NGINX,'-s','reload']);reloaded=True
        for attempt in range(12):
            try:
                for name in ['version.json','index.html','demo/index.html','assets/site.css']:
                    row=next(r for r in rows if r['path']==name)
                    if sha(read_url(PREFIX+name))!=row['sha256']:raise RuntimeError('新站文件不匹配：'+name)
                break
            except Exception:
                if attempt==11:raise
                time.sleep(.5)
        after=snapshot()
        if before!=after:raise RuntimeError('受保护站点、游戏指针或服务发生变化，回退本次发布')
    except Exception:
        if applied:
            if old:switch(old)
            elif current.is_symlink():current.unlink()
        if changed:
            if old_config is None:EXT.unlink(missing_ok=True)
            else:atomic(EXT,old_config)
            run([NGINX,'-t'])
            if reloaded:run([NGINX,'-s','reload'])
        raise
    report={'applied':True,'url':ORIGIN+PREFIX,'release':a.release,'directory':str(release/'site'),'backup':str(backup),'archiveSha256':a.sha256,'files':len(rows),'before':before,'after':after,'protectedUnchanged':before==after,'nginxReloaded':reloaded}
    atomic(BASE/'deployment.json',json.dumps(report,ensure_ascii=False,indent=2).encode());print('HPD_DEPLOY_JSON='+json.dumps(report,ensure_ascii=False,separators=(',',':')));print('HPD_DEPLOY_DONE')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--release',required=True);deploy(ap.parse_args())
if __name__=='__main__':main()
