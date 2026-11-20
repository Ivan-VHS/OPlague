from __future__ import annotations
import hashlib,json,math,tempfile,unittest
from pathlib import Path
from tools.reaper_report import AUDIT_SCHEMA,ReaperReportError,read_reaper_report,validate_reaper_comparison_report
def fixture():
 r={"schema":"reaper.oplage-comparison.v1","mode":"read_only","reference_snapshot_sha256":"a"*64,"candidate_snapshot_sha256":"b"*64,"dimensions":["cpu","memory"],"dimension_count":2,"euclidean_distance":math.hypot(.3,.1),"python_euclidean_distance":math.hypot(.3,.1),"distance_backend":"reaper-python","components":{"cpu":{"reference":.5,"candidate":.8,"difference":.3},"memory":{"reference":.7,"candidate":.8,"difference":.1}}}
 r["report_sha256"]=hashlib.sha256(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest();return r
class ReaperReportTests(unittest.TestCase):
 def test_valid(self):
  x=validate_reaper_comparison_report(fixture());self.assertEqual(x["schema"],AUDIT_SCHEMA);self.assertTrue(x["accepted"])
 def test_regular_file(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.json";p.write_text(json.dumps(fixture()),encoding="utf-8");self.assertTrue(read_reaper_report(p)["accepted"])
 def test_bad_digest(self):
  x=fixture();x["report_sha256"]="c"*64
  with self.assertRaisesRegex(ReaperReportError,"report_sha256"):validate_reaper_comparison_report(x)
 def test_bad_difference(self):
  x=fixture();x["components"]["cpu"]["difference"]=.2
  with self.assertRaisesRegex(ReaperReportError,"difference"):validate_reaper_comparison_report(x)
 def test_bad_dimensions_and_nan(self):
  x=fixture();x["dimensions"]=["cpu","other"]
  with self.assertRaisesRegex(ReaperReportError,"exactly"):validate_reaper_comparison_report(x)
  x=fixture();x["components"]["cpu"]["reference"]=float("nan")
  with self.assertRaisesRegex(ReaperReportError,"finite"):validate_reaper_comparison_report(x)
 def test_bad_mode_backend(self):
  x=fixture();x["mode"]="write"
  with self.assertRaisesRegex(ReaperReportError,"read_only"):validate_reaper_comparison_report(x)
  x=fixture();x["distance_backend"]="mystery"
  with self.assertRaisesRegex(ReaperReportError,"unsupported"):validate_reaper_comparison_report(x)
 def test_duplicate_keys_and_symlinks(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"dup.json";p.write_text('{"schema":"a","schema":"b"}',encoding="utf-8")
   with self.assertRaisesRegex(ReaperReportError,"duplicate"):read_reaper_report(p)
   q=Path(d)/"link.json"
   try:q.symlink_to(p)
   except (OSError,NotImplementedError):self.skipTest("symlink unavailable")
   with self.assertRaisesRegex(ReaperReportError,"non-symlink"):read_reaper_report(q)
if __name__=="__main__":unittest.main()
