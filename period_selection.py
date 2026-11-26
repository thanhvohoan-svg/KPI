"""Teacher's period selector and non-destructive task inheritance."""
from core import end_of_quarter,audit,normalize

MARK='Khởi tạo hồ sơ kỳ đánh giá'

def label(e):
 return f'Quý {e["quarter"]}/{e["year"]}'

def initialized(c,e):
 return bool(c.execute('SELECT 1 FROM tasks WHERE evaluation=? LIMIT 1',(e['id'],)).fetchone() or c.execute('SELECT 1 FROM audit WHERE evaluation=? AND actor=? AND action=? LIMIT 1',(e['id'],e['user'],MARK)).fetchone())

def personal_periods(c,u):
 return c.execute('SELECT p.*,e.id eid,e.status,e.common FROM periods p LEFT JOIN evaluations e ON e.period=p.id AND e.user=? ORDER BY p.year DESC,p.quarter DESC',(u['id'],)).fetchall()

def selector(c,u,csrf,r):
 from app import h,layout,select,fail,STATUSES
 ps=personal_periods(c,u)
 years=sorted({p['year'] for p in ps},reverse=True)
 if not years:return layout('Chọn kỳ đánh giá','<section class="panel">Chưa mở kỳ đánh giá. Vui lòng liên hệ Ban Giám hiệu.</section>',u,csrf,compact=True)
 default=next((p['year'] for p in ps if not p['locked'] and p['eid']),years[0])
 try:year=int(r.query_params.get('year',default))
 except ValueError:fail('Năm không hợp lệ.')
 if year not in years:fail('Năm chưa có kỳ đánh giá.',404)
 byq={p['quarter']:p for p in ps if p['year']==year}
 body='<section class="panel period-select"><h2>CHỌN KỲ ĐÁNH GIÁ</h2><form class="period-year" method="get" action="/my-periods">'+select('Năm đánh giá','year',[(y,y) for y in years],year)+'<button>Xem</button></form><div class="period-grid">'
 for q in range(1,5):
  p=byq.get(q);content=f'<b>QUÝ {q}</b><span>Tháng {q*3-2}–{q*3}</span>'
  if not p or not p['eid']:
   body+='<div class="period-tile unavailable" aria-disabled="true">'+content+'<small>Chưa mở hồ sơ</small></div>'
  else:
   status='Đã khóa · Chỉ xem' if p['locked'] else STATUSES.get(p['status'],'')
   body+=f'<a class="period-tile" href="/my-period/{p["eid"]}">'+content+'<small>'+h(status)+'</small></a>'
 return layout('Chọn kỳ đánh giá',body+'</div></section>',u,csrf,compact=True)

def sources(c,e):
 return c.execute('''SELECT e.id,p.year,p.quarter FROM evaluations e JOIN periods p ON p.id=e.period
 WHERE e.user=? AND (p.year*4+p.quarter)<? AND EXISTS(SELECT 1 FROM tasks t WHERE t.evaluation=e.id AND t.cancelled=0)
 ORDER BY p.year DESC,p.quarter DESC''',(e['user'],e['year']*4+e['quarter'])).fetchall()

def source_tasks(c,source):
 return c.execute('SELECT * FROM tasks WHERE evaluation=? AND cancelled=0 ORDER BY axis,id',(source,)).fetchall()

def start(c,u,e,csrf,r):
 from app import h,layout,redirect,fail,select,form,check
 from axis_self import AXES
 if u['id']!=e['user']:fail('Không có quyền khởi tạo hồ sơ.',403)
 if e['locked'] or e['status'] not in ('draft','returned') or initialized(c,e):
  return redirect('/eval/'+str(e['id']))
 srcs=sources(c,e)
 body='<section class="panel period-start"><h2>KHỞI TẠO HỒ SƠ '+h(label(e)).upper()+'</h2><div class="period-start-actions">'+form('/action/period_start/'+str(e['id']),csrf,'<input type="hidden" name="mode" value="new">','Tạo hồ sơ mới')+'</div>'
 if srcs:
  try:sid=int(r.query_params.get('source',srcs[0]['id']))
  except ValueError:fail('Kỳ nguồn không hợp lệ.')
  if sid not in {p['id'] for p in srcs}:fail('Kỳ nguồn không hợp lệ.',403)
  body+='<h3>Kế thừa công việc từ kỳ đánh giá trước</h3><form method="get" class="period-year" action="/my-period/'+str(e['id'])+'">'+select('Kỳ lấy dữ liệu','source',[(p['id'],label(p)) for p in srcs],sid)+'<button class="secondary">Xem</button></form>'
  tasks=source_tasks(c,sid)
  fields='<input type="hidden" name="mode" value="copy"><input type="hidden" name="source" value="'+str(sid)+'"><p class="muted">Chỉ kế thừa thông tin nhiệm vụ. Thời hạn chuyển sang quý mới; kết quả, minh chứng, điểm và phê duyệt phải nhập lại.</p>'
  for axis in range(1,7):
   rows=[t for t in tasks if t['axis']==axis]
   if rows:
    fields+='<section class="period-copy-axis"><h4>TRỤC '+str(axis)+' · '+h(AXES[axis][0])+'</h4>'
    for t in rows:fields+=check(t['title'],'task_'+str(t['id']),True)
    fields+='</section>'
  fields+=check('Xác nhận công việc được chọn tiếp tục phù hợp với quý mới.','confirmed')
  body+=form('/action/period_start/'+str(e['id']),csrf,fields,'Kế thừa công việc')
 body+='<p><a href="/my-periods">← Chọn kỳ khác</a></p></section>'
 return layout('Khởi tạo hồ sơ',body,u,csrf,compact=True)

def apply(c,u,f,eid):
 from app import get_eval,own_edit,fail,required,integer,redirect,DEMO
 e=get_eval(c,u,eid);own_edit(u,e)
 if initialized(c,e):fail('Hồ sơ đã khởi tạo. Không ghi đè dữ liệu hiện có.',409)
 mode=required(f,'mode')
 if mode not in ('new','copy'):fail('Lựa chọn không hợp lệ.')
 if mode=='copy':
  if not f.get('confirmed'):fail('Cần xác nhận công việc phù hợp quý mới.')
  sid=integer(f,'source',1,10**9)
  if sid not in {p['id'] for p in sources(c,e)}:fail('Không có quyền kế thừa kỳ này.',403)
  rows=source_tasks(c,sid);valid={t['id'] for t in rows}
  wanted={int(k[5:]) for k in f.keys() if k.startswith('task_') and k[5:].isdigit() and f.get(k)}
  if not wanted:fail('Chưa chọn công việc.')
  if not wanted<=valid:fail('Công việc không thuộc hồ sơ nguồn.',403)
  if DEMO and c.execute('SELECT count(*) FROM tasks').fetchone()[0]+len(wanted)>400:fail('Demo giới hạn 400 nhiệm vụ.')
  cutoff=end_of_quarter(e['year'],e['quarter']).isoformat()
  for t in rows:
   if t['id'] not in wanted:continue
   tid=c.execute('INSERT INTO tasks(evaluation,title,source,axis,grp,product,qty,due) VALUES(?,?,?,?,?,?,?,?)',(eid,t['title'],t['source'],t['axis'],t['grp'],t['product'],t['qty'],cutoff)).lastrowid
   audit(c,u['id'],'Tự khai nhiệm vụ',eid,str(tid));audit(c,u['id'],'Kế thừa công việc',eid,t['title'])
  audit(c,u['id'],MARK,eid,'Kế thừa '+str(len(wanted))+' công việc từ hồ sơ '+str(sid))
  return redirect('/eval/'+str(eid)+'?axis=1')
 audit(c,u['id'],MARK,eid,'Tạo hồ sơ mới')
 return redirect('/eval/'+str(eid))
