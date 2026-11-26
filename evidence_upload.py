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

def save_files(c,u,e,tid,f,required=False,key='file',outstanding=False):
 from app import audit,fail
 files=[x for x in f.getlist(key) if isinstance(x,UploadFile) and x.filename]
 if required and not files:fail('Chưa chọn tệp.')
 for file in files:
  name,data=read_file(c,file,True)
  aid=c.execute('INSERT INTO attachments(task,filename,body) VALUES(?,?,?)',(tid,name,data)).lastrowid
  if outstanding:c.execute('INSERT INTO outstanding_files(attachment) VALUES(?)',(aid,))
  audit(c,u['id'],'Đính kèm minh chứng',e['id'],name)

def fields(c=None,t=None):
 from app import h,textarea,field
 value=t.get('manual_evidence',t['evidence']) if t is not None else ''
 out='<div class="evidence-entry"><div>'+textarea('Minh chứng bổ sung (nếu có)','evidence',value,attrs='rows="2" maxlength="2000"')+'</div><div>'+field('Đính kèm minh chứng','file',kind='file',attrs='multiple')
 if c is not None and t is not None:
  setup(c)
  rs=c.execute('SELECT id,filename FROM attachments WHERE task=? AND id NOT IN (SELECT attachment FROM outstanding_files) ORDER BY id',(t['id'],)).fetchall()
  if rs:out+='<div class="evidence-uploads">'+''.join('<a href="/attachment/'+str(r['id'])+'">'+h(r['filename'])+'</a>' for r in rs)+'</div>'
 return out+'</div></div>'

def setup(c):
 c.execute("CREATE TABLE IF NOT EXISTS outstanding_evidence(task INTEGER PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE, note TEXT NOT NULL DEFAULT '')")
 c.execute("CREATE TABLE IF NOT EXISTS outstanding_files(attachment INTEGER PRIMARY KEY REFERENCES attachments(id) ON DELETE CASCADE)")

def proof(c,tid):
 setup(c)
 row=c.execute('SELECT note FROM outstanding_evidence WHERE task=?',(tid,)).fetchone()
 files=c.execute('SELECT a.id,a.filename FROM attachments a JOIN outstanding_files x ON x.attachment=a.id WHERE a.task=? ORDER BY a.id',(tid,)).fetchall()
 return (row['note'] if row else ''),files

def outstanding_fields(c,t=None):
 from app import h,textarea,field
 on=bool(t and t['outstanding'])
 note,files=proof(c,t['id']) if t else ('',[])
 def radio(value,label,checked):return '<label class="check"><input type="radio" name="outstanding" value="'+value+'"'+(' checked' if checked else '')+'> '+label+'</label>'
 out='<div class="outstanding-block" data-outstanding><div class="outstanding-choice"><b>Đề xuất vượt yêu cầu</b>'+radio('0','Không',not on)+radio('1','Có',on)+'</div><div data-outstanding-details'+('' if on else ' hidden')+'>'
 out+=textarea('Mô tả kết quả nổi trội và tác động','outstanding_note',t['outstanding_note'] if t else '',attrs='rows="2" maxlength="2000" data-outstanding-note')+'<div class="evidence-entry"><div>'+textarea('Minh chứng vượt yêu cầu','outstanding_evidence',note,attrs='rows="2" maxlength="2000"')+'</div><div>'+field('Đính kèm minh chứng vượt yêu cầu','outstanding_file',kind='file',attrs='multiple')
 if files:out+='<div class="evidence-uploads">'+''.join('<a href="/attachment/'+str(r['id'])+'">'+h(r['filename'])+'</a>' for r in files)+'</div>'
 return out+'</div></div></div></div>'

def save_outstanding(c,u,e,tid,f,on,note):
 from app import fail,optional
 if not on:return
 if not note:fail('Cần mô tả kết quả vượt yêu cầu.')
 setup(c)
 old,files=proof(c,tid)
 ev=optional(f,'outstanding_evidence') if 'outstanding_evidence' in f else old
 save_files(c,u,e,tid,f,key='outstanding_file',outstanding=True)
 _,files=proof(c,tid)
 if not ev and not files:fail('Cần nhập hoặc đính kèm minh chứng vượt yêu cầu.')
 c.execute('INSERT INTO outstanding_evidence(task,note) VALUES(?,?) ON CONFLICT(task) DO UPDATE SET note=excluded.note',(tid,ev))
