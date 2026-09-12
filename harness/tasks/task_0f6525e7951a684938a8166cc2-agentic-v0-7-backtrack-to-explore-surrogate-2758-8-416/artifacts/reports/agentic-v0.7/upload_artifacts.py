"""Publish this task's report artifacts through the supported Harness doc-sync route."""
import hashlib
import json
import subprocess
from pathlib import Path

TASK='task_0f6525e7951a684938a8166cc2'
OUT=Path(__file__).resolve().parent
index=OUT/'uploaded.json'
uploaded=json.loads(index.read_text()) if index.exists() else {}
for p in sorted(OUT.rglob('*')):
    if not p.is_file() or p.suffix not in {'.md','.json','.jsonl','.log','.py','.png'}:
        continue
    if '__pycache__' in p.parts or p.name in {'uploaded.json','upload.log'}:
        continue
    relative=str(p.relative_to(OUT));digest=hashlib.sha256(p.read_bytes()).hexdigest()
    if uploaded.get(relative)==digest:
        continue
    result=subprocess.run(['ha','task','artifact','add',TASK,'--source',str(p),
        '--destination','reports/agentic-v0.7/'+relative],capture_output=True,text=True)
    print(relative,result.returncode,result.stdout.strip(),result.stderr.strip(),flush=True)
    if result.returncode:
        raise RuntimeError('artifact publication failed: '+relative)
    uploaded[relative]=digest
    index.write_text(json.dumps(uploaded,indent=2)+'\n')
result=subprocess.run(['ha','doc','sync','--submit','--task',TASK],capture_output=True,text=True)
print(result.stdout,result.stderr,flush=True)
if result.returncode:
    raise RuntimeError('task doc sync failed')
