"""初始化技能独立环境；在技能根目录执行 python3 scripts/setup.py，--check 只检查。"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description='初始化或检查户型设计器环境')
parser.add_argument('--check', action='store_true', help='只检查，不安装')
args = parser.parse_args()
python = root / '.venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
npm = shutil.which('npm.cmd' if sys.platform == 'win32' else 'npm')
node = shutil.which('node')
if sys.version_info < (3, 12):
    parser.error('需要 Python 3.12 或更新版本')
if not npm or not node:
    parser.error('需要 Node.js 22.12+ 和 npm')
version = json.loads(subprocess.check_output([node, '-p', 'JSON.stringify(process.versions.node)'], text=True))
major, minor = map(int, version.split('.')[:2])
if (major, minor) < (22, 12):
    parser.error('需要 Node.js 22.12+，当前版本 ' + version)
if not args.check:
    if not python.exists():
        subprocess.run([sys.executable, '-m', 'venv', str(root / '.venv')], check=True)
    subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(root / 'requirements.txt')], check=True)
    subprocess.run([npm, 'ci', '--ignore-scripts'], cwd=root / 'scripts', check=True)
if not python.exists():
    parser.error('缺少独立 Python 环境，请先运行 setup.py')
subprocess.run([str(python), '-m', 'pip', 'check'], check=True)
# 导入检查能发现缺包以及本机二进制库不兼容的问题。
subprocess.run([str(python), '-c', 'import numpy, PIL, cv2, fitz, ezdxf, pypdf; print("Python 依赖导入通过")'], check=True)
subprocess.run([node, '--input-type=module', '-e', "import puppeteer from 'puppeteer-core'; import {findBrowser} from './browser.mjs'; console.log('浏览器：'+findBrowser()); console.log('Puppeteer 导入通过')"], cwd=root / 'scripts', check=True)
print('环境检查通过。运行 Python 脚本时使用：' + str(python))
