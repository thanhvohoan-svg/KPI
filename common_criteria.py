"""Quarter-specific common criteria and per-record snapshots."""
import json, hashlib, math
from pathlib import Path
from html import escape
DEFAULT=json.loads((Path(__file__).parent/'common_templates.json').read_text(encoding='utf-8'))
NAMES={'2':'Cá nhân giữ chức vụ lãnh đạo, quản lý','3':'Cá nhân không giữ chức vụ lãnh đạo, quản lý'}
SUB={'2':{'3.a':'Năng lực lãnh đạo, quản lý','3.b':'Năng lực chuyên môn, nghiệp vụ theo vị trí việc làm','3.c':'Khả năng đáp ứng yêu cầu thực thi nhiệm vụ được giao','3.d':'Thái độ công tác trong thực hiện nhiệm vụ','3.đ':'Tinh thần đổi mới sáng tạo, dám nghĩ, dám làm, dám chịu trách nhiệm vì lợi ích chung'},'3':{'2.a':'Năng lực chuyên môn, nghiệp vụ theo yêu cầu của vị trí việc làm','2.b':'Khả năng đáp ứng yêu cầu thực thi nhiệm vụ được giao','2.c':'Thái độ công tác trong thực hiện nhiệm vụ','2.d':'Tinh thần đổi mới sáng tạo, dám nghĩ, dám làm, dám chịu trách nhiệm vì lợi ích chung'}}
def setup(c):
 c.execute('CREATE TABLE IF NOT EXISTS common_templates(period INTEGER REFERENCES periods(id), appendix TEXT, data TEXT NOT NULL, PRIMARY KEY(period,appendix))')
 c.execute('CREATE TABLE IF NOT EXISTS common_assignment(evaluation INTEGER PRIMARY KEY REFERENCES evaluations(id), appendix TEXT NOT NULL)')
 c.execute('CREATE TABLE IF NOT EXISTS common_scores(evaluation INTEGER PRIMARY KEY REFERENCES evaluations(id), appendix TEXT NOT NULL, template TEXT NOT NULL, scores TEXT NOT NULL)')
def read(c,e):
 setup(c)
 return c.execute('SELECT * FROM common_scores WHERE evaluation=?',(e['id'],)).fetchone()
def appendix(c,e):
 row=c.execute('SELECT appendix FROM common_assignment WHERE evaluation=?',(e['id'],)).fetchone()
 if row:return row['appendix']
 role=c.execute('SELECT role FROM users WHERE id=?',(e['user'],)).fetchone()['role']
 return '2' if role in ('leader','manager','admin') else '3'
def template(c,pid,k):
 row=c.execute('SELECT data FROM common_templates WHERE period=? AND appendix=?',(pid,k)).fetchone()
 return json.loads(row['data']) if row else DEFAULT[k]
def pack(data):
 return json.dumps(data,ensure_ascii=False,separators=(',',':'))
def token(k,data):
 return hashlib.sha256((k+pack(data)).encode()).hexdigest()
def get(c,e):
 row=read(c,e)
 if row:return row['appendix'],json.loads(row['template']),json.loads(row['scores'])
 k=appendix(c,e)
 return k,template(c,e['period'],k),{}
def leaves(data):
 return [r for _,rows in data for r in rows]
def points(rows):return sum(r[2] for r in rows)
def edit_panel(c,e,csrf,editable):
 from app import h,form
 row=read(c,e)
 if not editable and not row:
  return '<section class="panel"><h2>PHẦN I. TIÊU CHÍ CHUNG (30 ĐIỂM)</h2><p>Hồ sơ cũ chỉ có điểm tổng: '+h(e['common'] if e['common'] is not None else 'Chưa chấm')+'. Không tự tạo điểm chi tiết cho hồ sơ đã nộp.</p></section>'
 k,data,scores=get(c,e)
 total=sum(v for v in scores.values() if v is not None)
 out='<section class="panel common-panel"><h2>PHẦN I. TIÊU CHÍ CHUNG (30 ĐIỂM)</h2><h3>PHỤ LỤC '+k+' – '+h(NAMES[k])+'</h3><p class="muted">Điểm chuẩn 30 · Điểm tự chấm đã lưu: '+h(round(total,2))+'/30 · '+str(len(scores))+'/'+str(len(leaves(data)))+' tiêu chí</p>'
 if editable and not row and e['common'] is not None:out+='<p class="alert">Điểm tổng cũ chưa phải phiếu chi tiết. Hãy chấm lại từng tiêu chí trước khi nộp.</p>'
 fields='<input type="hidden" name="template_token" value="'+token(k,data)+'">'
 for i,(group,rows) in enumerate(data):
  subtotal=sum(scores.get(x[0],0) for x in rows)
  fields+='<details class="common-group"'+(' open' if i==0 else '')+'><summary><b>'+h(group)+'</b><span>'+h(round(subtotal,2))+'/'+h(points(rows))+'</span></summary><div class="tablewrap"><table><thead><tr><th>Mục</th><th>Nội dung tiêu chí</th><th>Điểm chuẩn</th><th>Tự chấm</th></tr></thead><tbody>'
  last=''
  for key,desc,maximum in rows:
   prefix=key.rsplit('.',1)[0] if key.count('.')==2 else ''
   if prefix!=last and prefix in SUB[k]:
    fields+='<tr class="common-subgroup"><th colspan="4">'+h(prefix+' · '+SUB[k][prefix])+'</th></tr>'
   last=prefix
   val=scores.get(key,'')
   cell=('<input aria-label="Điểm '+h(key)+'" type="number" name="score_'+h(key)+'" min="0" max="'+h(maximum)+'" step="0.01" value="'+h(val)+'" data-common-score required>') if editable else h(val if val!='' else '—')
   fields+='<tr><td>'+h(key)+'</td><td>'+h(desc)+'</td><td>'+h(maximum)+'</td><td>'+cell+'</td></tr>'
  fields+='</tbody></table></div></details>'
 if editable:
  fields+='<p class="common-live">Tổng điểm đang nhập: <strong data-common-total>'+h(round(total,2))+'</strong>/30</p>'
  out+=form('/action/common_detail/'+str(e['id']),csrf,fields,'Lưu tiêu chí chung',extra='data-common-form')+'<script src="/static/common.js?v=22" defer></script>'
 else:out+=fields
 return out+'</section>'
def save(c,u,e,f):
 from app import own_edit,number,fail,audit
 own_edit(u,e);k,data,old=get(c,e)
 if f.get('template_token')!=token(k,data):fail('Bộ tiêu chí đã thay đổi. Vui lòng tải lại trang.')
 scores={key:number(f,'score_'+key,0,maximum) for key,_,maximum in leaves(data)}
 total=round(sum(scores.values()),2)
 c.execute('INSERT INTO common_scores(evaluation,appendix,template,scores) VALUES(?,?,?,?) ON CONFLICT(evaluation) DO UPDATE SET scores=excluded.scores',(e['id'],k,pack(data),pack(scores)))
 c.execute('UPDATE evaluations SET common=? WHERE id=?',(total,e['id']))
 audit(c,u['id'],'Lưu phiếu tiêu chí chung',e['id'],'Phụ lục '+k+' · '+str(total)+'/30')
def encode(data):
 return '\n'.join(group+' | '+key+' | '+str(m)+' | '+desc for group,rows in data for key,desc,m in rows)
def parse(value):
 groups={};seen=set()
 for line in value.splitlines():
  if not line.strip():continue
  a=line.split('|',3)
  if len(a)!=4:raise ValueError('Mỗi dòng cần 4 cột, phân cách bằng dấu |.')
  group,key,score,desc=[x.strip() for x in a]
  try:m=float(score.replace(',','.'))
  except ValueError:raise ValueError('Điểm chuẩn không hợp lệ.')
  if not group or not key or not desc or key in seen or not math.isfinite(m) or not 0<m<=30 or abs(m-round(m,2))>1e-9:raise ValueError('Thiếu nội dung, trùng mã hoặc điểm không hợp lệ.')
  if len(group)>1000 or len(key)>50 or len(desc)>4000:raise ValueError('Nội dung quá dài.')
  seen.add(key);groups.setdefault(group,[]).append([key,desc,round(m,2)])
 data=[[g,r] for g,r in groups.items()]
 if not 1<=len(seen)<=150 or abs(points(leaves(data))-30)>1e-8:raise ValueError('Tổng điểm chuẩn phải đúng 30 và tối đa 150 tiêu chí.')
 return data
def frozen(c,pid,k):
 return c.execute('SELECT 1 FROM common_scores s JOIN evaluations e ON e.id=s.evaluation WHERE e.period=? AND s.appendix=? LIMIT 1',(pid,k)).fetchone() is not None
def admin_panel(c,p,csrf):
 from app import h,form,textarea,select,check
 setup(c);pid=p['id'];out='<section class="panel"><h2>QUẢN LÝ TIÊU CHÍ CHUNG THEO QUÝ</h2><p>Chỉnh bộ tiêu chí trước khi giáo viên lưu phiếu. Tổng điểm chuẩn luôn là 30. Hồ sơ đã lưu giữ nguyên mẫu của kỳ.</p>'
 for k in ('2','3'):
  data=template(c,pid,k)
  out+='<details><summary><b>PHỤ LỤC '+k+' – '+h(NAMES[k])+'</b><span>30 điểm</span></summary>'
  if p['locked'] or frozen(c,pid,k):out+='<p>Đã khóa mẫu vì có hồ sơ đã chấm hoặc kỳ đã khóa.</p>'
  else:
   fields='<input type="hidden" name="appendix" value="'+k+'"><p>Mỗi dòng: Tên nhóm | Mã tiêu chí | Điểm chuẩn | Nội dung. Có thể thêm, sửa hoặc xóa dòng.</p>'+textarea('Nội dung bộ tiêu chí','data',encode(data),attrs='rows="18" required')+check('Xác nhận bộ tiêu chí đã được kiểm tra và áp dụng cho quý','confirmed')
   out+=form('/action/common_template/'+str(pid),csrf,fields,'Lưu bộ tiêu chí')
   previous=c.execute('SELECT id,year,quarter FROM periods WHERE year<? OR (year=? AND quarter<?) ORDER BY year DESC,quarter DESC',(p['year'],p['year'],p['quarter'])).fetchall()
   if previous:out+=form('/action/common_copy/'+str(pid),csrf,'<input type="hidden" name="appendix" value="'+k+'">'+select('Sao chép từ quý', 'source',[(r['id'],str(r['quarter'])+'/'+str(r['year'])) for r in previous])+check('Xác nhận thay thế mẫu của quý đang chọn','confirmed'),'Sao chép')
  out+='</details>'
 return out+'</section>'
def assignment_panel(c,e,csrf):
 from app import form,select
 setup(c)
 if e['locked'] or e['status'] not in ('draft','returned') or read(c,e):return ''
 return '<section class="panel"><h2>Phân loại phụ lục tiêu chí chung</h2><p>BGH xác nhận đúng đối tượng theo chức vụ, không chỉ dựa vào quyền tài khoản.</p>'+form('/action/common_assign/'+str(e['id']),csrf,select('Phụ lục áp dụng','appendix',[(k,'Phụ lục '+k+' – '+v) for k,v in NAMES.items()],appendix(c,e)),'Xác nhận phụ lục')+'</section>'
def admin_action(c,u,f,action,obj):
 from app import assert_manage,period,unlocked,fail,required,integer,audit,get_eval,redirect
 assert_manage(u);setup(c);k=required(f,'appendix')
 if k not in NAMES:fail('Phụ lục không hợp lệ.')
 if action=='common_assign':
  e=get_eval(c,u,obj);unlocked(e)
  if e['status'] not in ('draft','returned') or read(c,e):fail('Hồ sơ đã chấm hoặc đã nộp, không đổi phụ lục.')
  c.execute('INSERT OR REPLACE INTO common_assignment VALUES(?,?)',(obj,k));audit(c,u['id'],'Phân loại phụ lục',obj,k);return redirect('/eval/'+str(obj))
 p=period(c,obj);unlocked(p)
 if frozen(c,obj,k):fail('Mẫu đã được sử dụng, không sửa hồi tố.')
 if not f.get('confirmed'):fail('Cần xác nhận bộ tiêu chí.')
 if action=='common_copy':
  src=period(c,integer(f,'source',1,10**9))
  if (src['year'],src['quarter'])>=(p['year'],p['quarter']):fail('Chỉ sao chép từ quý trước.')
  data=template(c,src['id'],k)
 else:
  try:data=parse(required(f,'data',200000))
  except ValueError as ex:fail(str(ex))
 c.execute('INSERT OR REPLACE INTO common_templates VALUES(?,?,?)',(obj,k,pack(data)));audit(c,u['id'],'Cập nhật bộ tiêu chí',detail=str(obj)+' / Phụ lục '+k);return redirect('/period/'+str(obj))
