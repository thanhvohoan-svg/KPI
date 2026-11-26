"""Self-declared work in the quarterly KPI wizard. No task is treated as approved solely because it was entered."""
from core import normalize, end_of_quarter, audit

AXES={
 1:("Thực hiện mục tiêu phát triển kinh tế - xã hội và nhiệm vụ chính trị được giao","Các nhiệm vụ chuyên môn, giảng dạy, kiểm tra đánh giá, công tác chủ nhiệm và nhiệm vụ chính trị nhà trường thực sự giao trong quý."),
 2:("Hoàn thiện thể chế, phân cấp, phân quyền và kiểm tra, giám sát","Công việc xây dựng hoặc góp ý quy chế, quy trình, kế hoạch quản lý, kiểm tra nội bộ theo phân công; không kê trùng nhiệm vụ chuyên môn."),
 3:("Khoa học, công nghệ, đổi mới sáng tạo và chuyển đổi số","Công việc nghiên cứu, ứng dụng công nghệ, cải tiến phương pháp hoặc sản phẩm số có nhiệm vụ và kết quả cụ thể."),
 4:("Xây dựng Đảng và hệ thống chính trị; đoàn kết, liêm chính","Nhiệm vụ xây dựng tổ chức, công tác Đảng, đoàn thể, kiểm tra, phòng chống tiêu cực khi cá nhân được phân công."),
 5:("Phát triển văn hóa, con người và bảo đảm an sinh xã hội","Nhiệm vụ giáo dục văn hóa, kỹ năng sống, hỗ trợ học sinh, hoạt động cộng đồng hoặc an sinh có căn cứ giao việc."),
 6:("Củng cố quốc phòng, an ninh, giữ vững ổn định chính trị - xã hội, nâng cao hiệu quả đối ngoại và hội nhập quốc tế","Nhiệm vụ quốc phòng - an ninh, an toàn trường học, phối hợp hoặc đối ngoại, hội nhập theo phân công thực tế.")
}

def intro(axis):
 from app import h
 name,desc=AXES[axis]
 return f'<div class="axis-intro"><h2>{h(name)}</h2></div>'

def manageable(c,e,t):
 from app import one,DEMO
 if t['cancelled'] or t['effective_due'] or t['late_override'] is not None:return False
 mark=one(c,'SELECT action FROM audit WHERE evaluation=? AND actor=? AND detail=? AND action IN (?,?) ORDER BY id DESC LIMIT 1',(e['id'],e['user'],str(t['id']),'Tự khai nhiệm vụ','Xóa nhiệm vụ tự khai'))
 return bool(mark and mark['action']=='Tự khai nhiệm vụ') or (DEMO and t['source']=='KH DEMO 01 (giả lập)')


# Demo suggestions only. Real deployments use the school-managed task library.
SUGGESTIONS={
 1:["Thực hiện kế hoạch giảng dạy","Soạn kế hoạch bài dạy","Kiểm tra, đánh giá học sinh","Sinh hoạt chuyên môn","Công tác chủ nhiệm lớp","Bồi dưỡng học sinh giỏi","Phụ đạo học sinh","Thực hiện hồ sơ chuyên môn","Coi thi, chấm thi"],
 2:["Xây dựng hoặc góp ý quy chế nhà trường","Xây dựng quy trình chuyên môn","Tham gia kiểm tra nội bộ","Rà soát hồ sơ, kế hoạch theo phân công","Thực hiện nhiệm vụ quản lý được giao"],
 3:["Ứng dụng công nghệ trong dạy học","Xây dựng học liệu số","Thực hiện nhiệm vụ chuyển đổi số","Nghiên cứu khoa học","Thực hiện sáng kiến","Hướng dẫn học sinh nghiên cứu khoa học"],
 4:["Thực hiện nhiệm vụ công tác Đảng","Tham gia công tác Công đoàn","Tham gia công tác Đoàn thanh niên","Thực hiện nhiệm vụ xây dựng tổ chức theo phân công"],
 5:["Tổ chức hoạt động trải nghiệm, hướng nghiệp","Giáo dục kỹ năng sống","Hỗ trợ học sinh có hoàn cảnh khó khăn","Tổ chức hoạt động văn hóa, văn nghệ, thể thao","Tham gia hoạt động cộng đồng"],
 6:["Thực hiện nhiệm vụ giáo dục quốc phòng - an ninh","Tham gia công tác an toàn trường học","Tuyên truyền phòng chống tệ nạn xã hội","Tham gia phòng cháy, chữa cháy theo phân công","Thực hiện nhiệm vụ đối ngoại, hợp tác quốc tế"]
}

def choices(c,axis,current=''):
 from app import DEMO
 names=[r['title'] for r in c.execute('SELECT title FROM library WHERE axis=? ORDER BY title',(axis,))]
 if DEMO:names+=SUGGESTIONS[axis]
 if current:names.append(current)
 unique={}
 for name in names:unique.setdefault(normalize(name),name)
 return list(unique.values())

def title_fields(c,axis,t):
 from app import field,select
 current=t.get('title','')
 options=[('','-- Chọn nội dung công việc --')]+[(name,name) for name in choices(c,axis,current)]+[('__other__','Công việc khác (tự nhập)')]
 return '<div class="work-choice">'+select('Nội dung công việc', 'choice',options,current,attrs='required data-work-choice')+'<div data-work-custom>'+field('Tên công việc khác (chỉ nhập nếu chọn Công việc khác)','title',attrs='maxlength="500" placeholder="Nhập tên công việc chưa có trong danh mục"')+'</div></div>'

def quarter_label(e):
 return 'Quý '+('I','II','III','IV')[e['quarter']-1]+'/'+str(e['year'])

def date_label(e,value,due=None):
 if not value:return 'Chưa hoàn thành'
 return quarter_label(e) if value==end_of_quarter(e['year'],e['quarter']).isoformat() and (due is None or due==value) else str(value)

def quarter_field(e,label,name,value=None,optional=False,due=None,default_quarter=False):
 from app import field,select
 cutoff=end_of_quarter(e['year'],e['quarter']).isoformat()
 mode='quarter' if (value==cutoff and (due is None or due==cutoff)) or (not value and (not optional or default_quarter) and (due is None or due==cutoff)) else 'exact' if value else ''
 options=([('','Chưa hoàn thành')] if optional else [])+([('quarter',quarter_label(e))] if due is None or due==cutoff else [])+[('exact','Ngày cụ thể')]
 return '<div class="quarter-field" data-quarter-field>'+select(label,name,options,mode,attrs='data-quarter-choice')+'<div data-quarter-date>'+field('Ngày cụ thể',name+'_exact',value if mode=='exact' else '',kind='date',attrs='data-quarter-exact')+'</div></div>'

def read_quarter(f,key,e,empty=False,due=None):
 from app import datefield,fail
 value=str(f.get(key,'')).strip()
 cutoff=end_of_quarter(e['year'],e['quarter']).isoformat()
 if value=='quarter':
  if due is not None and due<cutoff:fail('Công việc có hạn riêng: hãy chọn ngày hoàn thành cụ thể để tính đúng tiến độ.')
  return cutoff
 return datefield(f,key+'_exact' if value=='exact' else key,empty and value!='exact')

def metadata(c,e,axis,t=None):
 from app import field,textarea,select,h
 from work_suggestions import catalogue
 import json
 t=t or {}
 current=t.get('title','')
 data=catalogue(c,e,axis,choices(c,axis,current)+['__other__'])
 def suggest(kind,label,value):
  options=data.get(current,data['__other__'])[kind] if current else []
  values={x['value'] for x in options}
  custom=bool(value and value not in values)
  menu='<label>'+h(label)+'<select class="field-suggestions" data-suggest="'+kind+'" required><option value="">Chọn gợi ý</option>'+''.join('<option value="'+h(x['value'])+'"'+(' selected' if x['value']==value else '')+'>'+h(x['label'])+'</option>' for x in options)+'<option value="__custom__"'+(' selected' if custom else '')+'>Tự nhập</option></select></label>'
  return '<div class="suggest-field">'+menu+'<input name="'+kind+'" type="text" value="'+h(value)+'" maxlength="500" data-suggest-value="'+kind+'" aria-label="'+h(label)+'" placeholder="Tự nhập nội dung"'+('' if custom else ' hidden')+'></div>'
 return '<div class="work-meta-fields" data-work-suggestions="'+h(json.dumps(data,ensure_ascii=False))+'">'+title_fields(c,axis,t)+'<div class="twocol work-meta">'+suggest('source','Căn cứ giao nhiệm vụ',t.get('source',''))+suggest('product','Sản phẩm cụ thể',t.get('product',''))+'</div>'+ '<div class="formgrid">'+select('Phân nhóm đề xuất','grp',[('','Chọn nhóm'),(1,'Nhóm 1 · 100 điểm'),(2,'Nhóm 2 · 150 điểm'),(3,'Nhóm 3 · 200 điểm'),(4,'Nhóm 4 · 250 điểm')],t.get('grp',''),attrs='required')+field('Số lượng phải hoàn thành','qty',t.get('qty',1),'number','min="1" max="1000000" required')+quarter_field(e,'Thời hạn hoàn thành','due',t.get('due'))+'</div></div>'

def add_panel(c,e,csrf,axis,count,add_next=False):
 from app import field,textarea,check,form
 import evidence_upload as eu
 fields=metadata(c,e,axis)+ '<div class="formgrid">'+field('Số lượng thực tế hoàn thành','done','','number','min="0" max="1000000"')+field('Số lần chỉnh sửa do lỗi chủ quan','corrections',0,'number','min="0" max="1000000"')+quarter_field(e,'Thời gian hoàn thành thực tế','finish',optional=True,default_quarter=True)+'</div>'+eu.fields()+eu.outstanding_fields(c)
 opened=' open' if add_next else ''
 return f'<div class="new-work-panel" id="new-work"><details class="new-work" name="axis-work"{opened}><summary><b class="new-work-title"><svg class="new-work-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></svg>Nhập thêm công việc {count+1}</b></summary><form method="post" action="/action/self_add/{e["id"]}" enctype="multipart/form-data" data-work-form><input type="hidden" name="csrf" value="{csrf}"><input type="hidden" name="axis" value="{axis}">'+fields+'<div class="axis-actions"><button type="submit" name="next_work" value="0" class="secondary">Lưu và thu gọn</button><button type="submit" name="next_work" value="1">Lưu và nhập công việc tiếp theo →</button></div></form></details></div>'

def delete_panel(c,e,t,csrf):
 from app import form,check
 if not manageable(c,e,t):return ''
 return '<details><summary>Xóa công việc tự khai / mẫu</summary>'+form(f'/action/self_delete/{t["id"]}',csrf,check('Xác nhận xóa công việc này và minh chứng đi kèm','confirmed'),'Xóa công việc')+'</details>'

def manage_panel(c,e,t,csrf):
 from app import form,check
 if not manageable(c,e,t):return ''
 tid=t['id']
 return '<details><summary>Sửa tên, phân nhóm, sản phẩm hoặc hạn công việc tự khai</summary>'+form(f'/action/self_edit/{tid}',csrf,metadata(c,e,t['axis'],dict(t)),'Lưu nội dung công việc',extra='data-work-form')+'</details><details><summary>Xóa công việc tự khai / mẫu</summary>'+form(f'/action/self_delete/{tid}',csrf,check('Xác nhận xóa công việc này và minh chứng đi kèm','confirmed'),'Xóa công việc')+'</details>'

def action(c,u,f,action,obj):
 from app import get_eval,own_edit,integer,datefield,required,optional,one,fail,redirect,DEMO
 uid=u['id']
 if action=='self_add':
  e=get_eval(c,u,obj);own_edit(u,e);axis=integer(f,'axis',1,6);tid=None
  if DEMO and one(c,'SELECT count(*) FROM tasks')[0]>=400:fail('Demo giới hạn 400 nhiệm vụ.')
 else:
  t=one(c,'SELECT * FROM tasks WHERE id=?',(obj,))
  if not t:fail('Không tìm thấy công việc.',404)
  e=get_eval(c,u,t['evaluation']);own_edit(u,e);axis=t['axis'];tid=t['id']
  if not manageable(c,e,t):fail('Không thể sửa hoặc xóa nhiệm vụ do quản lý giao hay đã được điều chỉnh. Liên hệ tổ trưởng.',403)
 if action=='self_delete':
  if not f.get('confirmed'):fail('Cần xác nhận xóa.')
  c.execute('DELETE FROM attachments WHERE task=?',(tid,));c.execute('DELETE FROM tasks WHERE id=?',(tid,));audit(c,uid,'Xóa nhiệm vụ tự khai',e['id'],str(tid))
  audit(c,uid,'Chi tiết công việc đã xóa',e['id'],t['title'])
  return redirect(f'/eval/{e["id"]}?axis={axis}')
 choice=required(f,'choice')
 if choice=='__other__':title=required(f,'title')
 else:
  allowed=choices(c,axis,t['title'] if action=='self_edit' else '')
  if choice not in allowed:fail('Công việc không có trong danh mục của trục này.')
  title=choice
 source=required(f,'source');product=required(f,'product');grp=integer(f,'grp',1,4);qty=integer(f,'qty',1,1000000);due=read_quarter(f,'due',e);cutoff=end_of_quarter(e['year'],e['quarter']).isoformat()
 if due>cutoff:fail('Hạn phải trong hoặc trước ngày kết thúc quý.')
 for old in c.execute('SELECT id,title,source FROM tasks WHERE evaluation=?',(e['id'],)):
  if old['id']!=tid and normalize(old['title'])==normalize(title) and normalize(old['source'])==normalize(source):fail('Công việc đã có trong phiếu. Không kê trùng giữa các trục.')
 if action=='self_edit':
  c.execute('UPDATE tasks SET title=?,source=?,product=?,grp=?,qty=?,due=? WHERE id=?',(title,source,product,grp,qty,due,tid));audit(c,uid,'Sửa nội dung công việc tự khai',e['id'],title)
 else:
  done=integer(f,'done',0,1000000,True);cor=integer(f,'corrections',0,1000000,True);finish=read_quarter(f,'finish',e,True,due);ev=optional(f,'evidence');out=int(f.get('outstanding')=='1');note=optional(f,'outstanding_note') if out else ''
  if finish and finish>cutoff:fail('Ngày hoàn thành sau thời điểm chốt quý.')
  tid=c.execute('INSERT INTO tasks(evaluation,title,source,axis,grp,product,qty,due,done,corrections,finish,evidence,outstanding,outstanding_note) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(e['id'],title,source,axis,grp,product,qty,due,done,cor,finish,ev,out,note)).lastrowid
  import evidence_upload as eu
  eu.save_files(c,u,e,tid,f)
  eu.save_outstanding(c,u,e,tid,f,out,note)
  audit(c,uid,'Tự khai nhiệm vụ',e['id'],str(tid));audit(c,uid,'Nội dung nhiệm vụ tự khai',e['id'],title)
 if action=='self_add' and f.get('next_work')=='1':return redirect(f'/eval/{e["id"]}?axis={axis}&add=1#axis-workspace')
 return redirect(f'/eval/{e["id"]}?axis={axis}')
