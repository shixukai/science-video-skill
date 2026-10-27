"""Synthetic evidence regressions; no actual film or user approval is asserted."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import label_permission_guard as guard
from presentation_checks import validate_text_plan, prohibited_cue
from stage_checks import Checks, digest


def consent_item(item, root):
    """Explicitly synthetic original-message fixture for schema tests only."""
    item.update(position='bottom right', time_range=[0, 1])
    quote='Synthetic user statement: show ' + item['text'] + ' at bottom right from 0 to 1 seconds.'
    path=Path(root)/'synthetic-user-consent.txt'; path.write_text(quote)
    item['user_approval']={'scope':guard.scope(item),'user_message_ref':'synthetic-test-message:1',
                           'user_quote':quote,'evidence':{'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}


class LabelPermissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.root=Path(self.tmp.name)
        self.item={'id':'label','surface':'frame','text':'结构示意','purposes':['scientific_condition'],
                   'necessity':'identify the scientific structure','removal_loss':'structure reference would be lost'}
        self.data={'presentation_text':{'channels':{s:{'status':'present' if s=='frame' else 'absent','note':'synthetic declared surface'} for s in ('frame','caption','voiceover','cover')},'items':[self.item],'required_notices':[]}}
        self.view={'sha256':'a'*64,'duration':1}
        source=self.root/'synthetic-renderer.py'; source.write_text('pass\n')
        self.manifest={'schema_version':1,'status':'pass','stage':'G2','media_sha256':self.view['sha256'],
          'inventory_sha256':digest(self.data['presentation_text']),'time_range':[0,1],
          'method':'actual_output_and_sources','actual_output_inspected':True,
          'reviewer':'synthetic reviewer fixture','observation':'Synthetic declaration only; no actual viewing',
          'zones':sorted(guard.ZONES),'unknown_overlays':[],
          'sources':[{'id':'source','kind':'renderer','file':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}],
          'observed':[dict(item_id='label',source_ids=['source'],text=self.item['text'],surface='frame',position='center',time_range=[0,1])]}

    def plan(self):
        checks=Checks(self.data,self.root);validate_text_plan(checks);return checks.errors

    def overlay(self, stage='G2'):
        path=self.root/'overlay.json';path.write_text(json.dumps(self.manifest))
        review={'overlay_evidence':{'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}
        checks=Checks(self.data,self.root)
        guard.validate_overlay_review(checks,stage,self.view,review,{'label':self.item},{'label'})
        return checks.errors

    def assert_blocked(self, errors, fragment):
        self.assertTrue(any(fragment in error for error in errors),errors)

    def test_scientific_labels_and_normal_captions_need_no_user_permission(self):
        for wording,purpose in [('结构示意','scientific_condition'),('机制示意','mechanism'),('不按实际比例绘制','scientific_condition'),('时间放慢10倍','scientific_condition'),('在相同温度下比较','scientific_condition'),('阳光经过水滴发生折射','accessibility'),('纸币水印的明暗来自纸张厚度差','mechanism'),('玻璃上的水印由矿物质沉积形成','mechanism'),('水印','topic')]:
            with self.subTest(wording=wording):
                self.item.update(text=wording,purposes=[purpose]);self.assertEqual(self.plan(),[])
                self.assertFalse(guard.marking_cue(wording))

    def test_license_does_not_supply_user_consent(self):
        self.item.update(text='Jane / CC BY 4.0',purposes=['attribution'])
        self.assert_blocked(self.plan(),'original user message')

    def test_specific_original_consent_allows_otherwise_eligible_attribution(self):
        self.item.update(text='Jane / CC BY 4.0',purposes=['attribution']);consent_item(self.item,self.root)
        self.assertEqual(self.plan(),[])
        self.manifest.update(inventory_sha256=digest(self.data['presentation_text']))
        self.manifest['observed'][0].update(guard.scope(self.item))
        self.assertEqual(self.overlay(),[])

    def test_blanket_boolean_approval_and_quote_fabrication_fail(self):
        self.item.update(text='Jane / CC BY 4.0',purposes=['attribution'],user_approval=True)
        self.assert_blocked(self.plan(),'original user message')
        consent_item(self.item,self.root);self.item['user_approval']['user_quote']='Another user statement'
        self.assert_blocked(self.plan(),'quote absent')

    def test_approval_binds_text_surface_position_time_and_graphic(self):
        self.item.update(text='Jane / CC BY 4.0',purposes=['attribution']);consent_item(self.item,self.root)
        for key,value in [('text','Another credit'),('surface','caption'),('position','top left'),('time_range',[0,2]),('graphic_sha256','f'*64)]:
            with self.subTest(key=key):
                old=copy.deepcopy(self.item);self.item[key]=value
                self.assert_blocked(self.plan(),'consent must match')
                self.item.clear();self.item.update(old)

    def test_stale_or_unsafe_consent_evidence_blocks(self):
        self.item.update(text='Jane / CC BY 4.0',purposes=['attribution']);consent_item(self.item,self.root)
        self.item['user_approval']['evidence']['sha256']='0'*64
        self.assert_blocked(self.plan(),'hash stale')
        self.item['user_approval']['evidence']['file']='../outside.txt'
        self.assert_blocked(self.plan(),'path missing/unsafe')

    def test_graphic_mark_is_not_exempt_because_it_has_no_words(self):
        self.item.update(text='monochrome logo asset',kind='marking',graphic_sha256='b'*64)
        self.assert_blocked(self.plan(),'original user message')

    def test_graphic_digest_must_be_valid_and_bound_to_actual_asset(self):
        self.item.update(text='monochrome logo asset', kind='marking', graphic_sha256='invalid')
        consent_item(self.item,self.root)
        self.assert_blocked(self.plan(),'actual graphic SHA-256')
        path=self.root/'graphic.svg';path.write_text('<svg/>')
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        self.item.update(graphic_sha256=sha,graphic_source={'file':path.name,'sha256':sha})
        consent_item(self.item,self.root);self.assertEqual(self.plan(),[])
        self.manifest['observed'][0].update(guard.scope(self.item))
        self.manifest['inventory_sha256']=digest(self.data['presentation_text'])
        self.assert_blocked(self.overlay(),'not bound to its reviewed source asset')
        self.manifest['sources'].append(dict(id='graphic',kind='image',**self.item['graphic_source']))
        self.manifest['observed'][0]['source_ids'].append('graphic')
        self.assertEqual(self.overlay(),[])
        path.write_text('<svg>changed</svg>')
        self.assert_blocked(self.overlay(),'hash stale')
        self.assert_blocked(self.plan(),'hash stale')

    def test_validation_receipt_binds_the_new_guard(self):
        from check_episode import validation_resources
        resources=validation_resources()
        path=Path(guard.__file__)
        self.assertEqual(resources['scripts/label_permission_guard.py'],hashlib.sha256(path.read_bytes()).hexdigest())

    def test_ai_simulation_and_misclassified_markers_require_permission(self):
        for wording in ['AI 模拟示意','ＡＩ 模擬','A\u200bI模拟','AI-generated picture','制作说明','内部验收记录','video watermark','Created using AI']:
            with self.subTest(wording=wording):
                self.item.update(text=wording,purposes=['mechanism'])
                self.assertTrue(guard.marking_cue(wording))
                self.assert_blocked(self.plan(),'original user message')

    def test_ai_research_wording_documents_conservative_screening_limit(self):
        # Known conservative false positives, not a claim that these science
        # statements are production labels. Manual scientific review is needed;
        # this revision deliberately does not invent a self-approved exemption.
        for wording in ['AI模拟大气环流用于预测天气','人工智能辅助识别细胞结构']:
            self.assertTrue(guard.marking_cue(wording))

    def test_ai_disclosure_requires_notice_as_well_as_specific_consent(self):
        self.item.update(text='AI生成画面',purposes=['ai_simulation']);consent_item(self.item,self.root)
        self.assert_blocked(self.plan(),'production/material-defect cue')
        self.item.update(text='AI模拟示意',purposes=['mechanism']);consent_item(self.item,self.root)
        self.assert_blocked(self.plan(),'production/material-defect cue')

    def test_ai_disclosure_in_companion_needs_no_visual_item_or_consent(self):
        self.data['presentation_text']['required_notices']=[{'id':'AI','purpose':'ai_simulation',
          'text':'AI生成画面','basis':'Synthetic platform disclosure obligation','placement':'companion',
          'placement_basis':'Synthetic platform field accepts the declaration','companion_destination':'platform AI field'}]
        self.assertEqual(self.plan(),[])

    def test_metv2_unrequested_label_is_failure_example(self):
        self.item.update(text='AI模拟示意',purposes=['mechanism'],kind='marking')
        self.assert_blocked(self.plan(),'original user message')
        self.manifest['observed'][0].update(text='AI模拟示意',position='upper corner')
        self.assert_blocked(self.overlay(),'specifically consented')

    def test_plan_requires_no_actual_export(self):
        self.assertEqual(self.plan(),[])
        self.assertFalse((self.root/'overlay.json').exists())

    def test_bound_scientific_overlay_fixture_passes_structurally(self):
        self.assertEqual(self.overlay(),[])

    def test_missing_actual_overlay_evidence_blocks(self):
        checks=Checks(self.data,self.root)
        guard.validate_overlay_review(checks,'G2',self.view,{}, {'label':self.item},{'label'})
        self.assert_blocked(checks.errors,'evidence file required')

    def test_unknown_source_and_unknown_overlay_block(self):
        for field,value,fragment in [('unknown_overlays',['unidentified corner logo'],'unknown/untracked'),('sources',[],'source inventory'),('observed',[{'item_id':'unlisted','source_ids':['source']}],'unknown/unclassified')]:
            with self.subTest(field=field):
                old=copy.deepcopy(self.manifest);self.manifest[field]=value
                self.assert_blocked(self.overlay(),fragment);self.manifest=old
        self.manifest['observed'][0]['source_ids']=['missing']
        self.assert_blocked(self.overlay(),'source unknown')

    def test_source_hash_and_output_inventory_binding_are_verified(self):
        self.manifest['sources'][0]['sha256']='0'*64
        self.assert_blocked(self.overlay(),'hash stale')
        for field in ['media_sha256','inventory_sha256']:
            self.manifest[field]='f'*64;self.assert_blocked(self.overlay(),'stale media/inventory')

    def test_actual_unclassified_or_changed_text_is_blocked(self):
        self.manifest['observed'][0]['text']='AI模拟示意'
        self.assert_blocked(self.overlay(),'differs from classified')
        self.manifest['observed']=[]
        self.assert_blocked(self.overlay(),'does not cover')

    def test_actual_label_location_or_time_change_blocks(self):
        self.item.update(text='Jane / CC BY 4.0',purposes=['attribution']);consent_item(self.item,self.root)
        self.manifest['observed'][0].update(guard.scope(self.item))
        for key,value in [('position','top left'),('time_range',[.2,1])]:
            old=copy.deepcopy(self.manifest);self.manifest['observed'][0][key]=value
            self.assert_blocked(self.overlay(),'specifically consented');self.manifest=old

    def test_actual_inspection_all_zones_full_time_and_stage_required(self):
        for field,value,fragment in [('actual_output_inspected',False,'must be inspected'),('method','source_only','must be inspected'),('zones',['subtitles'],'coverage required'),('time_range',[0,.5],'whole current'),('stage','G3','whole current')]:
            with self.subTest(field=field):
                old=copy.deepcopy(self.manifest);self.manifest[field]=value
                self.assert_blocked(self.overlay(),fragment);self.manifest=old

    def test_malformed_inventory_is_blocked_without_crashing(self):
        for field,value in [('sources',[None,{'id':[]}]),('observed',[None,{'item_id':[]}]),('zones',[[]]),('observed',None)]:
            with self.subTest(field=field):
                old=copy.deepcopy(self.manifest);self.manifest[field]=value
                self.assertTrue(self.overlay());self.manifest=old


if __name__=='__main__':unittest.main()
