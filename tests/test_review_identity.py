"""Declared identity consistency tests, not actual perception or independence proof."""
import unittest
from stage_fixture import gates
class ReviewIdentityTests(unittest.TestCase):
 def record(self, a='a', b='b', kind='agent'):
  return {name+'_review':{'reviewer':who,'reviewer_kind':kind} for name,who in [('explanation',a),('expression',b)]}
 def test_distinct(self): self.assertEqual(gates.review_identity_errors(self.record()),[])
 def test_equal(self): self.assertEqual(len(gates.review_identity_errors(self.record('a','a'))),1)
 def test_whitespace(self): self.assertEqual(len(gates.review_identity_errors(self.record('a',' a '))),1)
 def test_human_not_forced(self): self.assertEqual(gates.review_identity_errors(self.record('a','a','human')),[])
 def test_legacy(self):
  qa={'comprehension':{'internal_review':{'reviewer_kind':'agent','responsibilities':{'explanation':{'reviewer':'same'},'expression':{'reviewer':'same'}}}}}
  self.assertEqual(len(gates.review_identity_errors(qa)),1)
 def test_malformed(self):
  for qa in (None,[],{}, {'comprehension':{'internal_review':None}}):self.assertEqual(gates.review_identity_errors(qa),[])
 def test_no_invented_task_ids(self): self.assertEqual(gates.review_identity_errors(self.record()),[])
 def test_same_task(self):
  qa=self.record()
  for record in qa.values():record['review_task_id']='same'
  self.assertEqual(len(gates.review_identity_errors(qa)),1)
 def test_legacy_kind_is_authoritative(self):
  qa={'comprehension':{'internal_review':{'reviewer_kind':'agent','responsibilities':{'explanation':{'reviewer':'same','reviewer_kind':'human'},'expression':{'reviewer':'same'}}}}}
  self.assertEqual(len(gates.review_identity_errors(qa)),1)
