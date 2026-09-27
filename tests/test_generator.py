import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('builder',str(Path(__file__).resolve().parents[1]/'scripts/build_html.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class Generator(unittest.TestCase):
 def data(self):return json.loads((Path(__file__).resolve().parents[1]/'examples/demo.json').read_text())
 def test_injection(self):
  d=self.data();d['cards'][0]['sentence']='figure out </script><script>window.pwned=true</script> 中文 & "quoted"'
  with tempfile.TemporaryDirectory() as p:
   f=Path(p)/'a.html';b.build(d,f);html=f.read_text();self.assertNotIn('<script>window.pwned',html);self.assertIn('\\u003c/script',html)
 def test_duplicate(self):
  d=self.data();d['cards'].append(d['cards'][0]);self.assertRaises(ValueError,b.validate,d)
 def test_missing(self):
  d=self.data();del d['cards'][0]['ipa'];self.assertRaises(ValueError,b.validate,d)
 def test_empty(self):
  d=self.data();d['cards']=[];self.assertRaises(ValueError,b.validate,d)
 def test_stable_ids(self):
  d=self.data();before=b.validate(d)['cards'][0]['id'];d['cards'].reverse();self.assertEqual(before,b.validate(d)['cards'][-1]['id'])
 def test_targets_inflection(self):
  d=self.data();d['cards'][0]['sentence']='She figured it out.';d['cards'][0]['targets']=['figured','out'];self.assertEqual(b.validate(d)['cards'][0]['target_spans'],[[4,11],[15,18]])
 def test_missing_target(self):
  d=self.data();d['cards'][0]['term']='missing';self.assertRaises(ValueError,b.validate,d)
 def test_word_boundary(self):
  d=self.data();d['cards'][0]['term']='can';d['cards'][0]['sentence']='A candle.';self.assertRaises(ValueError,b.validate,d)
 def test_utf16(self):
  d=self.data();d['cards'][0]['sentence']='😀 figure out';self.assertEqual(b.validate(d)['cards'][0]['target_spans'],[[3,13]])
 def test_merge_adds_and_replaces_deck_without_losing_others(self):
  first=self.data()
  second=self.data();second['title']='演示词库 2';second['deck_id']='demo:second:zh'
  with tempfile.TemporaryDirectory() as p:
   page=Path(p)/'juyouci.html'
   b.build(first,page);b.build(second,page)
   library,_,_=b.existing_library(page.read_text())
   self.assertEqual([x['deck_id'] for x in library['decks']],[first['deck_id'],second['deck_id']])
   second['note']='已更新';b.build(second,page)
   library,_,_=b.existing_library(page.read_text())
   self.assertEqual(len(library['decks']),2)
   self.assertEqual(library['decks'][0]['deck_id'],first['deck_id'])
   self.assertEqual(library['decks'][1]['note'],'已更新')
 def test_migrate_legacy_single_deck_html(self):
  d=self.data();d['cards'][0]['sentence']='She figured it out.';d['cards'][0]['targets']=['figured','out']
  normalized=b.validate(d)
  legacy_cards=[]
  for card in normalized['cards']:
   card=dict(card);card.pop('targets');card.pop('answers');legacy_cards.append(card)
  legacy={'title':normalized['title'],'deck_id':normalized['deck_id'],'cards':legacy_cards,'sources':normalized['sources'],'note':''}
  with tempfile.TemporaryDirectory() as p:
   page=Path(p)/'old.html'
   page.write_text('<script type="application/json" id="vocab-data">'+b.safe_json(legacy)+'</script>')
   second=self.data();second['deck_id']='demo:second:zh';b.build(second,page)
   library,_,_=b.existing_library(page.read_text())
   self.assertEqual(len(library['decks']),2)
   self.assertEqual(library['decks'][0]['cards'][0]['targets'],['figured','out'])
if __name__=='__main__':unittest.main()
