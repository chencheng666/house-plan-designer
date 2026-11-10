"""未知模板保护与重复执行回归。"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('patch_template',ROOT/'scripts/patch_template.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PatchTests(unittest.TestCase):
    def test_unknown_template_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'template.html';p.write_text('未知版本')
            with self.assertRaises(ValueError):module.patch_template(p)
            self.assertEqual(p.read_text(),'未知版本')

    def test_repeated_patch_does_not_change_template(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'template.html';original=(ROOT/'assets/template.html').read_bytes();p.write_bytes(original)
            self.assertFalse(module.patch_template(p));self.assertEqual(p.read_bytes(),original)

if __name__=='__main__':unittest.main()
