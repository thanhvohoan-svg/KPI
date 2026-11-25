from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import UploadFile
from core import *
import axis_self
import workflow
import common_criteria as cc
import personal_exports as pe
import leader_ui
from school_logo import LOGO_URI
import html, json, time, io, urllib.parse, xlsxwriter
from contextlib import closing
from pathlib import Path
app=FastAPI(title='Hệ thống đánh giá KPI giáo viên',docs_url=None,redoc_url=None,openapi_url=None)
app.mount('/static',StaticFiles(directory=Path(__file__).parent/'static'),name='static')
init()
SECURE=os.environ.get('KPI_HTTPS','0')=='1'
DEMO=os.environ.get('KPI_DEMO','0')=='1'
DEMO_HINT='<section class="demo-banner"><b>HỆ THỐNG ĐÁNH GIÁ KPI · BẢN THỬ NGHIỆM</b> · Chỉ dùng dữ liệu giả lập. Mỗi trình duyệt có hồ sơ thử riêng; dữ liệu có thể mất khi Render khởi động lại. Không nhập thông tin thật.</section>' if DEMO else ''
DEMO_LOGIN='<div class="demo-accounts"><h3>Tài khoản thử nghiệm</h3><p>Giáo viên: <b>giaovien</b><br>Tổ trưởng: <b>totruong</b><br>Ban Giám hiệu: <b>bangiamhieu</b></p><p>Mật khẩu chung: <b>KpiDemo2026!</b></p><p>Đăng xuất rồi đổi vai trò trên cùng trình duyệt để tiếp tục hồ sơ. Mở cửa sổ riêng tư để bắt đầu lại.</p></div>' if DEMO else ''
def h(v): return html.escape(str(v if v is not None else ''),quote=True)
def one(c,sql,p=()): return c.execute(sql,p).fetchone()
def allrows(c,sql,p=()): return c.execute(sql,p).fetchall()
def fail(msg,status=400): raise HTTPException(status,msg)
def required(f,key,maxlen=500):
 s=str(f.get(key,'')).strip()
 if not s or len(s)>maxlen: fail('Thiếu hoặc không hợp lệ: '+key)
 return s
def optional(f,key,maxlen=2000):
 s=str(f.get(key,'')).strip()
 if len(s)>maxlen: fail('Nội dung quá dài: '+key)
 return s
def integer(f,key,lo,hi,empty=False):
 s=str(f.get(key,'')).strip()
 if empty and not s:return None
 try: n=int(s)
 except ValueError: fail('Cần nhập số nguyên: '+key)
 if not lo<=n<=hi: fail('Số ngoài phạm vi: '+key)
 return n
def number(f,key,lo=0,hi=30):
 try: v=float(f.get(key,''))
 except (ValueError,TypeError): fail('Điểm không hợp lệ')
 if not math.isfinite(v) or not lo<=v<=hi: fail('Điểm ngoài phạm vi')
 return round(v,2)
def datefield(f,key,empty=False):
 v=str(f.get(key,'')).strip()
 if not v and empty:return None
 try: d=dt.date.fromisoformat(v)
 except ValueError: fail('Ngày không hợp lệ: '+key)
 if d.year<2000 or d.year>2100:fail('Ngày ngoài phạm vi')
 return d.isoformat()
def redirect(url): return RedirectResponse(url,status_code=303)
def field(label,name,value='',kind='text',attrs=''):
 return f'<label>{h(label)}<input name="{name}" type="{kind}" value="{h(value)}" {attrs}></label>'
def textarea(label,name,value='',attrs=''): return f'<label>{h(label)}<textarea name="{name}" {attrs}>{h(value)}</textarea></label>'
def select(label,name,options,value=None,attrs=''):
 return f'<label>{h(label)}<select name="{name}" {attrs}>'+''.join(f'<option value="{h(k)}"'+(' selected' if str(k)==str(value) else '')+f'>{h(v)}</option>' for k,v in options)+'</select></label>'
def check(label,name,value=False): return f'<label class="check"><input type="checkbox" name="{name}" value="1"'+(' checked' if value else '')+f'> {h(label)}</label>'
def form(url,csrf,body,button='Lưu',extra=''):
 return f'<form method="post" action="{url}" {extra}><input type="hidden" name="csrf" value="{h(csrf)}">{body}<button>{h(button)}</button></form>'
def layout(title,body,u=None,csrf='',nav=True,compact=False):
 links=''
 if u and nav:
  links=('' if u['role']=='teacher' else '<a href="/">Quản lý tổ</a>' if u['role'] in ('leader','deputy') else '<a href="/">Tổng quan</a>')+('' if DEMO else '<a href="/password">Đổi mật khẩu</a>')
  if u['role'] in ('admin','manager'): links+='<a href="/manage">Quản trị</a><a href="/audit">Nhật ký</a>'
  if can_manage(u) or u['role']=='leader': links+='<a href="/assign">Giao nhiệm vụ</a>'
  links+='<div class="header-account"><strong>'+h(u['name'])+'</strong>'+form('/logout',csrf,'','Đăng xuất')+'</div>'
 heading='' if compact else f'<div class="heading"><div><p class="eyebrow">HỆ THỐNG ĐÁNH GIÁ HẰNG QUÝ</p><h1>{h(title)}</h1></div></div>'
 main_class=' class="personal-main"' if compact else ''
 return HTMLResponse(f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{h(title)} · THPT chuyên Trần Hưng Đạo - Lâm Đồng</title><link rel="stylesheet" href="/static/style.css?v=27"></head><body><header><a class="brand school-brand" href="/"><img class="school-logo" src="{LOGO_URI}" alt="Logo Trường THPT chuyên Trần Hưng Đạo" width="80" height="80"><div class="school-brand-text"><strong>TRƯỜNG THPT CHUYÊN TRẦN HƯNG ĐẠO - LÂM ĐỒNG</strong><em>Hệ thống đánh giá KPI giáo viên</em></div></a><nav>{links}</nav></header><main{main_class}>{heading}{DEMO_HINT}{body}<footer>TRƯỜNG THPT CHUYÊN TRẦN HƯNG ĐẠO - LÂM ĐỒNG · {"ONLINE DEMO – dữ liệu giả lập" if DEMO else "Dữ liệu nội bộ nhà trường"} · Phiên bản 2.7</footer></main></body></html>')
def auth(c,r):
 tok=r.cookies.get('kpi_session',''); row=one(c,'SELECT * FROM sessions WHERE token=? AND expires>?',(token_hash(tok),int(time.time()))) if tok else None
 u=one(c,'SELECT * FROM users WHERE id=? AND active=1',(row['user'],)) if row and row['user'] else None
 return u,row
def issue(c,user=None):
 token=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(32); c.execute('DELETE FROM sessions WHERE expires<?',(int(time.time()),)); c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(token_hash(token),user,csrf,int(time.time())+43200)); return token,csrf
def cookie(res,token): res.set_cookie('kpi_session',token,httponly=True,secure=SECURE,samesite='lax',max_age=43200,path='/'); return res
def can_manage(u):return u['role'] in ('admin','manager')
def assert_manage(u):
 if not can_manage(u):fail('Không có quyền quản trị.',403)
def viewable(u,e):return u['id']==e['user'] or can_manage(u) or (u['role'] in ('leader','deputy') and u['department'] is not None and u['department']==e['department'])
def team_review(u,e):return u['id']!=e['user'] and u['role']=='leader' and u['department'] is not None and u['department']==e['department']
def get_eval(c,u,eid):
 e=one(c,'''SELECT e.*,p.year,p.quarter,p.mode,p.locked,u.name,u.code,u.subject,d.name dept FROM evaluations e JOIN periods p ON p.id=e.period JOIN users u ON u.id=e.user LEFT JOIN departments d ON d.id=e.department WHERE e.id=?''',(eid,))
 if not e or not viewable(u,e):fail('Không có quyền xem hồ sơ.',403)
 return e
def period(c,pid):
 p=one(c,'SELECT * FROM periods WHERE id=?',(pid,))
 if not p:fail('Không tìm thấy kỳ',404)
 return p
def unlocked(e):
 if e['locked']:fail('Kỳ đánh giá đã khóa.',409)
def own_edit(u,e):
 unlocked(e)
 if u['id']!=e['user'] or e['status'] not in ('draft','returned'):fail('Hồ sơ không thể chỉnh sửa.',403)
def result(c,e):
 t=allrows(c,'SELECT * FROM tasks WHERE evaluation=? ORDER BY axis,id',(e['id'],)); hol=[r['day'] for r in allrows(c,'SELECT day FROM holidays WHERE period=?',(e['period'],))]; return calculate(t,e['mode'],hol,end_of_quarter(e['year'],e['quarter']).isoformat())
def workflow_panel(c,e,connected=False):
 has_team=e['department'] is not None and one(c,"SELECT id FROM users WHERE active=1 AND role='leader' AND department=? AND id<>? LIMIT 1",(e['department'],e['user'])) is not None
 return workflow.render(e['status'],has_team,e['team_common'] is not None,bool(e['locked']),connected)
def shown_common(e):return e['final_common'] if e['final_common'] is not None else e['team_common'] if e['team_common'] is not None else e['common']
def group_quota(c,e):
 q=one(c,'SELECT SUM(final_level=?) good,SUM(final_level=?) xs FROM evaluations WHERE period=? AND department IS ? AND cohort=? AND status="approved" AND id<>?',(LEVELS[1],LEVELS[0],e['period'],e['department'],e['cohort'],e['id'])); return int(q['good'] or 0),int(q['xs'] or 0)
def scope_evals(c,u,pid):
 sql='SELECT e.*,u.name,u.code,d.name dept,p.year,p.quarter,p.mode,p.locked FROM evaluations e JOIN users u ON u.id=e.user JOIN periods p ON p.id=e.period LEFT JOIN departments d ON d.id=e.department WHERE e.period=?'; args=[pid]
 if not can_manage(u):
  if u['role'] in ('leader','deputy') and u['department'] is not None:sql+=' AND (e.department=? OR e.user=?)';args.extend([u['department'],u['id']])
  else:sql+=' AND e.user=?';args.append(u['id'])
 return allrows(c,sql+' ORDER BY d.name,u.name',args)
def table(headers,rows):return '<div class="tablewrap"><table><thead><tr>'+''.join('<th>'+h(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def stat(label,v):return f'<div class="stat"><small>{h(label)}</small><strong>{h(v)}</strong></div>'
def error_page(msg,status=400):
 res=layout('Không thể thực hiện',f'<section class="panel"><p>{h(msg)}</p><a class="btn" href="/">Về trang chính</a></section>');res.status_code=status;return res
@app.exception_handler(HTTPException)
async def error_handler(r,e):return error_page(e.detail,e.status_code)
@app.middleware('http')
async def security(r,call_next):
 if int(r.headers.get('content-length','0') or 0)>6*1024*1024:return error_page('Tệp quá lớn (tối đa 5 MB).',413)
 res=await call_next(r);res.headers['X-Content-Type-Options']='nosniff';res.headers['X-Frame-Options']='DENY';res.headers['Referrer-Policy']='no-referrer';res.headers['Content-Security-Policy']="default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; form-action 'self'; base-uri 'none'";res.headers['Cache-Control']='no-store';return res
@app.get('/login')
def login_get(r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if u:return redirect('/')
  if s:csrf=s['csrf']; tok=None
  else:tok,csrf=issue(c);c.commit()
  res=layout('Đăng nhập', '<section class="panel login"><h2>Hệ thống đánh giá KPI giáo viên</h2><p>'+('Chọn tài khoản mẫu ở bên dưới.' if DEMO else 'Nhập họ tên đầy đủ. Mật khẩu lần đầu là số điện thoại.')+'</p>'+form('/login',csrf,field('Họ và tên','name',attrs='required autocomplete="username"')+field('Mật khẩu','password',kind='password',attrs='required autocomplete="current-password"'),'Đăng nhập')+DEMO_LOGIN+'</section>')
  return cookie(res,tok) if tok else res
@app.post('/login')
async def login_post(r:Request):
 f=await r.form(); now=int(time.time())
 with closing(connect()) as c, c:
  u,s=auth(c,r)
  if not s or not hmac.compare_digest(str(f.get('csrf','')),s['csrf']):fail('Phiên hết hạn. Mở lại trang đăng nhập.',403)
  name=normalize(str(f.get('name',''))[:200]); password=str(f.get('password',''))[:200]; key=token_hash((r.client.host if r.client else '')+'|'+name); ipkey=token_hash((r.client.host if r.client else '')+'|*'); attempt=one(c,'SELECT * FROM attempts WHERE key=?',(key,)); ipattempt=one(c,'SELECT * FROM attempts WHERE key=?',(ipkey,))
  if any(a and a['until']>now and a['count']>=limit for a,limit in [(attempt,5),(ipattempt,50)]):return error_page('Thử đăng nhập quá nhiều. Thử lại sau 15 phút.',429)
  u=one(c,'SELECT * FROM users WHERE login=? AND active=1',(name,)); valid=check_password(password,u['password']) if u else check_password(password,'00'*16+'$'+'00'*32)
  if not u or not valid:
   for k,a in [(key,attempt),(ipkey,ipattempt)]:c.execute('INSERT OR REPLACE INTO attempts VALUES(?,?,?)',(k,a['count']+1 if a and a['until']>now else 1,a['until'] if a and a['until']>now else now+900))
   return layout('Đăng nhập', '<section class="panel login"><p class="alert">Tên hoặc mật khẩu không đúng.</p>'+form('/login',s['csrf'],field('Họ và tên','name',attrs='required')+field('Mật khẩu','password',kind='password',attrs='required'),'Đăng nhập')+DEMO_LOGIN+'</section>')
  c.execute('DELETE FROM sessions WHERE token=?',(s['token'],));c.execute('DELETE FROM attempts WHERE key=?',(key,));tok,csrf=issue(c,u['id']);audit(c,u['id'],'Đăng nhập');return cookie(redirect('/password' if u['must_change'] else '/'),tok)
@app.get('/')
def home(r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if not u:return redirect('/login')
  if u['must_change']:return redirect('/password')
  periods=allrows(c,'SELECT * FROM periods ORDER BY year DESC,quarter DESC'); csrf=s['csrf']
  if not periods:return layout('Tổng quan','<section class="panel">Chưa mở kỳ đánh giá. '+('<a class="btn" href="/manage">Thiết lập kỳ</a>' if can_manage(u) else 'Vui lòng liên hệ Ban Giám hiệu.')+'</section>',u,csrf)
  if u['role']=='teacher':
   personal=one(c,'SELECT e.id FROM evaluations e JOIN periods p ON p.id=e.period WHERE e.user=? ORDER BY p.locked ASC,p.year DESC,p.quarter DESC LIMIT 1',(u['id'],))
   if personal:return redirect(f'/eval/{personal["id"]}')
   return layout('Hồ sơ cá nhân','<section class="panel">Chưa có hồ sơ đánh giá. Vui lòng liên hệ Ban Giám hiệu.</section>',u,csrf,compact=True)
  default_pid=next((p['id'] for p in periods if not p['locked']),periods[0]['id']) if u['role'] in ('leader','deputy') else periods[0]['id']
  try:pid=int(r.query_params.get('period',default_pid))
  except ValueError:fail('Kỳ không hợp lệ')
  p=period(c,pid); es=scope_evals(c,u,pid); role_cards=''; view=r.query_params.get('view','team')
  if u['role'] in ('leader','deputy'):return leader_ui.dashboard(c,u,p,periods,es,csrf,r)
  rows=[]; submitted=sum(e['status'] not in ('draft','returned') for e in es); approved=sum(e['status']=='approved' for e in es)
  for e in es:
   calc=result(c,e); common=shown_common(e); rows.append([h(e['name']),h(e['dept'] or 'Chưa phân tổ'),h(STATUSES[e['status']]),f"{calc['kpi']:.2f}" if calc['n'] else '—',f'{common+calc["kpi"]:.2f}' if common is not None and calc['n'] else '—',h(e['final_level'] or '—'),f'<a class="btn small" href="/eval/{e["id"]}">Mở hồ sơ</a>'])
  chooser='<form method="get" class="inline">'+(f'<input type="hidden" name="view" value="{view}">' if u['role'] in ('leader','deputy') else '')+select('Kỳ đánh giá','period',[(x['id'],f'Quý {x["quarter"]}/{x["year"]}'+(' · đã khóa' if x['locked'] else '')) for x in periods],pid)+'<button>Xem</button></form>'
  body='<section class="panel toolbar">'+chooser+(f'<a class="btn secondary" href="/export/period/{pid}">Xuất tổng hợp Excel</a>' if u['role']!='teacher' else '')+'</section>'+role_cards+'<div class="stats">'+stat('Hồ sơ',len(es))+stat('Đã nộp',submitted)+stat('BGH đã duyệt',approved)+stat('Chưa nộp / trả lại',len(es)-submitted)+'</div><section class="panel"><h2>Danh sách hồ sơ</h2>'+table(['Họ tên','Tổ','Trạng thái','KPI /70','Tổng /100','Xếp loại',''],rows)+'</section>'
  if can_manage(u):
   grouped={}
   for e in es:
    k=(e['dept'] or 'Chưa phân tổ',e['cohort']);g=grouped.setdefault(k,[0,0,0]);g[0]+=1;g[1]+=e['status']=='approved' and e['final_level']==LEVELS[1];g[2]+=e['status']=='approved' and e['final_level']==LEVELS[0]
   body+='<section class="panel"><h2>Kiểm soát tỷ lệ xuất sắc</h2><p class="muted">Theo tổ và nhóm tương đồng; số tối đa = làm tròn 20% số HTT đã duyệt. Số chưa duyệt chưa được tính.</p>'+table(['Tổ','Nhóm','Hồ sơ','HTT','Tối đa HTXS','HTXS đã duyệt'],[[h(k[0]),h(k[1]),g[0],g[1],quota(g[1]),g[2]] for k,g in grouped.items()])+'</section>'
  return layout('Tổng quan',body,u,csrf)
@app.get('/password')
def password_get(r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if not u:return redirect('/login')
  return layout('Đổi mật khẩu','<section class="panel login"><p>'+('Bắt buộc đổi mật khẩu lần đầu.' if u['must_change'] else 'Đổi mật khẩu tài khoản.')+'</p>'+form('/password',s['csrf'],field('Mật khẩu hiện tại','old',kind='password',attrs='required')+field('Mật khẩu mới (ít nhất 10 ký tự)','new',kind='password',attrs='required minlength="10" maxlength="200"')+field('Nhập lại mật khẩu mới','confirm',kind='password',attrs='required'),'Đổi mật khẩu')+'</section>',u,s['csrf'],not u['must_change'])
@app.get('/manage')
def manage(r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if not u:return redirect('/login')
  if u['must_change']:return redirect('/password')
  assert_manage(u); csrf=s['csrf']; ds=allrows(c,'SELECT * FROM departments ORDER BY name'); ps=allrows(c,'SELECT * FROM periods ORDER BY year DESC,quarter DESC'); users=allrows(c,'SELECT u.*,d.name dept FROM users u LEFT JOIN departments d ON d.id=u.department ORDER BY u.name'); lib=allrows(c,'SELECT * FROM library ORDER BY id');
  depopts=[('', 'Chưa phân tổ')]+[(d['id'],d['name']) for d in ds]; popts=[(p['id'],f'Quý {p["quarter"]}/{p["year"]}') for p in ps if not p['locked']]
  body='<div class="twocol"><section class="panel"><h2>1 · Tổ chuyên môn</h2>'+form('/action/department',csrf,field('Tên tổ','name',attrs='required'),'Thêm tổ')+'<p>'+h(' · '.join(d['name'] for d in ds) or 'Chưa có tổ')+'</p></section><section class="panel"><h2>2 · Mở kỳ đánh giá</h2>'+form('/action/period',csrf,field('Năm','year',2026,'number','min="2000" max="2100" required')+select('Quý','quarter',[(n,n) for n in range(1,5)],3)+select('Quy tắc trọng số đã phê duyệt','mode',[('task','Theo nhiệm vụ (mục 5–6)'),('product','Theo số sản phẩm (Phụ lục II)')])+check('Đã xác nhận quy tắc và cách áp dụng tại trường','confirmed'),'Mở kỳ')+'</section></div>'
  body+='<section class="panel"><h2>3 · Kỳ đánh giá</h2>'+table(['Kỳ','Trọng số','Trạng thái','Ngày nghỉ & khóa'],[[h(f'Quý {p["quarter"]}/{p["year"]}'),h(p['mode']),h('Đã khóa' if p['locked'] else 'Đang mở'),('Đã khóa' if p['locked'] else f'<a class="btn small" href="/period/{p["id"]}">Thiết lập</a>')] for p in ps])+'</section>'
  body+='<section class="panel"><h2>4 · Quản lý tài khoản</h2><p class="muted">Phân tổ và nhóm tương đồng trước khi giao nhiệm vụ. Chỉ quản trị viên được cấp quyền quản trị/BGH.</p>'+table(['Mã','Họ tên','Môn','Tổ','Quyền',''],[[h(x['code']),h(x['name']),h(x['subject']),h(x['dept'] or 'Chưa phân tổ'),h(ROLES[x['role']]),('Cố định (demo)' if DEMO else f'<a class="btn small" href="/user/{x["id"]}">Thiết lập</a>')] for x in users if x['role']!='admin' or u['role']=='admin'])+'</section>'
  body+='<section class="panel"><h2>5 · Thư viện nhiệm vụ gợi ý</h2>'+form('/action/library',csrf,field('Tên nhiệm vụ','title',attrs='required')+select('Nhóm','grp',[(i,f'Nhóm {i}') for i in range(1,5)])+select('Trục (theo quy định trường)','axis',[(i,f'Trục {i}') for i in range(1,7)])+field('Sản phẩm dự kiến','product',attrs='required'),'Thêm nhiệm vụ')+table(['Nhiệm vụ','Nhóm','Trục','Sản phẩm'],[[h(x['title']),x['grp'],x['axis'],h(x['product'])] for x in lib])+'</section>'
  body+='<section class="panel"><h2>7 · Quản lý tiêu chí chung</h2><p>Thiết lập Phụ lục 2 và 3 theo từng quý.</p>'+''.join(f'<a class="btn secondary" href="/period/{p["id"]}#common-templates">Quý {p["quarter"]}/{p["year"]}</a> ' for p in ps if not p['locked'])+'</section>'
  if popts:body+='<section class="panel"><h2>6 · Giao nhiệm vụ hàng loạt</h2><a class="btn" href="/assign">Giao nhiệm vụ</a></section>'
  return layout('Quản trị hệ thống',body,u,csrf)
@app.get('/user/{uid}')
def user_get(uid:int,r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if not u:return redirect('/login')
  if u['must_change']:return redirect('/password')
  assert_manage(u); x=one(c,'SELECT * FROM users WHERE id=?',(uid,));
  if not x or (u['role']!='admin' and x['role'] in ('admin','manager')):fail('Không có quyền.',403)
  ds=allrows(c,'SELECT * FROM departments ORDER BY name'); roles=[(k,v) for k,v in ROLES.items() if u['role']=='admin' or k not in ('admin','manager')]; csrf=s['csrf'];body='<section class="panel"><h2>'+h(x['name'])+'</h2>'+form(f'/action/user/{uid}',csrf,select('Tổ chuyên môn','department',[('','Chưa phân tổ')]+[(d['id'],d['name']) for d in ds],x['department'])+field('Nhóm tương đồng','cohort',x['cohort'],attrs='required')+select('Vai trò','role',roles,x['role'])+check('Tài khoản hoạt động','active',x['active'])+check('Cập nhật hồ sơ nháp chưa có nhiệm vụ trong kỳ mở','sync'),'Lưu phân quyền')+'</section>'
  if uid!=u['id']:body+='<section class="panel"><h2>Đặt lại mật khẩu</h2>'+form(f'/action/reset/{uid}',csrf,field('Mật khẩu tạm (ít nhất 10 ký tự)','password',kind='password',attrs='required minlength="10"'),'Đặt lại')+'</section>'
  return layout('Thiết lập tài khoản',body,u,csrf)
@app.get('/period/{pid}')
def period_get(pid:int,r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if not u:return redirect('/login')
  if u['must_change']:return redirect('/password')
  assert_manage(u);p=period(c,pid);unlocked(p); csrf=s['csrf'];hol=allrows(c,'SELECT day FROM holidays WHERE period=? ORDER BY day',(pid,)); body='<section class="panel"><h2>Ngày nghỉ ngoài thứ Bảy và Chủ nhật</h2><p class="muted">Lịch nghỉ do nhà trường xác nhận. Không tự động suy đoán ngày nghỉ hoặc lịch làm việc thứ Bảy.</p>'+form(f'/action/holiday/{pid}',csrf,field('Ngày nghỉ','day',kind='date',attrs='required'),'Thêm ngày nghỉ')+''.join(form(f'/action/unholiday/{pid}',csrf,f'<input type="hidden" name="day" value="{h(x["day"])}"><span>{h(x["day"])}</span>','Xóa',extra='class="inline"') for x in hol)+'</section><section class="panel"><h2>Khóa kỳ</h2><p>Chỉ khóa khi toàn bộ hồ sơ đã được BGH duyệt.</p>'+form(f'/action/lock/{pid}',csrf,check('Xác nhận khóa kỳ và lưu kết quả','confirmed'),'Khóa kỳ')+'</section>';return layout(f'Quý {p["quarter"]}/{p["year"]}',body+'<div id="common-templates">'+cc.admin_panel(c,p,csrf)+'</div>',u,csrf)
@app.get('/assign')
def assign_get(r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if not u:return redirect('/login')
  if u['must_change']:return redirect('/password')
  if not can_manage(u) and u['role']!='leader':fail('Không có quyền.',403)
  ps=allrows(c,'SELECT * FROM periods WHERE locked=0 ORDER BY year DESC,quarter DESC');csrf=s['csrf']
  if not ps:return layout('Giao nhiệm vụ','<p>Chưa có kỳ mở.</p>',u,csrf)
  pid=int(r.query_params.get('period',ps[0]['id']));p=period(c,pid);unlocked(p);es=[e for e in scope_evals(c,u,pid) if e['status'] in ('draft','returned') and (can_manage(u) or team_review(u,e))];ds=allrows(c,'SELECT * FROM departments ORDER BY name');lib=allrows(c,'SELECT * FROM library ORDER BY id'); options=[('','Nhập nhiệm vụ riêng')]+[(x['id'],x['title']) for x in lib]; body='<section class="panel"><form method="get" class="inline">'+select('Kỳ','period',[(x['id'],f'Quý {x["quarter"]}/{x["year"]}') for x in ps],pid)+'<button>Chọn</button></form></section><section class="panel"><h2>Phân công nhiệm vụ</h2><p class="muted">Chọn người nhận hoặc cả tổ. Tổ trưởng chỉ giao cho tổ viên. Nhiệm vụ không được trùng cùng nội dung, căn cứ và trục.</p>'+form(f'/action/assign/{pid}',csrf,select('Nhiệm vụ mẫu','library',options)+field('Tên nhiệm vụ (nếu không chọn mẫu)','title')+field('Căn cứ giao nhiệm vụ','source',attrs='required')+select('Trục','axis',[(i,f'Trục {i}') for i in range(1,7)])+select('Nhóm','grp',[(i,f'Nhóm {i} – {50+i*50}') for i in range(1,5)])+field('Sản phẩm dự kiến','product')+field('Số lượng','qty',1,'number','min="1" max="1000000" required')+field('Hạn hoàn thành','due',end_of_quarter(p['year'],p['quarter']).isoformat(),'date','required')+select('Phân công','target',[('selected','Người được chọn'),('all','Tất cả trong phạm vi')]+[(f'd:{d["id"]}',d['name']) for d in ds])+ '<details open><summary>Chọn giáo viên</summary><div class="pick">'+''.join(check(e['name']+' · '+(e['dept'] or 'Chưa phân tổ'),f'e_{e["id"]}') for e in es)+'</div></details>','Giao nhiệm vụ')+'</section>';return layout('Giao nhiệm vụ',body,u,csrf)
def axis_editor(c,e,calc,csrf,step,add_next=False):
 eid=e['id']; grouped={i:[] for i in range(1,7)}
 for t,z in calc['rows']:grouped[t['axis']].append((t,z))
 def counts(i):
  active=[(t,z) for t,z in grouped[i] if not t['cancelled']]
  return sum(bool(z['ready'] and t['evidence'] and (not t['outstanding'] or t['outstanding_note'])) for t,z in active),len(active)
 def url(i):return f'/eval/{eid}?axis={i}'
 body='<section class="panel axis-workspace"><div class="axis-top"><h2>Phiếu tự đánh giá theo trục</h2><p class="muted">Chọn trục, nhập công việc và lưu lần lượt.</p></div><div class="axis-nav">'
 for i in range(1,7):
  n,total=counts(i);status=f'{n}/{total} đã đủ dữ liệu' if total else 'Không có nhiệm vụ'
  body+=f'<a class="axis-tab{" active" if step==i else ""}" href="{url(i)}"'+(' aria-current="step"' if step==i else '')+f'><b>TRỤC {i}</b><small>{status}</small></a>'
 body+=f'<a class="axis-tab{" active" if step==7 else ""}" href="{url(7)}"'+(' aria-current="step"' if step==7 else '')+'><b>TỔNG HỢP</b><small>Điểm chung & gửi duyệt</small></a></div>'
 if step==7:
  body+='</section>'
  rows=[]
  for i in range(1,7):
   n,total=counts(i);rows.append([f'<a href="{url(i)}">Trục {i}</a>',f'{n}/{total}' if total else 'Không có nhiệm vụ',f'{sum(z["kpi"] for t,z in grouped[i]):.2f}',f'{sum(z["max"] for t,z in grouped[i]):.2f}'])
  common=e['common'] if cc.read(c,e) else None
  body+='<div class="stats summary-scores">'+stat('Tiêu chí chung /30',common if common is not None else '—')+stat('KPI /70',f'{calc["kpi"]:.2f}')+stat('Tổng /100',f'{common+calc["kpi"]:.2f}' if common is not None else '—')+'</div>'
  body+='<section class="panel"><h2>Tổng hợp và gửi duyệt</h2>'+table(['Trục','Đủ dữ liệu','KPI đạt','KPI tối đa'],rows)+'</section>'
  body+='<section class="panel"><h2>Tiêu chí chung (30 điểm)</h2><p>Điểm đã lưu: '+h(e['common'] if cc.read(c,e) else 'Chưa chấm chi tiết')+'</p><a class="btn secondary" href="/eval/'+str(eid)+'?part=common">Mở phiếu tiêu chí chung</a></section>'
  ready=calc['ready'] and cc.read(c,e) is not None and e['common'] is not None and e['department'] is not None and all(counts(i)[0]==counts(i)[1] for i in range(1,7))
  body+='<section class="panel"><h2>Gửi hồ sơ đánh giá</h2><p>Đề xuất sơ bộ: '+h(suggestion(calc,e['common']))+'</p>'
  if ready:body+=form(f'/action/submit/{eid}',csrf,check('Xác nhận thông tin và minh chứng đúng thực tế','confirmed'),'Gửi duyệt')
  else:body+='<p class="alert">Chưa đủ nhiệm vụ, kết quả, minh chứng, điểm chung hoặc thông tin tổ. Hãy quay lại các trục cần bổ sung.</p>'
  return body+f'<a class="btn secondary" href="{url(6)}">← Trục trước</a></section><section class="panel"><h2>XUẤT EXCEL HỒ SƠ ĐÁNH GIÁ</h2><p class="muted">Xuất dữ liệu đã lưu; bản nháp vẫn có thể tải xuống để kiểm tra.</p>'+pe.export_buttons(eid)+'</section>'
 n,total=counts(step);body+=f'<div class="axis-content" data-axis="{step}">'+axis_self.intro(step)
 body+=f'<div class="axis-progress"><span><b>{n}/{total}</b> công việc đủ dữ liệu</span><span>KPI trục: <b>{sum(z["kpi"] for t,z in grouped[step]):.2f}/{sum(z["max"] for t,z in grouped[step]):.2f}</b></span></div><div class="axis-task-list">'
 if grouped[step]:body+='<h3>Công việc đã lưu</h3>'
 for i,(t,z) in enumerate(grouped[step],1):
  tid=t['id'];ready=bool(z['ready'] and t['evidence'] and (not t['outstanding'] or t['outstanding_note']))
  status='Đã dừng' if t['cancelled'] else 'Đã lưu đủ dữ liệu' if ready else 'Cần bổ sung'
  body+=f'<details class="task work-card" name="axis-work"><summary><span class="work-name"><b>Công việc {i}: {h(t["title"])}</b><small>{status} · {h(t["done"] if t["done"] is not None else "—")}/{t["qty"]} · KPI {z["kpi"]:.2f}/{z["max"]:.2f}</small></span><span class="work-open">Mở / sửa</span></summary>'
  if t['cancelled']:body+='<p class="alert">Dừng hợp lệ: '+h(t['cancel_reason'])+'</p>'
  else:
   body+=f'<p>{h(t["source"])} · Sản phẩm: {h(t["product"])} · SL giao: {t["qty"]} · Hạn: {h(t["effective_due"] or t["due"])} · Nhóm {t["grp"]}</p>'
   fields='<div class="formgrid">'+field('Số lượng hoàn thành','done',t['done'],'number','min="0" max="1000000" required')+field('Số lần sửa do lỗi chủ quan','corrections',t['corrections'],'number','min="0" max="1000000" required')+field('Ngày hoàn thành thực tế','finish',t['finish'],'date')+'</div>'+textarea('Minh chứng (số văn bản, ngày, đường dẫn; nếu có tệp ghi mô tả)','evidence',t['evidence'])+check('Đề xuất vượt yêu cầu','outstanding',t['outstanding'])+textarea('Mô tả kết quả nổi trội và tác động','outstanding_note',t['outstanding_note'])
   body+=form(f'/action/task/{tid}',csrf,fields,'Lưu và thu gọn công việc',extra='data-work-form')
   body+=f'<p class="scoreline">Điểm đã lưu: A {z["a"]:.2f} · B {z["b"]:.2f} · C {z["c"]:.2f} · KPI {z["kpi"]:.2f}/{z["max"]:.2f}</p>'
   attachments=allrows(c,'SELECT id,filename FROM attachments WHERE task=?',(tid,))
   body+='<details><summary>Đính kèm minh chứng</summary>'+form(f'/action/upload/{tid}',csrf,field('Tệp TXT mẫu (tối đa 100 KB)' if DEMO else 'Tệp minh chứng (tối đa 5 MB)','file',kind='file',attrs='required accept=".txt"' if DEMO else 'required accept=".pdf,.docx,.xlsx,.png,.jpg,.jpeg,.txt"'),'Đính kèm',extra='enctype="multipart/form-data" data-work-form')
   if attachments:body+='<p>Tệp: '+' · '.join(f'<a href="/attachment/{a["id"]}">{h(a["filename"])}</a>' for a in attachments)+'</p>'
   body+='</details>'+axis_self.manage_panel(c,e,t,csrf)
  body+='</details>'
 body+='</div>'
 body+=axis_self.add_panel(c,e,csrf,step,len(grouped[step]),add_next)
 body+='<div class="axis-finish"><p class="muted">Đã nhập hết công việc của trục? Chọn hoàn thành để chuyển tiếp.</p><div class="axis-actions">'
 if step>1:body+=f'<a class="btn secondary" href="{url(step-1)}">← Trục trước</a>'
 body+=form(f'/action/axis_next/{eid}',csrf,f'<input type="hidden" name="axis" value="{step}">',('Hoàn thành trục · sang trục '+str(step+1)+' →') if step<6 else 'Hoàn thành trục · tổng hợp →')+'</div></div></div></section>'
 body+='<script src="/static/axis.js?v=15" defer></script>'
 return body

@app.get('/eval/{eid}')
def eval_get(eid:int,r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if not u:return redirect('/login')
  if u['must_change']:return redirect('/password')
  e=get_eval(c,u,eid); csrf=s['csrf']; calc=result(c,e); common=shown_common(e); editable=u['id']==e['user'] and not e['locked'] and e['status'] in ('draft','returned');review=not e['locked'] and (team_review(u,e) or (can_manage(u) and u['id']!=e['user'])); body=f'<section class="panel toolbar"><div><h2>{h(e["name"])} · Quý {e["quarter"]}/{e["year"]}</h2><p>{h(e["dept"] or "Chưa phân tổ")} · {h(STATUSES[e["status"]])} · {"Đã khóa" if e["locked"] else "Đang mở"}</p></div>{pe.export_buttons(eid)}</section><div class="stats">'+stat('Tiêu chí chung /30',common if common is not None else '—')+stat('KPI /70',f'{calc["kpi"]:.2f}')+stat('Tổng /100',f'{common+calc["kpi"]:.2f}' if common is not None else '—')+stat('Vượt yêu cầu',f'{calc["outstanding"]}/{calc["n"]}')+'</div>'
  personal=u['id']==e['user']
  leader_view=u['role'] in ('leader','deputy')
  member_view=leader_view and not personal
  leader_active=member_view and review and e['status']=='submitted' and team_review(u,e)
  if personal:
   if editable:body='<div class="personal-flow-frame">'+workflow_panel(c,e,True)+'<div class="personal-flow-content" aria-label="Phiếu tự đánh giá">'
   else:body=workflow_panel(c,e)
   if not editable:body+='<section class="panel">'+pe.export_buttons(eid)+'</section>'
  elif member_view:
   body=leader_ui.member_header(e,calc,common)
   if leader_active:body+='<div class="personal-flow-frame team-flow-frame">'+workflow_panel(c,e,True)+'<div class="personal-flow-content" aria-label="Tổ trưởng đánh giá hồ sơ">'
   else:body+=workflow_panel(c,e)
   body+=leader_ui.score_panel(c,e,calc)
  else:body+=workflow_panel(c,e)
  if leader_view:body=leader_ui.tabs_for_eval(c,u,e,'self' if personal else 'team')+body
  if e['note']:body+='<p class="alert">Nhận xét: '+h(e['note'])+'</p>'
  if can_manage(u):body+=cc.assignment_panel(c,e,csrf)
  if editable:
   part=r.query_params.get('part','kpi' if 'axis' in r.query_params else 'common')
   if part not in ('common','kpi'):part='common'
   raw=r.query_params.get('axis','1');step=int(raw) if raw in ('1','2','3','4','5','6','7') else 1
   body+='<section class="panel role-cards evaluation-parts">'+workflow.dashboard_card(f'/eval/{eid}?part=common','PHẦN I. TIÊU CHÍ CHUNG','30 điểm','file',part=='common')+workflow.dashboard_card(f'/eval/{eid}?axis=1','PHẦN II. KPI','70 điểm · 6 trục','team',part=='kpi' and step!=7)+workflow.dashboard_card(f'/eval/{eid}?axis=7','TỔNG HỢP','100 điểm · Gửi hồ sơ','check',part=='kpi' and step==7)+'</section>'
   if part=='common':body+=cc.edit_panel(c,e,csrf,True)+f'<a class="btn" href="/eval/{eid}?axis=1">Chuyển sang phần KPI →</a>'
   else:body+=axis_editor(c,e,calc,csrf,step,r.query_params.get('add')=='1')
  else:
   body+=cc.edit_panel(c,e,csrf,False)
   if editable:body+='<section class="panel"><h2>Điểm tiêu chí chung</h2>'+form(f'/action/common/{eid}',csrf,field('Điểm tự chấm theo biểu mẫu có thẩm quyền','common',e['common'],'number','min="0" max="30" step="0.01" required'),'Lưu điểm')+'</section>'
   body+='<section class="panel"><h2>'+('PHẦN II. KPI – 70 ĐIỂM' if member_view else 'Nhiệm vụ được giao')+'</h2><p class="muted">Điểm được tính theo quy tắc kỳ: '+h(e['mode'])+'. Nhiệm vụ chưa hoàn thành áp dụng giới hạn chất lượng/tiến độ thận trọng; xem hướng dẫn sử dụng.</p>'
   last_axis=None
   if not calc['rows']:body+='<p>Chưa có nhiệm vụ được giao. Liên hệ tổ trưởng hoặc BGH.</p>'
   for t,z in calc['rows']:
    if member_view and t['axis']!=last_axis:
     if last_axis is not None:body+='</div></details>'
     last_axis=t['axis'];axis_tasks=[(a,b) for a,b in calc['rows'] if a['axis']==last_axis]
     body+=f'<details class="team-axis"><summary><b>TRỤC {last_axis} · {h(axis_self.AXES[last_axis][0])}</b><span>{len(axis_tasks)} công việc · {sum(b["kpi"] for a,b in axis_tasks):.2f}/{sum(b["max"] for a,b in axis_tasks):.2f} điểm</span></summary><div class="team-axis-content">'
    tid=t['id']; attachments=allrows(c,'SELECT id,filename FROM attachments WHERE task=?',(tid,)); body+=f'<details class="task"'+('' if member_view else ' open')+f'><summary><b>{h(t["title"])}</b><span>Trục {t["axis"]} · Nhóm {t["grp"]} · {z["actual"]:.2f}/{z["base"]:.0f} điểm</span></summary><p>{h(t["source"])} · Sản phẩm: {h(t["product"])} · SL giao: {t["qty"]} · Hạn: {h(t["effective_due"] or t["due"])}</p>'
    if t['cancelled']:body+='<p class="alert">Dừng hợp lệ: '+h(t['cancel_reason'])+'</p>'
    else:
     if editable:body+=form(f'/action/task/{tid}',csrf,'<div class="formgrid">'+field('Số lượng hoàn thành','done',t['done'],'number','min="0" max="1000000" required')+field('Số lần sửa do lỗi chủ quan','corrections',t['corrections'],'number','min="0" max="1000000" required')+field('Ngày hoàn thành thực tế','finish',t['finish'],'date')+'</div>'+textarea('Minh chứng (số văn bản, ngày, đường dẫn; nếu có tệp ghi mô tả)','evidence',t['evidence'])+check('Đề xuất vượt yêu cầu','outstanding',t['outstanding'])+textarea('Mô tả kết quả nổi trội và tác động','outstanding_note',t['outstanding_note']),'Lưu kết quả nhiệm vụ')+form(f'/action/upload/{tid}',csrf,field('Tệp TXT mẫu (tối đa 100 KB)' if DEMO else 'Tệp minh chứng (tối đa 5 MB)','file',kind='file',attrs='required accept=".txt"' if DEMO else 'required accept=".pdf,.docx,.xlsx,.png,.jpg,.jpeg,.txt"'),'Đính kèm',extra='enctype="multipart/form-data"')
     else:body+=f'<p>Hoàn thành: {h(t["done"])} / {t["qty"]} · Chỉnh sửa: {h(t["corrections"])} · Ngày hoàn thành: {h(t["finish"])} · Chậm: {z["late"]} ngày làm việc</p><p>Minh chứng: {h(t["evidence"])}</p><p>Vượt yêu cầu: {h(t["outstanding_note"])}</p>'
     body+=f'<p class="scoreline">A: {z["a"]:.2f} · B: {z["b"]:.2f} · C: {z["c"]:.2f} · KPI: {z["kpi"]:.2f}/ {z["max"]:.2f}</p>'
    if attachments:body+='<p>Tệp: '+ ' · '.join(f'<a href="/attachment/{a["id"]}">{h(a["filename"])}</a>' for a in attachments)+'</p>'
    if review and e['status'] in ('draft','returned'):
     body+='<details><summary>Điều chỉnh hợp lệ (người quản lý)</summary>'+form(f'/action/adjust/{tid}',csrf,field('Hạn điều chỉnh (nếu có)','effective_due',t['effective_due'],'date')+field('Căn cứ điều chỉnh hạn','extension_reason',t['extension_reason'])+field('Số ngày chậm chủ quan được xác nhận (để trống: tự tính)','late_override',t['late_override'],'number','min="0" max="1000000"')+field('Căn cứ điều chỉnh ngày chậm','late_reason',t['late_reason'])+check('Dừng nhiệm vụ hợp lệ','cancelled',t['cancelled'])+field('Căn cứ dừng','cancel_reason',t['cancel_reason']),'Lưu điều chỉnh')+'</details>'
    body+='</details>'
   if member_view and last_axis is not None:body+='</div></details>'
   body+='</section>'
   if editable:body+='<section class="panel"><h2>Gửi hồ sơ đánh giá</h2><p>Đề xuất sơ bộ: '+h(suggestion(calc,e['common']))+'. Phải có căn cứ giao nhiệm vụ, minh chứng và điểm tiêu chí chung.</p>'+form(f'/action/submit/{eid}',csrf,check('Xác nhận thông tin và minh chứng đúng thực tế','confirmed'),'Gửi duyệt')+'</section>'
  if review and e['status'] in ('submitted','team'):
   body+='<section class="panel'+(' team-review-panel' if member_view else '')+'"><h2>'+('NHẬN XÉT VÀ ĐÁNH GIÁ CỦA TỔ TRƯỞNG' if member_view else 'Rà soát hồ sơ')+'</h2><p>Điểm tự chấm tiêu chí chung: '+h(e['common'])+' /30 · Đề xuất: '+h(e['self_level'])+'</p>'
   if not member_view:body+=form(f'/action/return/{eid}',csrf,textarea('Lý do trả lại','note',attrs='required'),'Trả lại bổ sung')
   if team_review(u,e) and e['status']=='submitted':body+=form(f'/action/team/{eid}',csrf,field('Điểm tiêu chí chung sau rà soát (tối đa 30)','common',e['common'],'number','min="0" max="30" step="0.01" required')+textarea('Nhận xét của tổ trưởng','note',attrs='required'),'Xác nhận và chuyển BGH')
   if member_view:body+='<details class="team-return"><summary>Trả lại hồ sơ để bổ sung</summary>'+form(f'/action/return/{eid}',csrf,textarea('Lý do trả lại','note',attrs='required'),'Trả lại bổ sung')+'</details>'
   if can_manage(u):
    good,xs=group_quota(c,e);body+=f'<p>Nhóm tương đồng: HTT đã duyệt {good} · HTXS đã duyệt {xs} · tối đa {quota(good)}.</p>'+form(f'/action/approve/{eid}',csrf,field('Điểm tiêu chí chung xác nhận','common',common,'number','min="0" max="30" step="0.01" required')+select('Xếp loại chính thức','level',[(x,x) for x in LEVELS],suggestion(calc,common))+textarea('Nhận xét / căn cứ lựa chọn','note',attrs='required')+check('Đã kiểm tra điều kiện, minh chứng, thẩm quyền và tỷ lệ','confirmed'),'BGH duyệt')
   body+='</section>'
  if can_manage(u) and u['id']!=e['user'] and not e['locked'] and e['status']=='approved':body+='<section class="panel">'+form(f'/action/reopen/{eid}',csrf,textarea('Lý do mở lại hồ sơ','note',attrs='required'),'Mở lại hồ sơ')+'</section>'
  if e['self_snapshot']:body+='<section class="panel"><h2>Lịch sử tự chấm</h2><p>Điểm tự chấm lần nộp gần nhất: '+h(e['common'])+' /30 · '+h(e['self_level'])+'</p></section>'
  if editable or leader_active:body+='</div></div>'
  hist=allrows(c,'SELECT a.*,u.name FROM audit a LEFT JOIN users u ON u.id=a.actor WHERE evaluation=? ORDER BY a.id DESC LIMIT 30',(eid,));body+=('<details class="panel personal-history"><summary>Nhật ký hồ sơ</summary>' if personal or member_view else '<section class="panel"><h2>Nhật ký hồ sơ</h2>')+table(['Thời gian (UTC)','Người thực hiện','Thao tác','Chi tiết'],[[h(x['at']),h(x['name']),h(x['action']),h(x['detail'])] for x in hist])+('</details>' if personal or member_view else '</section>')
  return layout('Phiếu KPI cá nhân',body,u,csrf,compact=personal or leader_view)
@app.post('/password')
@app.post('/logout')
@app.post('/action/{action}')
@app.post('/action/{action}/{obj:int}')
async def actions(r:Request,action:str='',obj:int=0):
 f=await r.form(); action=action or r.url.path[1:];
 with closing(connect()) as c,c:
  c.execute('BEGIN IMMEDIATE');u,s=auth(c,r)
  if not u:fail('Vui lòng đăng nhập.',401)
  if not hmac.compare_digest(str(f.get('csrf','')),s['csrf']):fail('Phiên không hợp lệ.',403)
  uid=u['id']
  if action=='logout':c.execute('DELETE FROM sessions WHERE token=?',(s['token'],));res=redirect('/login');res.delete_cookie('kpi_session');return res
  if DEMO and action in ('password','reset','user'):fail('Bản demo giữ nguyên tài khoản mẫu và quyền để tránh mất quyền truy cập. Chức năng quản trị khác vẫn dùng được.',403)
  if DEMO and action=='period' and one(c,'SELECT count(*) FROM periods')[0]>=8:fail('Demo giới hạn 8 kỳ đánh giá.')
  if DEMO and action=='assign' and one(c,'SELECT count(*) FROM tasks')[0]>=400:fail('Demo giới hạn 400 nhiệm vụ.')
  if action=='password':
   old=required(f,'old',200);new=required(f,'new',200)
   if not check_password(old,u['password']) or len(new)<10 or new==old or new!=f.get('confirm'):fail('Mật khẩu cũ sai, mật khẩu mới không khớp hoặc chưa đạt yêu cầu.')
   c.execute('UPDATE users SET password=?,must_change=0 WHERE id=?',(password_hash(new),uid));c.execute('DELETE FROM sessions WHERE user=? AND token<>?',(uid,s['token']));audit(c,uid,'Đổi mật khẩu');return redirect('/')
  if u['must_change']:fail('Phải đổi mật khẩu trước khi sử dụng.',403)
  if action in ('department','period','user','reset','library','holiday','unholiday','lock'):assert_manage(u)
  try:
   if action=='department':c.execute('INSERT INTO departments(name) VALUES(?)',(required(f,'name',100),));audit(c,uid,'Thêm tổ');return redirect('/manage')
   if action=='period':
    if not f.get('confirmed'):fail('Cần xác nhận quy tắc đã được phê duyệt.')
    year=integer(f,'year',2000,2100);q=integer(f,'quarter',1,4);mode=required(f,'mode');
    if mode not in ('task','product'):fail('Quy tắc không hợp lệ')
    pid=c.execute('INSERT INTO periods(year,quarter,mode) VALUES(?,?,?)',(year,q,mode)).lastrowid;c.execute('INSERT INTO evaluations(period,user,department,cohort) SELECT ?,id,department,cohort FROM users WHERE active=1 AND code<>"ADMIN"',(pid,));audit(c,uid,'Mở kỳ',detail=f'{year}/Q{q}: {mode}');return redirect('/manage')
   if action in ('user','reset'):
    x=one(c,'SELECT * FROM users WHERE id=?',(obj,));
    if not x or (u['role']!='admin' and x['role'] in ('admin','manager')):fail('Không có quyền.',403)
    if action=='reset':
     if obj==uid:fail('Dùng chức năng đổi mật khẩu.')
     pwd=required(f,'password',200)
     if len(pwd)<10:fail('Mật khẩu quá ngắn.')
     c.execute('UPDATE users SET password=?,must_change=1 WHERE id=?',(password_hash(pwd),obj));c.execute('DELETE FROM sessions WHERE user=?',(obj,));audit(c,uid,'Đặt lại mật khẩu',detail=x['code']);return redirect('/manage')
    role=required(f,'role');dep=integer(f,'department',1,10**9,True);cohort=required(f,'cohort',100);active=int(bool(f.get('active')))
    if role not in ROLES or (role in ('manager','admin') and u['role']!='admin') or (obj==uid and (not active or role!=u['role'])) or (x['code']=='ADMIN' and (role!='admin' or not active)) or (role in ('leader','deputy') and dep is None):fail('Phân quyền không hợp lệ.')
    c.execute('UPDATE users SET department=?,cohort=?,role=?,active=? WHERE id=?',(dep,cohort,role,active,obj));
    if f.get('sync'):c.execute('UPDATE evaluations SET department=?,cohort=? WHERE user=? AND status="draft" AND period IN (SELECT id FROM periods WHERE locked=0) AND id NOT IN (SELECT evaluation FROM tasks)',(dep,cohort,obj))
    if not active:c.execute('DELETE FROM sessions WHERE user=?',(obj,))
    audit(c,uid,'Cập nhật phân quyền',detail=x['code']+' '+role);return redirect('/manage')
   if action=='library':c.execute('INSERT INTO library(title,grp,axis,product) VALUES(?,?,?,?)',(required(f,'title'),integer(f,'grp',1,4),integer(f,'axis',1,6),required(f,'product')));audit(c,uid,'Thêm nhiệm vụ mẫu');return redirect('/manage')
   if action in ('holiday','unholiday','lock'):
    p=period(c,obj);unlocked(p)
    if action=='lock':
     if not f.get('confirmed') or one(c,'SELECT count(*) FROM evaluations WHERE period=? AND status<>"approved"',(obj,))[0]:fail('Phải xác nhận và duyệt toàn bộ hồ sơ trước khi khóa.')
     groups=allrows(c,'SELECT department,cohort,SUM(final_level=?) good,SUM(final_level=?) xs FROM evaluations WHERE period=? GROUP BY department,cohort',(LEVELS[1],LEVELS[0],obj))
     if any(g['xs']>quota(g['good']) for g in groups):fail('Có nhóm vượt tỷ lệ.')
     c.execute('UPDATE periods SET locked=1 WHERE id=?',(obj,));audit(c,uid,'Khóa kỳ',detail=str(obj));return redirect('/manage')
    if one(c,'SELECT count(*) FROM evaluations WHERE period=? AND status NOT IN ("draft","returned")',(obj,))[0]:fail('Không thay đổi lịch nghỉ sau khi có hồ sơ đã nộp.')
    day=datefield(f,'day');c.execute('INSERT INTO holidays VALUES(?,?)' if action=='holiday' else 'DELETE FROM holidays WHERE period=? AND day=?',(obj,day));audit(c,uid,'Cập nhật lịch nghỉ',detail=day);return redirect(f'/period/{obj}')
   if action=='assign':
    if not can_manage(u) and u['role']!='leader':fail('Không có quyền.',403)
    p=period(c,obj);unlocked(p); libid=integer(f,'library',1,10**9,True);lib=one(c,'SELECT * FROM library WHERE id=?',(libid,)) if libid else None
    title=lib['title'] if lib else required(f,'title');product=lib['product'] if lib else required(f,'product');grp=lib['grp'] if lib else integer(f,'grp',1,4);axis=lib['axis'] if lib else integer(f,'axis',1,6);source=required(f,'source');qty=integer(f,'qty',1,1000000);due=datefield(f,'due');target=required(f,'target');
    if due>end_of_quarter(p['year'],p['quarter']).isoformat():fail('Hạn phải trong hoặc trước ngày kết thúc quý.')
    es=[e for e in scope_evals(c,u,obj) if e['status'] in ('draft','returned') and (can_manage(u) or team_review(u,e))];es=[e for e in es if target=='all' or target==f'd:{e["department"]}' or (target=='selected' and f.get(f'e_{e["id"]}'))]
    if not es:fail('Không có người nhận hợp lệ.')
    for e in es:
     if one(c,'SELECT id FROM tasks WHERE evaluation=? AND title=? AND source=?',(e['id'],title,source)):continue
     c.execute('INSERT INTO tasks(evaluation,title,source,axis,grp,product,qty,due) VALUES(?,?,?,?,?,?,?,?)',(e['id'],title,source,axis,grp,product,qty,due));audit(c,uid,'Giao nhiệm vụ',e['id'],title)
    return redirect(f'/assign?period={obj}')
   if action in ('common_template','common_copy','common_assign'):return cc.admin_action(c,u,f,action,obj)
   if action=='common_detail':
    e=get_eval(c,u,obj);cc.save(c,u,e,f);return redirect(f'/eval/{obj}?part=common')
   if action in ('self_add','self_edit','self_delete'):return axis_self.action(c,u,f,action,obj)
   if action=='axis_next':
    e=get_eval(c,u,obj);own_edit(u,e);axis=integer(f,'axis',1,6);calc=result(c,e)
    if any(t['axis']==axis and not t['cancelled'] and (not z['ready'] or not t['evidence'] or (t['outstanding'] and not t['outstanding_note'])) for t,z in calc['rows']):fail('Trục còn công việc thiếu dữ liệu. Mở công việc cần bổ sung, lưu lại rồi chuyển trục.')
    return redirect(f'/eval/{obj}?axis={axis+1}')
   if action=='axis':
    e=get_eval(c,u,obj);own_edit(u,e);axis=integer(f,'axis',1,6);advance=integer(f,'advance',0,1);tasks=allrows(c,'SELECT * FROM tasks WHERE evaluation=? AND axis=? AND cancelled=0 ORDER BY id',(obj,axis))
    if not tasks:fail('Trục này không có nhiệm vụ cần nhập.')
    for t in tasks:
     tid=t['id'];pre=f't{tid}_'
     if pre+'done' not in f or pre+'corrections' not in f:fail('Danh sách nhiệm vụ thay đổi. Vui lòng mở lại trục.')
     done=integer(f,pre+'done',0,1000000,not advance);cor=integer(f,pre+'corrections',0,1000000,not advance);finish=datefield(f,pre+'finish',True);evidence=optional(f,pre+'evidence');out=int(bool(f.get(pre+'outstanding')));on=optional(f,pre+'outstanding_note')
     if finish and finish>end_of_quarter(e['year'],e['quarter']).isoformat():fail('Ngày hoàn thành sau ngày kết thúc quý: '+t['title'])
     if advance and ((done>=t['qty'] and not finish) or not evidence or (out and not on)):fail('Cần đủ ngày hoàn thành (nếu đạt số lượng), minh chứng và mô tả vượt yêu cầu: '+t['title'])
     c.execute('UPDATE tasks SET done=?,corrections=?,finish=?,evidence=?,outstanding=?,outstanding_note=? WHERE id=?',(done,cor,finish,evidence,out,on,tid))
    audit(c,uid,'Lưu kết quả trục',obj,f'Trục {axis} · {len(tasks)} nhiệm vụ');return redirect(f'/eval/{obj}?axis={axis+advance}')
   if action in ('task','upload','adjust'):
    t=one(c,'SELECT * FROM tasks WHERE id=?',(obj,));
    if not t:fail('Không có nhiệm vụ.',404)
    e=get_eval(c,u,t['evaluation']);unlocked(e)
    if action=='adjust':
     if u['id']==e['user'] or not (can_manage(u) or team_review(u,e)) or e['status'] not in ('draft','returned'):fail('Không có quyền điều chỉnh.',403)
     ed=datefield(f,'effective_due',True);er=optional(f,'extension_reason');lo=integer(f,'late_override',0,1000000,True);lr=optional(f,'late_reason');cancel=int(bool(f.get('cancelled')));cr=optional(f,'cancel_reason')
     if (ed and not er) or (lo is not None and not lr) or (cancel and not cr):fail('Cần ghi căn cứ xác nhận.')
     c.execute('UPDATE tasks SET effective_due=?,extension_reason=?,late_override=?,late_reason=?,cancelled=?,cancel_reason=? WHERE id=?',(ed,er,lo,lr,cancel,cr,obj));audit(c,uid,'Điều chỉnh nhiệm vụ',e['id'],t['title']+' | '+er+' | '+lr+' | '+cr)
    else:
     own_edit(u,e)
     if t['cancelled']:fail('Nhiệm vụ đã dừng.')
     if action=='task':
      done=integer(f,'done',0,1000000);cor=integer(f,'corrections',0,1000000);finish=datefield(f,'finish',True);evidence=optional(f,'evidence');out=int(bool(f.get('outstanding')));on=optional(f,'outstanding_note')
      if finish and finish>end_of_quarter(e['year'],e['quarter']).isoformat():fail('Ngày hoàn thành sau ngày kết thúc quý. Chỉ nhập kết quả tại thời điểm chốt quý.')
      if done>=t['qty'] and not finish:fail('Cần ngày hoàn thành khi đủ số lượng.')
      if out and not on:fail('Cần mô tả kết quả vượt yêu cầu.')
      c.execute('UPDATE tasks SET done=?,corrections=?,finish=?,evidence=?,outstanding=?,outstanding_note=? WHERE id=?',(done,cor,finish,evidence,out,on,obj));audit(c,uid,'Lưu kết quả',e['id'],t['title'])
     else:
      file=f.get('file');
      if not isinstance(file,UploadFile):fail('Chưa chọn tệp.')
      name=Path((file.filename or '').replace('\\','/')).name[:180];data=await file.read(5*1024*1024+1);await file.close()
      if Path(name).suffix.lower() not in ('.pdf','.docx','.xlsx','.png','.jpg','.jpeg','.txt') or not data or len(data)>5*1024*1024:fail('Tệp không hợp lệ (tối đa 5 MB).')
      if DEMO and (Path(name).suffix.lower()!='.txt' or len(data)>100000 or one(c,'SELECT COALESCE(SUM(length(body)),0) FROM attachments')[0]+len(data)>1000000):fail('Demo chỉ nhận tệp TXT giả lập tối đa 100 KB, tổng 1 MB mỗi phiên.')
      if one(c,'SELECT count(*) FROM attachments WHERE task=?',(obj,))[0]>=10:fail('Tối đa 10 tệp mỗi nhiệm vụ.')
      c.execute('INSERT INTO attachments(task,filename,body) VALUES(?,?,?)',(obj,name,data));audit(c,uid,'Đính kèm minh chứng',e['id'],name)
    return redirect(f'/eval/{e["id"]}?axis={t["axis"]}')
   if action in ('common','submit','team','return','approve','reopen'):
    e=get_eval(c,u,obj);unlocked(e);calc=result(c,e)
    if action in ('common','submit'):
     own_edit(u,e)
     if action=='common':fail('Hãy chấm từng tiêu chí trong Phần I.',400)
     else:
      if not f.get('confirmed') or not calc['ready'] or cc.read(c,e) is None or e['common'] is None or e['department'] is None or any(t['outstanding'] and not t['outstanding_note'] and not t['cancelled'] for t,z in calc['rows']):fail('Cần xác nhận, phân tổ, nhiệm vụ, kết quả, minh chứng và điểm chung đầy đủ.')
      snapshot=json.dumps({'common':e['common'],'calc':calc,'level':suggestion(calc,e['common'])},ensure_ascii=False);c.execute('UPDATE evaluations SET status="submitted",self_snapshot=?,self_level=?,team_common=NULL,final_common=NULL,final_level=NULL WHERE id=?',(snapshot,suggestion(calc,e['common']),obj));audit(c,uid,'Nộp hồ sơ',obj,snapshot)
    else:
     if uid==e['user'] or not (can_manage(u) or team_review(u,e)):fail('Không có quyền duyệt hồ sơ.',403)
     note=required(f,'note',2000)
     if action=='reopen':
      if not can_manage(u) or e['status']!='approved':fail('Không thể mở lại.')
      c.execute('UPDATE evaluations SET status="returned",note=?,team_common=NULL,final_common=NULL,final_level=NULL WHERE id=?',(note,obj))
     elif e['status'] not in ('submitted','team'):fail('Hồ sơ chưa nộp hoặc đã duyệt.')
     elif action=='return':c.execute('UPDATE evaluations SET status="returned",note=?,team_common=NULL WHERE id=?',(note,obj))
     elif action=='team':
      if not team_review(u,e) or e['status']!='submitted':fail('Không có quyền xác nhận tổ.',403)
      c.execute('UPDATE evaluations SET status="team",team_common=?,note=? WHERE id=?',(number(f,'common'),note,obj))
     elif action=='approve':
      if not can_manage(u) or not f.get('confirmed'):fail('Cần BGH xác nhận.',403)
      teacher=one(c,'SELECT role FROM users WHERE id=?',(e['user'],));has_leader=one(c,'SELECT id FROM users WHERE department=? AND role="leader" AND active=1 AND id<>?',(e['department'],e['user']))
      if e['status']!='team' and has_leader and teacher['role'] not in ('leader','manager','admin'):fail('Cần tổ trưởng xác nhận trước.')
      common=number(f,'common');lev=required(f,'level');total=common+calc['kpi'];good,xs=group_quota(c,e)
      if lev not in LEVELS or (lev==LEVELS[0] and (not eligible_xs(calc,common) or xs+1>quota(good))) or (lev==LEVELS[1] and total<70-1e-8) or (lev==LEVELS[2] and total<50-1e-8):fail('Không đủ điều kiện khung điểm, minh chứng hoặc vượt tỷ lệ. Duyệt HTT trước HTXS.')
      c.execute('UPDATE evaluations SET status="approved",final_common=?,final_level=?,note=? WHERE id=?',(common,lev,note,obj))
     audit(c,uid,action,obj,note)
    return redirect(f'/eval/{obj}?axis=7' if action=='common' and f.get('axis_summary') else f'/eval/{obj}')
  except sqlite3.IntegrityError:fail('Dữ liệu trùng hoặc không hợp lệ. Kiểm tra lại.')
  fail('Thao tác không tồn tại.',404)
@app.get('/attachment/{aid}')
def attachment(aid:int,r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if not u or u['must_change']:fail('Cần đăng nhập.',401)
  a=one(c,'SELECT a.*,t.evaluation FROM attachments a JOIN tasks t ON t.id=a.task WHERE a.id=?',(aid,))
  if not a:fail('Không tìm thấy tệp.',404)
  get_eval(c,u,a['evaluation']);return Response(a['body'],media_type='application/octet-stream',headers={'Content-Disposition':"attachment; filename*=UTF-8''"+urllib.parse.quote(a['filename'])})
@app.get('/audit')
def audits(r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if not u:return redirect('/login')
  if u['must_change']:return redirect('/password')
  assert_manage(u);rows=allrows(c,'SELECT a.*,u.name FROM audit a LEFT JOIN users u ON u.id=a.actor ORDER BY a.id DESC LIMIT 300');return layout('Nhật ký hệ thống','<section class="panel">'+table(['Thời gian UTC','Người thực hiện','Hành động','Hồ sơ','Chi tiết'],[[h(x['at']),h(x['name']),h(x['action']),h(x['evaluation']),h(x['detail'][:500])] for x in rows])+'</section>',u,s['csrf'])
def workbook():
 b=io.BytesIO();w=xlsxwriter.Workbook(b,{'in_memory':True,'strings_to_formulas':False,'strings_to_urls':False});return b,w
def formats(w):
 return {k:w.add_format(v) for k,v in {'title':{'bold':True,'font_size':15,'align':'center','valign':'vcenter','font_color':'#173B62'},'head':{'bold':True,'bg_color':'#D9E7F5','border':1,'text_wrap':True,'align':'center','valign':'vcenter'},'body':{'border':1,'text_wrap':True,'valign':'top'},'num':{'border':1,'num_format':'0.00','valign':'top'},'pct':{'border':1,'num_format':'0.00%'},'date':{'border':1,'num_format':'dd/mm/yyyy','valign':'top'},'bold':{'bold':True,'bg_color':'#D9E7F5','border':1,'num_format':'0.00'},'wrap':{'text_wrap':True,'valign':'top'}}.items()}
def send_xlsx(b,w,name):
 w.close();return Response(b.getvalue(),media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':"attachment; filename*=UTF-8''"+urllib.parse.quote(name)})
def setup_sheet(sh):
 sh.set_landscape();sh.set_paper(8);sh.fit_to_pages(1,0);sh.set_margins(.25,.25,.4,.4);sh.hide_gridlines(2);sh.set_footer('&CTrang &P / &N')
def write_row(sh,r,vals,fmt):
 for j,v in enumerate(vals):sh.write(r,j,v if v is not None else '',fmt)
@app.get('/export/eval/{eid}')
def export_eval(eid:int,r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if not u or u['must_change']:fail('Cần đăng nhập.',401)
  e=get_eval(c,u,eid);calc=result(c,e);b,w=workbook()
  pe.kpi_sheet(w,c,e,calc)
  return send_xlsx(b,w,pe.filename('KPI',e))
@app.get('/export/common/{eid}')
def export_common(eid:int,r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if not u or u['must_change']:fail('Cần đăng nhập.',401)
  e=get_eval(c,u,eid);b,w=workbook();k=pe.common_sheet(w,c,e)
  return send_xlsx(b,w,pe.filename('Phu_luc_'+k+'_cham',e))

@app.get('/export/period/{pid}')
def export_period(pid:int,r:Request):
 with closing(connect()) as c:
  u,s=auth(c,r)
  if not u or u['must_change'] or u['role']=='teacher':fail('Không có quyền xuất tổng hợp.',403)
  p=period(c,pid);es=scope_evals(c,u,pid);b,w=workbook();f=formats(w);sh=w.add_worksheet('Phụ lục III');setup_sheet(sh);sh.freeze_panes(3,2);sh.merge_range('A1:M1',f'PHỤ LỤC III – TỔNG HỢP KPI QUÝ {p["quarter"]}/{p["year"]}',f['title']);sh.merge_range('A2:M2','I. TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ CÁ NHÂN',f['title']);headers=['TT','Họ và tên','Tổ','Nhóm tương đồng','Tổng NV','KPI /70','Tiêu chí chung /30','Tổng /100','NV vượt','NV chậm/chưa HT','Tự đề xuất','BGH xác nhận','Trạng thái'];write_row(sh,2,headers,f['head']);sh.set_row(2,40);groups={};xsrows=[]
  for i,e in enumerate(es,3):
   z=result(c,e);common=shown_common(e);write_row(sh,i,[i-2,e['name'],e['dept'] or 'Chưa phân tổ',e['cohort'],z['n'],round(z['kpi'],2) if z['n'] else None,common,round(common+z['kpi'],2) if common is not None and z['n'] else None,z['outstanding'],z['late'],e['self_level'],e['final_level'],STATUSES[e['status']]],f['body']);sh.set_row(i,34);k=(e['dept'] or 'Chưa phân tổ',e['cohort']);g=groups.setdefault(k,[0,0,0]);g[0]+=e['status']=='approved' and e['final_level']==LEVELS[1];g[1]+=eligible_xs(z,common);g[2]+=e['status']=='approved' and e['final_level']==LEVELS[0]
   if eligible_xs(z,common):xsrows.append([e['name'],e['dept'],e['cohort'],round(z['kpi'],2),round(common+z['kpi'],2),z['outstanding'],z['n'],e['final_level'],e['note']])
  for j,width in enumerate([6,26,22,22,10,11,13,12,10,16,30,30,20]):sh.set_column(j,j,width)
  if es:sh.autofilter(2,0,2+len(es),12)
  q=w.add_worksheet('Kiểm soát tỷ lệ');setup_sheet(q);q.merge_range('A1:G1','II. KIỂM SOÁT TỶ LỆ HOÀN THÀNH XUẤT SẮC NHIỆM VỤ',f['title']);write_row(q,1,['Tổ','Nhóm','HTT đã duyệt','20% HTT','Tối đa HTXS','Đủ điều kiện sơ bộ','HTXS đã duyệt'],f['head']);q.set_column(0,6,22);q.set_row(1,40)
  for i,(k,g) in enumerate(groups.items(),2):write_row(q,i,[k[0],k[1],g[0],g[0]*.2,quota(g[0]),g[1],g[2]],f['body']);q.write_formula(i,3,f'=C{i+1}*20%',f['num'],g[0]*.2);q.write_formula(i,4,f'=ROUND(D{i+1},0)',f['num'],quota(g[0]))
  xs=w.add_worksheet('So sánh HTXS');setup_sheet(xs);xs.merge_range('A1:I1','III. DANH SÁCH XEM XÉT HOÀN THÀNH XUẤT SẮC',f['title']);write_row(xs,1,['Họ tên','Tổ','Nhóm','KPI','Tổng điểm','NV vượt','Tổng NV','Xếp loại','Nhận xét / căn cứ'],f['head']);xs.set_column(0,8,23);xs.set_column(8,8,48)
  for i,row in enumerate(xsrows,2):write_row(xs,i,row,f['body']);xs.set_row(i,38)
  return send_xlsx(b,w,f'KPI_TONG_HOP_{p["year"]}_Q{p["quarter"]}.xlsx')
