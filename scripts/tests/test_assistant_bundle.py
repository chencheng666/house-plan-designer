"""构建助手时的模板版本保护、转义和单文件打包检查。"""
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('assistant_bundle', ROOT/'scripts/assistant_bundle.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
class AssistantBundleTests(unittest.TestCase):
    def test_unknown_template_stops(self):
        with self.assertRaises(ValueError):
            module.inject_assistant('<html>未知模板</html>', {}, '/tmp/a.json')
    def test_minimal_test_template_can_skip(self):
        text = '<html>最小模板</html>'
        self.assertEqual(module.inject_assistant(text, {}, '/tmp/a.json', required=False), text)
    def test_current_template_embeds_modules_and_escapes_seed(self):
        template = (ROOT/'assets/template.html').read_text()
        text = module.inject_assistant(template, {'assistant':{'name':'</script><script>意外脚本</script>'}}, '/tmp/a.json')
        self.assertIn('window.__HPD_BRIDGE__=', text)
        self.assertIn('window.__HPD_BRIDGE__.on=Jt', text)
        self.assertIn('id="hpd-core"', text)
        self.assertIn('id="hpd-ui"', text)
        self.assertNotIn('<script>意外脚本</script>', text)
        self.assertIn('assistant:window.HPD?await window.HPD.projectPackage():null', text)
    def test_changed_share_interface_stops(self):
        template = (ROOT/'assets/template.html').read_text().replace('function ND(){if(!qc)', 'function changedShare(){if(!qc)')
        with self.assertRaises(ValueError):
            module.inject_assistant(template, {}, '/tmp/a.json')
if __name__ == '__main__':unittest.main()
