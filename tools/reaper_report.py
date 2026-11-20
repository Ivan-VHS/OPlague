"""Read-only importer for Reaper's versioned OPlague comparison reports."""
from __future__ import annotations
import argparse,hashlib,hmac,json,math,os,re,sys
from pathlib import Path
from typing import Any
REPORT_SCHEMA="reaper.oplage-comparison.v1";AUDIT_SCHEMA="oplage.reaper-report-audit.v1";MAX_JSON_BYTES=16*1024*1024;MAX_DIMENSIONS=128
_SHA256=re.compile(r"^[0-9a-f]{64}$")
class ReaperReportError(ValueError): """Invalid Reaper comparison report."""
def _unique(pairs:list[tuple[str,Any]])->dict[str,Any]:
 result={}
 for k,v in pairs:
  if k in result:raise ReaperReportError(f"duplicate JSON key: {k}")
  result[k]=v
 return result
def _canonical(v:Any)->bytes:
 try:return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
 except (TypeError,ValueError,OverflowError) as e:raise ReaperReportError(f"report is not canonical finite JSON: {e}") from e
def _number(v:Any,field:str,minimum:float|None=None)->float:
 if isinstance(v,bool) or not isinstance(v,(int,float)):raise ReaperReportError(f"{field} must be a real number")
 n=float(v)
 if not math.isfinite(n):raise ReaperReportError(f"{field} must be finite")
 if minimum is not None and n<minimum:raise ReaperReportError(f"{field} must be >= {minimum}")
 return n
def _digest(v:Any,field:str)->str:
 if not isinstance(v,str) or not _SHA256.fullmatch(v):raise ReaperReportError(f"{field} must be a lowercase SHA-256 digest")
 return v
def validate_reaper_comparison_report(r:Any)->dict[str,Any]:
 if not isinstance(r,dict):raise ReaperReportError("Reaper report must be a JSON object")
 required={"schema","mode","reference_snapshot_sha256","candidate_snapshot_sha256","dimensions","dimension_count","euclidean_distance","python_euclidean_distance","distance_backend","components","report_sha256"}
 if not required.issubset(r) or set(r)-required-{"native_backend"}:raise ReaperReportError("Reaper report fields do not match v1")
 if r["schema"]!=REPORT_SCHEMA:raise ReaperReportError(f"report schema must be {REPORT_SCHEMA}")
 if r["mode"]!="read_only":raise ReaperReportError("only read_only reports are accepted")
 _digest(r["reference_snapshot_sha256"],"reference_snapshot_sha256");_digest(r["candidate_snapshot_sha256"],"candidate_snapshot_sha256")
 dims=r["dimensions"]
 if not isinstance(dims,list) or not 1<=len(dims)<=MAX_DIMENSIONS:raise ReaperReportError("dimensions outside permitted bounds")
 if any(not isinstance(x,str) or not x.strip() or len(x)>128 for x in dims) or len(set(dims))!=len(dims):raise ReaperReportError("invalid or duplicate dimensions")
 if type(r["dimension_count"]) is not int or r["dimension_count"]!=len(dims):raise ReaperReportError("dimension_count mismatch")
 comp=r["components"]
 if not isinstance(comp,dict) or set(comp)!=set(dims):raise ReaperReportError("components must contain exactly declared dimensions")
 ss=[]
 for name in dims:
  x=comp[name]
  if not isinstance(x,dict) or set(x)!={"reference","candidate","difference"}:raise ReaperReportError(f"{name} component shape invalid")
  a=_number(x["reference"],f"{name}.reference",0);b=_number(x["candidate"],f"{name}.candidate",0);d=_number(x["difference"],f"{name}.difference")
  if a>1 or b>1:raise ReaperReportError(f"{name} values must be in [0,1]")
  if not math.isclose(d,b-a,rel_tol=1e-12,abs_tol=1e-12):raise ReaperReportError(f"{name}.difference mismatch")
  ss.append((b-a)**2)
 expected=math.sqrt(math.fsum(ss));py=_number(r["python_euclidean_distance"],"python_euclidean_distance",0);distance=_number(r["euclidean_distance"],"euclidean_distance",0);backend=r["distance_backend"]
 if not math.isclose(py,expected,rel_tol=1e-10,abs_tol=1e-12):raise ReaperReportError("Python distance mismatch")
 if backend=="reaper-python":
  if "native_backend" in r or not math.isclose(distance,py,rel_tol=1e-10,abs_tol=1e-12):raise ReaperReportError("Python backend result inconsistent")
 elif backend=="pytyliki-c-abi-v1":
  native=r.get("native_backend")
  if not isinstance(native,dict) or native.get("abi_version")!=1 or not isinstance(native.get("library"),str) or not native["library"].strip():raise ReaperReportError("Pytyliki ABI v1 metadata required")
  if not math.isclose(distance,py,rel_tol=1e-8,abs_tol=1e-10):raise ReaperReportError("native distance differs from Python reference")
 else:raise ReaperReportError("unsupported distance backend")
 supplied=_digest(r["report_sha256"],"report_sha256");payload={k:v for k,v in r.items() if k!="report_sha256"};actual=hashlib.sha256(_canonical(payload)).hexdigest()
 if not hmac.compare_digest(supplied,actual):raise ReaperReportError("report_sha256 does not match canonical report content")
 return {"schema":AUDIT_SCHEMA,"mode":"read_only","accepted":True,"source_schema":REPORT_SCHEMA,"report_sha256":actual,"dimension_count":len(dims),"distance_backend":backend,"semantics":"integrity and shape validation only; no source authenticity or driver verdict"}
def read_reaper_report(path:str|os.PathLike[str])->dict[str,Any]:
 p=Path(path)
 if p.is_symlink() or not p.is_file():raise ReaperReportError("input must be a regular non-symlink file")
 if p.stat().st_size>MAX_JSON_BYTES:raise ReaperReportError("report exceeds 16 MiB limit")
 raw=p.read_bytes()
 if len(raw)>MAX_JSON_BYTES:raise ReaperReportError("report exceeds 16 MiB limit")
 try:r=json.loads(raw.decode("utf-8"),object_pairs_hook=_unique,parse_constant=lambda t:(_ for _ in ()).throw(ReaperReportError(f"non-finite JSON: {t}")))
 except (UnicodeDecodeError,json.JSONDecodeError) as e:raise ReaperReportError(f"invalid UTF-8 JSON: {e}") from e
 return validate_reaper_comparison_report(r)
def main(argv:list[str]|None=None)->int:
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("report");parser.add_argument("--json",action="store_true");args=parser.parse_args(argv)
 try:r=read_reaper_report(args.report)
 except (ReaperReportError,OSError,ValueError,TypeError) as e:print(f"Reaper report INVALID: {e}",file=sys.stderr);return 1
 if args.json:print(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2))
 else:print(f"REAPER REPORT VALID | {r['dimension_count']} dimensions | {r['distance_backend']} | sha256={r['report_sha256']}")
 return 0
if __name__=="__main__":raise SystemExit(main())
