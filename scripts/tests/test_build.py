"""构建入口的标题转义、无效输入与模板错误回归。"""
import html
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

class BuildTests(unittest.TestCase):
    def build(self, spec, template='<html><meta charset="utf-8"><title>模板</title></html>'):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / 'spec.json').write_text(json.dumps(spec, ensure_ascii=False), encoding='utf-8')
            (d / 'template.html').write_text(template, encoding='utf-8')
            r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'build.py'), str(d / 'spec.json'), '-o', str(d / 'out.html'), '--template', str(d / 'template.html')], capture_output=True, text=True)
            return r, (d / 'out.html').read_text(encoding='utf-8') if (d / 'out.html').exists() else ''

    def spec(self):
        return {'name': '标题', 'walls': [{'a': [0, 0], 'b': [4000, 0], 't': 200}]}

    def test_title_escape_and_literal_backslash(self):
        spec = self.spec()
        spec['name'] = '测试</title><script>window.注入=1</script>\\g<1>&'
        r, text = self.build(spec)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('<title>' + html.escape(spec['name']) + ' · 装修设计器</title>', text)
        self.assertNotIn('<script>window.注入', text)
        self.assertIn('\\u003c/script>', text)

    def test_reject_invalid_geometry(self):
        for walls in [[], [{'a': [0, 0], 'b': [0, 0]}], [{'a': [True, 0], 'b': [1, 0]}], [{'a': [0, 0], 'b': [1, 0], 't': -1}]]:
            r, text = self.build({'walls': walls})
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse(text)

    def test_empty_download_directory_fails(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'qa_files.py'), d], capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn('没有可验证', r.stdout)

    def test_reject_missing_charset(self):
        r, text = self.build(self.spec(), '<title>无字符集</title>')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('模板缺少', r.stderr)
        self.assertFalse(text)

if __name__ == '__main__':
    unittest.main()
