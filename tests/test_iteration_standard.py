"""Offline navigation regression, not proof of execution or quality."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]/'skills/science-video-production'
spec=importlib.util.spec_from_file_location('iteration_reference_check',ROOT/'scripts/check_reference_system.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class IterationStandardTests(unittest.TestCase):
 def test_version_and_owner_navigation(self):
  profile=json.loads((ROOT/'config/series-profile.json').read_text())
  registry=json.loads((ROOT/'indexes/standard-coverage.json').read_text())
  owners=json.loads((ROOT/'indexes/rule-owners.json').read_text())
  self.assertEqual(profile['version'],'1.6.4');self.assertEqual(registry['version'],'1.6.4')
  self.assertEqual(len(owners['owners']),9)
  rules=[r for r in registry['rules'] if r['id'].startswith('ITERATE-')]
  self.assertEqual(len(rules),8)
  self.assertTrue(all(r['owner']=='references/production-checkpoints.md' and r['actual_execution']=='not_established' for r in rules))
  self.assertEqual(m.check(ROOT),[])
 def test_removed_responsibility_clause_fails_index(self):
  with tempfile.TemporaryDirectory() as tmp:
   target=Path(tmp)/'skill';shutil.copytree(ROOT,target)
   p=target/'references/production-checkpoints.md';s=p.read_text();s=s.replace('只改变预先写明的设计变量','任意扫seed')
   p.write_text(s)
   self.assertTrue(any('failure clause text missing/stale' in e for e in m.check(target)))
 def test_boundaries_remain_explicit(self):
  text=(ROOT/'references/production-checkpoints.md').read_text().split('## 精确可控与高效迭代',1)[1]
  for clause in ['不新增机器门禁','不保证接触次序','不盲重投','不擅停无权管理的服务','动态资源仍逐次现采','不能替代有声代表段','未经实际对照测量','最小恢复记录和当前媒体身份必须先落盘']:
   self.assertIn(clause,text)

if __name__=='__main__':unittest.main()
