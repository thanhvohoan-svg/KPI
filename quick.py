"""Quick declaration and quarter-scoped evidence catalogue. Never confirms a task implicitly."""
from core import normalize,end_of_quarter,audit
from pathlib import Path

def setup(c):
 c.execute("""CREATE TABLE IF NOT EXISTS quick_templates(id INTEGER PRIMARY KEY,period INTEGER NOT NULL REFERENCES periods(id),department INTEGER REFERENCES departments(id),title TEXT NOT NULL,axis INTEGER NOT NULL,grp INTEGER NOT NULL,product TEXT NOT NULL,source TEXT NOT NULL,qty INTEGER NOT NULL,due TEXT NOT NULL,actor INTEGER NOT NULL REFERENCES users(id))""")
 c.execute("""CREATE TABLE IF NOT EXISTS evidence_store(id INTEGER PRIMARY KEY,period INTEGER NOT NULL REFERENCES periods(id),scope TEXT NOT NULL CHECK(scope IN ('school','team','personal')),department INTEGER REFERENCES departments(id),owner INTEGER NOT NULL REFERENCES users(id),title TEXT NOT NULL,reference TEXT NOT NULL,task_title TEXT NOT NULL,filename TEXT NOT NULL DEFAULT '',body BLOB)""")
 c.execute("""CREATE TABLE IF NOT EXISTS evidence_links(task INTEGER REFERENCES tasks(id) ON DELETE CASCADE,evidence INTEGER REFERENCES evidence_store(id),PRIMARY KEY(task,evidence))""")

def scope_sql(e):
 return ("period=? AND (scope='school' OR (scope='team' AND department=?) OR (scope='personal' AND owner=?))",(e['period'],e['department'],e['user']))

def available(c,e):
 setup(c)
 sql,args=scope_sql(e)
 return c.execute('SELECT id,scope,title,reference,task_title,filename FROM evidence_store WHERE '+sql+' ORDER BY title,id',args).fetchall()

def templates(c,e,axis):
 setup(c)
 return c.execute('SELECT * FROM quick_templates WHERE period=? AND axis=? AND (department IS NULL OR department=?) ORDER BY title,id',(e['period'],axis,e['department'])).fetchall()

def linked(c,tid):
 setup(c)
 return c.execute('SELECT s.id,s.title,s.reference,s.filename FROM evidence_store s JOIN evidence_links l ON l.evidence=s.id WHERE l.task=? ORDER BY s.title,s.id',(tid,)).fetchall()

def enrich(c,tasks):
 setup(c)
 out=[]
 for t in tasks:
  t=dict(t);t['manual_evidence']=t['evidence'] or ''
  refs=linked(c,t['id'])
  extra=['Kho minh chứng: '+r['title']+(' · '+r['reference'] if r['reference'] else '')+(' · '+r['filename'] if r['filename'] else '') for r in refs]
  if not t['manual_evidence'] and not extra:
   extra=['Tệp: '+r['filename'] for r in c.execute('SELECT filename FROM attachments WHERE task=? ORDER BY id',(t['id'],))]
  t['evidence']='; '.join(x for x in [t['manual_evidence']]+extra if x)
  out.append(t)
 return out

def links_html(c,tid):
 from app import h
 return ''.join('<p class="linked-evidence"><b>'+h(r['title'])+'</b>'+(' · '+h(r['reference']) if r['reference'] else '')+(' · <a href="/quick/file/'+str(r['id'])+'?task='+str(tid)+'">'+h(r['filename'])+'</a>' if r['filename'] else '')+'</p>' for r in linked(c,tid))

def prior(c,e,axis):
 prev=c.execute('SELECT e.id,p.year,p.quarter FROM evaluations e JOIN periods p ON p.id=e.period WHERE e.user=? AND (p.year*4+p.quarter)=(?*4+?-1)',(e['user'],e['year'],e['quarter'])).fetchone()
 if not prev:return None,[]
 return prev,c.execute('SELECT * FROM tasks WHERE evaluation=? AND axis=? AND cancelled=0 ORDER BY id',(prev['id'],axis)).fetchall()

def panel(c,e,csrf,axis,rows):
 from app import h,form,check
 ts=templates(c,e,axis);existing={(normalize(t['title']),normalize(t['source'])) for t,z in rows}
 ts=[t for t in ts if (normalize(t['title']),normalize(t['source'])) not in existing]
 prev,old=prior(c,e,axis)
 old=[t for t in old if not any(normalize(t['title'])==normalize(x['title']) for x,z in rows)]
 items=available(c,e)
 out='<details class="quick-panel"><summary><b>Nhập nhanh công việc</b><span>Chọn nhiều · Sao chép · Xác nhận</span></summary><div class="quick-body">'
 if ts:
  fields='<input type="hidden" name="axis" value="'+str(axis)+'">'+''.join(check('Chọn · '+t['title']+' · '+t['product']+' · Nhóm '+str(t['grp'])+' · SL '+str(t['qty'])+' · '+t['source'],'tpl_'+str(t['id'])) for t in ts)
  out+='<h3>Chọn nhiệm vụ chuẩn</h3>'+form('/action/quick_add/'+str(e['id']),csrf,fields,'Thêm các công việc đã chọn')
 else:out+='<p class="muted">Chưa có nhiệm vụ chuẩn chưa chọn trong trục này. Có thể nhập riêng hoặc đề nghị tổ trưởng bổ sung danh mục.</p>'
 if old:
  fields='<input type="hidden" name="axis" value="'+str(axis)+'">'+''.join(check(t['title']+' · '+t['product'],'old_'+str(t['id'])) for t in old)+check('Xác nhận tên, sản phẩm, nhóm, số lượng và căn cứ vẫn phù hợp quý này','confirmed')
  out+='<h3>Sao chép từ quý trước</h3><p class="muted">Không sao chép kết quả, minh chứng hoặc điểm. Hạn đặt lại cuối quý hiện tại; rà soát nếu có hạn riêng.</p>'+form('/action/quick_copy/'+str(e['id']),csrf,fields,'Sao chép công việc đã chọn')
 cutoff=end_of_quarter(e['year'],e['quarter']).isoformat()
 candidates=[t for t,z in rows if not t['cancelled'] and t['done'] is None and t['corrections'] is None and not t['finish'] and (t['effective_due'] or t['due'])==cutoff and t['late_override'] is None]
 if candidates:
  fields='<input type="hidden" name="axis" value="'+str(axis)+'">'
  for t in candidates:
   fields+=check(t['title']+' · '+str(t['qty'])+' sản phẩm','done_'+str(t['id']))
   suggested=[r for r in items if normalize(r['task_title'])==normalize(t['title'])]
   if suggested:
    fields+='<div class="quick-suggestions"><small>Minh chứng phù hợp đã có trong kho (chọn nếu đúng thực tế)</small>'+''.join(check(r['title']+' · '+r['scope'],'link_'+str(t['id'])+'_'+str(r['id'])) for r in suggested)+'</div>'
  fields+=check('Tôi xác nhận các công việc đã chọn hoàn thành đủ số lượng, đúng hạn, không phải chỉnh sửa; minh chứng đã chọn thực sự liên quan.','confirmed')
  out+='<h3>Xác nhận kết quả hàng loạt</h3>'+form('/action/quick_done/'+str(e['id']),csrf,fields,'Lưu kết quả đã xác nhận')
 return out+'</div></details>'

def evidence_form(c,e,t,csrf):
 from app import h,form,check
 items=available(c,e);have={r['id'] for r in linked(c,t['id'])}
 matches=[r for r in items if normalize(r['task_title'])==normalize(t['title'])]
 rest=[r for r in items if r['id'] not in {x['id'] for x in matches}]
 fields=''
 for label,rs in [('Gợi ý theo công việc',matches),('Minh chứng khác trong kho',rest)]:
  if rs:fields+='<h4>'+label+'</h4>'+''.join(check(r['title']+(' · '+r['reference'] if r['reference'] else ''),'ev_'+str(r['id']),r['id'] in have) for r in rs)
 body=links_html(c,t['id'])
 if fields:body+=form('/action/quick_link/'+str(t['id']),csrf,fields+check('Xác nhận minh chứng đã chọn đúng với công việc','confirmed'),'Lưu liên kết')
 return '<details class="quick-evidence"><summary>Chọn từ kho minh chứng</summary>'+body+'<p><a href="/quick?period='+str(e['period'])+'">Mở kho minh chứng</a></p></details>'

def admin_panel(c,u,p,csrf):
 from app import h,form,field,select,textarea,table,can_manage
 from axis_self import quarter_label,quarter_field
 pid=p['id'];manage=can_manage(u);leader=u['role']=='leader' and u['department'] is not None
 dep=u['department']
 body='<section class="panel"><h2>Kho minh chứng · '+h(quarter_label(p))+'</h2><p>Chỉ thêm văn bản, đường dẫn hoặc tệp thực sự tồn tại. Không tự xác nhận sự tham gia của giáo viên.</p>'
 # period rows have id instead of period; scope for current user's catalogue
 e={'period':pid,'department':dep,'user':u['id']}
 scopes=[('personal','Cá nhân')]+([('school','Toàn trường')] if manage else [])+([('team','Tổ chuyên môn')] if leader else [])
 if not p['locked']:
  fields=select('Phạm vi','scope',scopes,'personal')+field('Tên minh chứng','title',attrs='required maxlength="500"')+field('Tên công việc liên quan (để gợi ý tự động)','task_title',attrs='maxlength="500"')+textarea('Số văn bản, đường dẫn hoặc mô tả vị trí lưu trữ','reference')+field('Tệp (không bắt buộc)','file',kind='file',attrs='accept=".txt"' if __import__('app').DEMO else 'accept=".pdf,.docx,.xlsx,.png,.jpg,.jpeg,.txt"')
  body+=form('/action/quick_evidence/'+str(pid),csrf,fields,'Thêm minh chứng',extra='enctype="multipart/form-data"')
 rs=available(c,e)
 body+=table(['Tên minh chứng','Phạm vi','Căn cứ','Tệp'],[[h(r['title']),h({'school':'Trường','team':'Tổ','personal':'Cá nhân'}[r['scope']]),h(r['reference']),'<a href="/quick/file/'+str(r['id'])+'">'+h(r['filename'])+'</a>' if r['filename'] else '—'] for r in rs])+'</section>'
 if manage or leader:
  if manage:depopts=[('','Toàn trường')]+[(r['id'],r['name']) for r in c.execute('SELECT * FROM departments ORDER BY name')]
  else:depopts=[(dep,'Tổ của tôi')]
  body+='<section class="panel"><h2>Danh mục nhiệm vụ chuẩn</h2><p>Thông tin đã được xác định trước theo quý; giáo viên chọn một lần để tạo công việc.</p>'
  if not p['locked']:
   fields=select('Áp dụng','department',depopts)+field('Nội dung công việc','title',attrs='required')+select('Trục','axis',[(i,'Trục '+str(i)) for i in range(1,7)])+select('Nhóm','grp',[(i,'Nhóm '+str(i)) for i in range(1,5)])+field('Sản phẩm','product',attrs='required')+field('Căn cứ giao nhiệm vụ','source',attrs='required')+field('Số lượng','qty',1,'number','min="1" max="1000000" required')+quarter_field(p,'Thời hạn','due')
   body+=form('/action/quick_template/'+str(pid),csrf,fields,'Thêm nhiệm vụ chuẩn')
  ts=c.execute('SELECT * FROM quick_templates WHERE period=? AND (? OR department=? OR department IS NULL) ORDER BY axis,title',(pid,int(manage),dep)).fetchall()
  body+=table(['Công việc','Trục','Nhóm','Sản phẩm','Số lượng','Căn cứ'],[[h(t['title']),t['axis'],t['grp'],h(t['product']),t['qty'],h(t['source'])] for t in ts])+'</section>'
 return body+'<script src="/static/axis.js?v=217" defer></script>'

async def action(c,u,f,action,obj):
 from app import get_eval,own_edit,period,unlocked,integer,required,optional,one,fail,redirect,can_manage,DEMO,UploadFile
 from axis_self import read_quarter
 setup(c);uid=u['id']
 if action in ('quick_template','quick_evidence'):
  p=period(c,obj);unlocked(p);dep=u['department'];manage=can_manage(u);leader=u['role']=='leader' and dep is not None
  if action=='quick_template':
   if not (manage or leader):fail('Không có quyền tạo nhiệm vụ chuẩn.',403)
   d=integer(f,'department',1,10**9,True)
   if not manage and d!=dep:fail('Chỉ được tạo nhiệm vụ cho tổ mình.',403)
   if d and not one(c,'SELECT id FROM departments WHERE id=?',(d,)):fail('Tổ không hợp lệ.')
   title=required(f,'title');source=required(f,'source');axis=integer(f,'axis',1,6);grp=integer(f,'grp',1,4);product=required(f,'product');qty=integer(f,'qty',1,1000000);due=read_quarter(f,'due',p)
   if due>end_of_quarter(p['year'],p['quarter']).isoformat():fail('Hạn sau quý.')
   if one(c,'SELECT id FROM quick_templates WHERE period=? AND department IS ? AND title=? AND source=?',(obj,d,title,source)):fail('Nhiệm vụ chuẩn đã có.')
   c.execute('INSERT INTO quick_templates(period,department,title,axis,grp,product,source,qty,due,actor) VALUES(?,?,?,?,?,?,?,?,?,?)',(obj,d,title,axis,grp,product,source,qty,due,uid));audit(c,uid,'Tạo nhiệm vụ chuẩn',detail=title)
  else:
   scope=required(f,'scope')
   if scope not in ('personal','school','team') or (scope=='school' and not manage) or (scope=='team' and not leader):fail('Không có quyền tạo minh chứng phạm vi này.',403)
   title=required(f,'title');ref=optional(f,'reference');match=optional(f,'task_title',500);file=f.get('file');name='';data=None
   if isinstance(file,UploadFile) and file.filename:
    name=Path(file.filename.replace('\\','/')).name[:180];data=await file.read(5*1024*1024+1);await file.close()
    if Path(name).suffix.lower() not in ('.pdf','.docx','.xlsx','.png','.jpg','.jpeg','.txt') or not data or len(data)>5*1024*1024:fail('Tệp không hợp lệ.')
    if DEMO and (Path(name).suffix.lower()!='.txt' or len(data)>100000 or one(c,'SELECT COALESCE(SUM(length(body)),0) FROM evidence_store')[0]+len(data)>1000000):fail('Demo chỉ nhận TXT giả lập tối đa 100 KB, tổng 1 MB.')
   if not ref and not data:fail('Cần căn cứ hoặc tệp minh chứng thực tế.')
   c.execute('INSERT INTO evidence_store(period,scope,department,owner,title,reference,task_title,filename,body) VALUES(?,?,?,?,?,?,?,?,?)',(obj,scope,dep if scope=='team' else None,uid,title,ref,match,name,data));audit(c,uid,'Thêm minh chứng vào kho',detail=title)
  return redirect('/quick?period='+str(obj))
 if action=='quick_link':
  t=one(c,'SELECT * FROM tasks WHERE id=?',(obj,))
  if not t:fail('Không tìm thấy công việc.',404)
  e=get_eval(c,u,t['evaluation']);own_edit(u,e)
  if t['cancelled'] or not f.get('confirmed'):fail('Cần xác nhận minh chứng.')
  items=available(c,e);allowed={r['id'] for r in items}
  wanted={int(k[3:]) for k in f.keys() if k.startswith('ev_') and k[3:].isdigit() and f.get(k)}
  if not wanted<=allowed:fail('Minh chứng ngoài phạm vi.',403)
  c.execute('DELETE FROM evidence_links WHERE task=?',(obj,))
  for k in wanted:c.execute('INSERT INTO evidence_links VALUES(?,?)',(obj,k))
  audit(c,uid,'Liên kết minh chứng',e['id'],str(obj));return redirect('/eval/'+str(e['id'])+'?axis='+str(t['axis'])+'#axis-workspace')
 e=get_eval(c,u,obj);own_edit(u,e);axis=integer(f,'axis',1,6);cutoff=end_of_quarter(e['year'],e['quarter']).isoformat()
 if action=='quick_done':
  if not f.get('confirmed'):fail('Cần xác nhận kết quả thực tế.')
  ts=c.execute('SELECT * FROM tasks WHERE evaluation=? AND axis=? AND cancelled=0',(obj,axis)).fetchall()
  selected=[t for t in ts if f.get('done_'+str(t['id']))]
  if not selected:fail('Chưa chọn công việc.')
  refs=available(c,e);allowed={r['id']:r for r in refs}
  for t in selected:
   if t['done'] is not None or t['corrections'] is not None or t['finish'] or (t['effective_due'] or t['due'])!=cutoff or t['late_override'] is not None:fail('Công việc đã có kết quả hoặc có hạn riêng; mở từng công việc để rà soát.')
   prefix='link_'+str(t['id'])+'_'
   ids={int(k[len(prefix):]) for k in f.keys() if k.startswith(prefix) and k[len(prefix):].isdigit() and f.get(k)}
   if any(k not in allowed or normalize(allowed[k]['task_title'])!=normalize(t['title']) for k in ids):fail('Minh chứng ngoài phạm vi hoặc không phù hợp.',403)
   for k in ids:c.execute('INSERT OR IGNORE INTO evidence_links VALUES(?,?)',(t['id'],k))
   c.execute('UPDATE tasks SET done=qty,corrections=0,finish=? WHERE id=?',(cutoff,t['id']));audit(c,uid,'Xác nhận kết quả hàng loạt',obj,t['title'])
 else:
  if action=='quick_add':chosen=[t for t in templates(c,e,axis) if f.get('tpl_'+str(t['id']))]
  elif action=='quick_copy':
   if not f.get('confirmed'):fail('Cần rà soát nhiệm vụ quý trước.')
   _,old=prior(c,e,axis);chosen=[t for t in old if f.get('old_'+str(t['id']))]
  else:fail('Thao tác không tồn tại.',404)
  if not chosen:fail('Chưa chọn nhiệm vụ hợp lệ.')
  if DEMO and one(c,'SELECT count(*) FROM tasks')[0]+len(chosen)>400:fail('Demo giới hạn 400 nhiệm vụ.')
  existing={(normalize(t['title']),normalize(t['source'])) for t in c.execute('SELECT title,source FROM tasks WHERE evaluation=?',(obj,))}
  for t in chosen:
   key=(normalize(t['title']),normalize(t['source']))
   if key in existing:continue
   tid=c.execute('INSERT INTO tasks(evaluation,title,source,axis,grp,product,qty,due) VALUES(?,?,?,?,?,?,?,?)',(obj,t['title'],t['source'],axis,t['grp'],t['product'],t['qty'],cutoff if action=='quick_copy' else t['due'])).lastrowid
   existing.add(key);audit(c,uid,'Tự khai nhiệm vụ',obj,str(tid));audit(c,uid,'Nhập nhanh nhiệm vụ',obj,t['title'])
 return redirect('/eval/'+str(obj)+'?axis='+str(axis)+'#axis-workspace')
