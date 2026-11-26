"""Two independent leader approvals, scoped to the current submission."""
from html import escape

def setup(c):
 c.execute('CREATE TABLE IF NOT EXISTS team_section_reviews(evaluation INTEGER NOT NULL REFERENCES evaluations(id),part TEXT NOT NULL CHECK(part IN ("common","kpi")),actor INTEGER NOT NULL REFERENCES users(id),score REAL,note TEXT NOT NULL DEFAULT "",at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(evaluation,part))')

def read(c,e):
 setup(c)
 return {r['part']:r for r in c.execute('SELECT * FROM team_section_reviews WHERE evaluation=?',(e['id'],))}

def clear(c,eid):
 setup(c)
 c.execute('DELETE FROM team_section_reviews WHERE evaluation=?',(eid,))

def approve(c,u,e,f,calc):
 from app import fail,team_review,number,h
 from core import audit
 if not team_review(u,e) or e['status']!='submitted' or e['locked']:fail('Không có quyền xác nhận tổ.',403)
 part=str(f.get('part',''))
 if part not in ('common','kpi'):fail('Cần duyệt riêng phụ lục và KPI.',400)
 saved=read(c,e)
 if part in saved:fail('Phần này đã được duyệt.',409)
 note=str(f.get('note','')).strip()
 if len(note)>2000:fail('Nhận xét quá dài.',400)
 score=number(f,'common') if part=='common' else calc['kpi']
 c.execute('INSERT INTO team_section_reviews(evaluation,part,actor,score,note) VALUES(?,?,?,?,?)',(e['id'],part,u['id'],score,note))
 audit(c,u['id'],'Duyệt phụ lục' if part=='common' else 'Duyệt KPI',e['id'],f'{score:.2f} điểm'+(' · '+note if note else ''))
 saved=read(c,e)
 if 'common' in saved and 'kpi' in saved:
  notes='; '.join(('Phụ lục: ' if k=='common' else 'KPI: ')+saved[k]['note'] for k in ('common','kpi') if saved[k]['note'])
  c.execute('UPDATE evaluations SET status="team",team_common=?,note=? WHERE id=?',(saved['common']['score'],notes or 'Tổ trưởng đã duyệt phụ lục và KPI.',e['id']))
  audit(c,u['id'],'Tổ đã duyệt',e['id'],'Đủ hai phần, chuyển BGH')
  return '/eval/'+str(e['id'])+'#review-finished'
 return '/eval/'+str(e['id'])+('?section=kpi#team-kpi' if part=='common' else '?section=common#team-approve')

def progress(e,saved):
 done=2 if e['status'] in ('team','approved') and e['team_common'] is not None else len(saved) if e['status']=='submitted' else 0
 return '<div id="team-review-progress" class="team-review-progress"><strong>TIẾN ĐỘ DUYỆT: '+str(done)+'/2</strong><span>'+('Đã chuyển BGH' if done==2 else 'Duyệt đủ hai phần để chuyển BGH' if e['status']=='submitted' else 'Chưa đến lượt tổ trưởng duyệt')+'</span></div>'

def approval_form(e,part,saved,csrf,active):
 from app import form,field,textarea,h
 old=saved.get(part)
 if old is not None and e['status'] in ('submitted','team','approved'):
  return '<div class="section-approved">✓ Đã duyệt '+('phụ lục' if part=='common' else 'KPI')+' · '+f'{old["score"]:.2f}'+' điểm'+(' · '+h(old['note']) if old['note'] else '')+'</div>'
 if not active:return ''
 fields='<input type="hidden" name="part" value="'+part+'">'
 if part=='common':fields+=field('Điểm tiêu chí chung tổ trưởng xác nhận /30','common',e['common'],'number','min="0" max="30" step="0.01" required')
 fields+='<details class="section-note"><summary>Nhận xét (nếu có)</summary>'+textarea('Nhận xét','note')+'</details>'
 return '<div class="section-approve">'+form('/action/team/'+str(e['id']),csrf,fields,'Duyệt phụ lục' if part=='common' else 'Duyệt KPI')+'</div>'
