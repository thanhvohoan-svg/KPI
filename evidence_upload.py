"""Evidence uploads, stored as private download-only attachments."""
import os
from pathlib import Path
from starlette.datastructures import UploadFile

MB=1024*1024
FILE_LIMIT=int(os.environ.get('KPI_FILE_LIMIT_MB','25'))*MB
REQUEST_LIMIT=int(os.environ.get('KPI_REQUEST_LIMIT_MB','100'))*MB
DEMO_LIMIT=int(os.environ.get('KPI_DEMO_EVIDENCE_LIMIT_MB','200'))*MB

def read_file(c,file,required=False):
 from app import fail,DEMO
 if not isinstance(file,UploadFile) or not file.filename:
  if required:fail('Chưa chọn tệp.')
  return None
 name=Path(file.filename.replace(chr(92),'/')).name
 name=''.join(x for x in name if ord(x)>=32 and ord(x)!=127)[:180]
 try:data=file.file.read(FILE_LIMIT+1)
 finally:file.file.close()
 if not name or not data:fail('Tệp không hợp lệ.')
 if len(data)>FILE_LIMIT:fail('Tệp vượt dung lượng '+str(FILE_LIMIT//MB)+' MB.',413)
 if DEMO:
  import quick
  quick.setup(c)
  used=c.execute('SELECT COALESCE(SUM(length(body)),0) FROM attachments').fetchone()[0]+c.execute('SELECT COALESCE(SUM(length(body)),0) FROM evidence_store').fetchone()[0]
  if used+len(data)>DEMO_LIMIT:fail('Kho thử nghiệm đã hết dung lượng.',413)
 return name,data

def save_files(c,u,e,tid,f,required=False):
 from app import audit,fail
 files=[x for x in f.getlist('file') if isinstance(x,UploadFile) and x.filename]
 if required and not files:fail('Chưa chọn tệp.')
 for file in files:
  name,data=read_file(c,file,True)
  c.execute('INSERT INTO attachments(task,filename,body) VALUES(?,?,?)',(tid,name,data))
  audit(c,u['id'],'Đính kèm minh chứng',e['id'],name)

def fields(c=None,t=None):
 from app import h,textarea,field
 value=t.get('manual_evidence',t['evidence']) if t is not None else ''
 out='<div class="evidence-entry"><div>'+textarea('Minh chứng bổ sung (nếu có)','evidence',value,attrs='rows="2" maxlength="2000"')+'</div><div>'+field('Đính kèm minh chứng','file',kind='file',attrs='multiple')
 if c is not None and t is not None:
  rs=c.execute('SELECT id,filename FROM attachments WHERE task=? ORDER BY id',(t['id'],)).fetchall()
  if rs:out+='<div class="evidence-uploads">'+''.join('<a href="/attachment/'+str(r['id'])+'">'+h(r['filename'])+'</a>' for r in rs)+'</div>'
 return out+'</div></div>'
