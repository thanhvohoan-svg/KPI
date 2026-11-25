"""Compact team-leader workspace. All records are supplied by the existing scoped query."""
from urllib.parse import urlencode
import workflow
import common_criteria as cc
from core import normalize

LABELS={
 'draft':'Chưa nộp','submitted':'Chờ tổ trưởng đánh giá',
 'team':'Đã chuyển BGH','approved':'BGH đã duyệt','returned':'Trả lại bổ sung'
}
ORDER={'submitted':0,'returned':1,'draft':2,'team':3,'approved':4}
SHORT={'submitted':'Chờ đánh giá','draft':'Chưa nộp','returned':'Trả lại','team':'Đã chuyển BGH','approved':'BGH đã duyệt'}

def url(pid,view='team',status='all',q=''):
 args={'period':pid,'view':view}
 if status!='all':args['status']=status
 if q:args['q']=q
 return '/?'+urlencode(args)

def tabs(pid,own_id=None,active='team'):
 own='/eval/'+str(own_id) if own_id is not None else url(pid,'self')
 return '<div class="leader-tabs role-cards">'+workflow.dashboard_card(own,'ĐÁNH GIÁ CÁ NHÂN','Hồ sơ của bản thân','person',active=='self')+workflow.dashboard_card(url(pid),'ĐÁNH GIÁ TỔ VIÊN','Hồ sơ trong tổ chuyên môn','team',active=='team')+'</div>'

def tabs_for_eval(c,u,e,active):
 own=c.execute('SELECT id FROM evaluations WHERE period=? AND user=?',(e['period'],u['id'])).fetchone()
 return tabs(e['period'],own['id'] if own else None,active)

def badge(status):
 from app import h
 return '<span class="team-status '+h(status)+'">'+h(LABELS.get(status,status))+'</span>'

def review_links(u,e,include_view=True):
 from app import team_review
 href='/eval/'+str(e['id'])
 out='<div class="team-row-actions">'
 if include_view:out+='<a class="btn small secondary" href="'+href+'">Xem hồ sơ</a>'
 if team_review(u,e) and not e['locked'] and e['status']=='submitted':
  out+='<a class="btn small team-approve-link" href="'+href+'?review=approve#team-approve">Duyệt hồ sơ</a><a class="btn small team-return-link" href="'+href+'?review=return#team-return">Trả lại</a>'
 return out+'</div>'

def dashboard(c,u,p,periods,es,csrf,r):
 from app import h,select,table,result,shown_common,layout,redirect
 pid=p['id']; own=next((e for e in es if e['user']==u['id']),None); members=[e for e in es if e['user']!=u['id']]
 view=r.query_params.get('view','team')
 if view=='self' and own:return redirect('/eval/'+str(own['id']))
 active='self' if view=='self' else 'team'
 body='<div class="leader-frame">'+tabs(pid,own['id'] if own else None,active)+'<div class="leader-content">'
 if view=='self':
  body+='<section class="panel">Chưa có hồ sơ cá nhân trong kỳ này. Vui lòng liên hệ Ban Giám hiệu.</section>'
  return layout('Đánh giá cá nhân',body+'</div></div>',u,csrf,compact=True)
 q=r.query_params.get('q','').strip()[:100]; status=r.query_params.get('status','all')
 if status not in LABELS and status!='all':status='all'
 dep=c.execute('SELECT name FROM departments WHERE id=?',(u['department'],)).fetchone()
 counts={k:sum(e['status']==k for e in members) for k in LABELS}
 body+='<section class="panel team-toolbar"><div><h2>'+h(dep['name'] if dep else 'Chưa phân tổ')+'</h2><p class="muted">Quý '+str(p['quarter'])+'/'+str(p['year'])+(' · Đã khóa kỳ' if p['locked'] else '')+' · '+str(len(members))+' tổ viên</p></div>'
 body+='<form method="get" class="inline"><input type="hidden" name="view" value="team">'+select('Kỳ đánh giá','period',[(x['id'],f'Quý {x["quarter"]}/{x["year"]}'+(' · đã khóa' if x['locked'] else '')) for x in periods],pid)+'<button>Xem</button></form><a class="btn secondary" href="/export/period/'+str(pid)+'">Xuất tổng hợp Excel</a></section>'
 body+='<div class="team-filters" aria-label="Lọc hồ sơ">'
 for key,label,n in [('all','Tất cả',len(members))]+[(k,SHORT[k],counts[k]) for k in ('submitted','draft','returned','team','approved')]:
  body+='<a class="team-filter '+key+(' active' if key==status else '')+'" href="'+h(url(pid,status=key,q=q))+'"'+(' aria-current="page"' if key==status else '')+'><span>'+h(label)+':</span><strong>'+str(n)+'</strong></a>'
 body+='</div><section class="panel team-list"><div class="team-list-top"><h2>DANH SÁCH TỔ VIÊN</h2><form method="get" class="team-search"><input type="hidden" name="period" value="'+str(pid)+'"><input type="hidden" name="view" value="team"><input type="hidden" name="status" value="'+h(status)+'"><input type="search" name="q" aria-label="Tìm giáo viên" placeholder="Tìm họ tên hoặc mã giáo viên" value="'+h(q)+'"><button>Tìm</button>'
 if q:body+='<a class="btn secondary" href="'+h(url(pid,status=status))+'">Xóa lọc</a>'
 body+='</form></div>'
 rows=[]
 for e in sorted(members,key=lambda e:(ORDER.get(e['status'],9),normalize(e['name']))):
  if status!='all' and e['status']!=status:continue
  if q and normalize(q) not in normalize(e['name']+' '+e['code']):continue
  z=result(c,e);common=shown_common(e) if cc.read(c,e) or e['status'] not in ('draft','returned') else None
  own=e['common'] if cc.read(c,e) or e['status'] not in ('draft','returned') else None
  href='/eval/'+str(e['id'])
  def fmt(v):return f'{v:.2f}' if v is not None else '—'
  common_cell='<strong>'+fmt(own)+'</strong>'
  if e['team_common'] is not None:common_cell+='<small class="team-score-stage">Tổ: '+fmt(e['team_common'])+'</small>'
  if e['final_common'] is not None:common_cell+='<small class="team-score-stage">BGH: '+fmt(e['final_common'])+'</small>'
  kpi=z['kpi'] if z['n'] else None
  rows.append([f'<a class="member-name" href="{href}">'+h(e['name'])+'</a>',badge(e['status']),common_cell,'<strong>'+fmt(kpi)+'</strong>',fmt(common+kpi) if common is not None and kpi is not None else '—',h(e['self_level'] or '—'),h(e['final_level'] or '—'),review_links(u,e)])
 if rows:body+=table(['Họ và tên','Trạng thái','Tiêu chí chung /30','KPI /70','Tổng /100','Tự xếp loại','Xếp loại chính thức','Hồ sơ / Thao tác'],rows)
 else:body+='<p class="team-empty">Không có hồ sơ phù hợp.</p>'
 body+='<p class="muted team-list-count">Hiển thị '+str(len(rows))+'/'+str(len(members))+' tổ viên. Hồ sơ chờ đánh giá được ưu tiên ở đầu.</p></section>'
 return layout('Đánh giá tổ viên',body+'</div></div>',u,csrf,compact=True)

def member_header(u,e,calc,common):
 from app import h
 import personal_exports as pe
 return '<section class="panel team-member-header"><div><a class="team-back" href="'+h(url(e['period']))+'">← Danh sách tổ viên</a><h2>'+h(e['name'])+'</h2><p class="muted">Quý '+str(e['quarter'])+'/'+str(e['year'])+' · '+h(e['dept'] or 'Chưa phân tổ')+'</p></div><div>'+badge(e['status'])+review_links(u,e,False)+pe.export_buttons(e['id'])+'</div></section>'

def score_panel(c,e,calc):
 from app import table,h
 own=e['common'] if cc.read(c,e) or e['status'] not in ('draft','returned') else None; team=e['team_common']; final=e['final_common']; kpi=calc['kpi']
 def fmt(v):return f'{v:.2f}' if v is not None else '—'
 return '<section class="panel team-score-panel"><h2>KẾT QUẢ ĐÁNH GIÁ</h2>'+table(['Nội dung','Điểm chuẩn','Cá nhân','Tổ trưởng','BGH'],[
 ['Tiêu chí chung','30',fmt(own),fmt(team),fmt(final)],
 ['KPI','70',fmt(kpi) if calc['n'] else '—',fmt(kpi) if team is not None else '—',fmt(kpi) if final is not None else '—'],
 ['<b>Tổng điểm</b>','100',fmt(own+kpi) if own is not None and calc['n'] else '—',fmt(team+kpi) if team is not None else '—',fmt(final+kpi) if final is not None else '—']
 ])+'<p class="muted">Đề xuất cá nhân: '+h(e['self_level'] or 'Chưa đề xuất')+' · Xếp loại chính thức: '+h(e['final_level'] or 'Chưa xác nhận')+'</p></section>'
