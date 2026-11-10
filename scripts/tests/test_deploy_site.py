"""新站点发行包只允许受约束的普通文件，防止跨目录覆盖。"""
import importlib.util,tarfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('deploy_site',ROOT/'scripts/deploy_site.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class DeploySiteTests(unittest.TestCase):
    def test_accept_expected_files(self):
        module.validate_members([tarfile.TarInfo('manifest.json'),tarfile.TarInfo('site/index.html'),tarfile.TarInfo('site/demo/index.html')])
    def test_reject_escape_and_unexpected_paths(self):
        for name in ['../index.html','/etc/passwd','site/../../etc/passwd','other/index.html']:
            with self.assertRaises(ValueError):module.validate_members([tarfile.TarInfo(name)])
    def test_reject_links_and_directories(self):
        for kind in [tarfile.SYMTYPE,tarfile.LNKTYPE,tarfile.DIRTYPE]:
            item=tarfile.TarInfo('site/index.html');item.type=kind
            with self.assertRaises(ValueError):module.validate_members([item])
if __name__=='__main__':unittest.main()
