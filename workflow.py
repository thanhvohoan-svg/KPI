"""Visual workflow linked to persisted evaluation states."""
from html import escape

ICONS={
 'person':'<circle cx="12" cy="7" r="3.5"/><path d="M5 21v-3a7 7 0 0 1 14 0v3Z"/>',
 'team':'<circle cx="9" cy="7" r="3"/><path d="M2 20v-2a7 7 0 0 1 14 0v2ZM17 4a3 3 0 0 1 0 6m1 3a5 5 0 0 1 4 5v2"/>',
 'shield':'<path d="m12 2 9 4v6c0 5-5 9-9 10-4-1-9-5-9-10V6Z"/><path d="m8 12 3 3 5-6"/>',
 'file':'<path d="M5 2h9l5 5v15H5ZM14 2v6h5m-11 7 3 3 5-6"/>',
 'arrow':'<path d="M3 12h17m-7-7 7 7-7 7"/>',
 'check':'<path d="m5 12 4 4 10-10"/>',
 'return':'<path d="m9 5-6 6 6 6M3 11h11a6 6 0 0 1 6 6v2"/>',
}
def icon(name):
 return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'+ICONS[name]+'</svg>'

def states(status,has_team=True,team_confirmed=False):
 if status=='approved':
  return ['done','done' if team_confirmed else 'skip','done','done']
 if status=='team':
  return ['done','done','current','pending']
 if status=='submitted':
  return ['done','current' if has_team else 'skip','pending' if has_team else 'current','pending']
 if status=='returned':
  return ['returned','pending' if has_team else 'skip','pending','pending']
 return ['current','pending' if has_team else 'skip','pending','pending']

def render(status,has_team=True,team_confirmed=False,locked=False):
 steps=states(status,has_team,team_confirmed)
 labels=[('CÁ NHÂN','Tự đánh giá','person'),('TỔ TRƯỞNG','Đánh giá','team'),('BAN GIÁM HIỆU','Phê duyệt','shield'),('HOÀN TẤT','Lưu hồ sơ','file')]
 desc={'current':'Đang thực hiện','done':'Đã hoàn thành','pending':'Chưa thực hiện','skip':'Không qua bước này','returned':'Trả lại bổ sung'}
 msg={'draft':'Cá nhân đang tự đánh giá','returned':'Hồ sơ được trả lại để bổ sung','submitted':'Chờ tổ trưởng đánh giá' if has_team else 'Chờ BGH đánh giá','team':'Chờ Ban Giám hiệu phê duyệt','approved':'Hồ sơ đã được BGH phê duyệt'}
 out='<section class="panel workflow" aria-label="Quy trình luân chuyển hồ sơ"><h2>QUY TRÌNH LUÂN CHUYỂN HỒ SƠ</h2><ol class="workflow-steps">'
 for i,((label,sub,key),state) in enumerate(zip(labels,steps)):
  out+='<li class="workflow-step '+state+'"'+(' aria-current="step"' if state in ('current','returned') else '')+'><div class="workflow-circle">'+icon(key)+'</div><strong>BƯỚC '+str(i+1)+'</strong><b>'+label+'</b><span>'+sub+'</span><small>'+desc[state]+'</small></li>'
  if i<3:out+='<li class="workflow-arrow" aria-hidden="true">'+icon('arrow')+'</li>'
 out+='</ol><p class="workflow-status '+('returned' if status=='returned' else '')+'">'+icon('return' if status=='returned' else 'check' if status=='approved' else 'file')+'<span>Trạng thái: '+escape(msg.get(status,'Chưa xác định'))+(' · Đã khóa kỳ' if locked else '')+'</span></p></section>'
 return out

def dashboard_card(url,title,description,key,active=False):
 return '<a class="role-card'+(' active' if active else '')+'" href="'+escape(url,quote=True)+'"'+(' aria-current="page"' if active else '')+'>'+icon(key)+'<span><strong>'+escape(title)+'</strong><small>'+escape(description)+'</small></span></a>'
