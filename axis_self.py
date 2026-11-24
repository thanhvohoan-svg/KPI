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
 return f'<section class="panel"><p class="eyebrow">TRỤC {axis} · HƯỚNG DẪN KÊ KHAI</p><h2>{h(name)}</h2><p>{h(desc)}</p><p class="muted">Gợi ý áp dụng cho THPT, không phải danh mục bắt buộc. Chỉ kê nhiệm vụ đã được giao có căn cứ; một nhiệm vụ chỉ tính ở một trục. Nếu không có nhiệm vụ, chuyển trục tiếp theo.</p></section>'

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

def metadata(c,axis,t=None):
 from app import field,textarea,select
 t=t or {}
 return title_fields(c,axis,t)+field('Căn cứ giao nhiệm vụ','source',t.get('source',''),attrs='required maxlength="500" placeholder="Số kế hoạch, quyết định, văn bản phân công..."')+textarea('Sản phẩm cụ thể','product',t.get('product',''),attrs='required maxlength="500"')+ '<div class="formgrid">'+select('Phân nhóm đề xuất','grp',[('','Chọn nhóm'),(1,'Nhóm 1 · 100 điểm'),(2,'Nhóm 2 · 150 điểm'),(3,'Nhóm 3 · 200 điểm'),(4,'Nhóm 4 · 250 điểm')],t.get('grp',''),attrs='required')+field('Số lượng phải hoàn thành','qty',t.get('qty',1),'number','min="1" max="1000000" required')+field('Thời hạn hoàn thành','due',t.get('due',''),'date','required')+'</div>'

def add_panel(c,e,csrf,axis,count,add_next=False):
 from app import field,textarea,check,form
 fields=metadata(c,axis)+ '<div class="formgrid">'+field('Số lượng thực tế hoàn thành','done','','number','min="0" max="1000000"')+field('Số lần chỉnh sửa do lỗi chủ quan','corrections',0,'number','min="0" max="1000000"')+field('Ngày hoàn thành thực tế','finish','','date')+'</div>'+textarea('Minh chứng','evidence',attrs='maxlength="2000" placeholder="Số văn bản, ngày, tên sản phẩm hoặc đường dẫn..."')+check('Đề xuất vượt yêu cầu','outstanding')+textarea('Kết quả nổi trội, hiệu quả','outstanding_note',attrs='maxlength="2000"')
 opened=' open' if not count or add_next else ''
 return f'<section class="panel new-work-panel" id="new-work"><details class="new-work" name="axis-work"{opened}><summary><b>＋ Nhập công việc {count+1}</b><span>Chọn hoặc tự khai công việc</span></summary><p>Chọn công việc từ danh sách xổ xuống. Nếu chưa có, chọn Công việc khác. Chỉ chọn nhiệm vụ thực tế được giao; nhóm và kết quả cần được rà soát.</p><form method="post" action="/action/self_add/{e["id"]}" data-work-form><input type="hidden" name="csrf" value="{csrf}"><input type="hidden" name="axis" value="{axis}">'+fields+'<div class="axis-actions"><button type="submit" name="next_work" value="0" class="secondary">Lưu và thu gọn</button><button type="submit" name="next_work" value="1">Lưu và nhập công việc tiếp theo →</button></div></form></details></section>'

def manage_panel(c,e,t,csrf):
 from app import form,check
 if not manageable(c,e,t):return ''
 tid=t['id']
 return '<details><summary>Sửa tên, phân nhóm, sản phẩm hoặc hạn công việc tự khai</summary>'+form(f'/action/self_edit/{tid}',csrf,metadata(c,t['axis'],dict(t)),'Lưu nội dung công việc',extra='data-work-form')+'</details><details><summary>Xóa công việc tự khai / mẫu</summary>'+form(f'/action/self_delete/{tid}',csrf,check('Xác nhận xóa công việc này và minh chứng đi kèm','confirmed'),'Xóa công việc')+'</details>'

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
 source=required(f,'source');product=required(f,'product');grp=integer(f,'grp',1,4);qty=integer(f,'qty',1,1000000);due=datefield(f,'due');cutoff=end_of_quarter(e['year'],e['quarter']).isoformat()
 if due>cutoff:fail('Hạn phải trong hoặc trước ngày kết thúc quý.')
 for old in c.execute('SELECT id,title,source FROM tasks WHERE evaluation=?',(e['id'],)):
  if old['id']!=tid and normalize(old['title'])==normalize(title) and normalize(old['source'])==normalize(source):fail('Công việc đã có trong phiếu. Không kê trùng giữa các trục.')
 if action=='self_edit':
  c.execute('UPDATE tasks SET title=?,source=?,product=?,grp=?,qty=?,due=? WHERE id=?',(title,source,product,grp,qty,due,tid));audit(c,uid,'Sửa nội dung công việc tự khai',e['id'],title)
 else:
  done=integer(f,'done',0,1000000,True);cor=integer(f,'corrections',0,1000000,True);finish=datefield(f,'finish',True);ev=optional(f,'evidence');out=int(bool(f.get('outstanding')));note=optional(f,'outstanding_note')
  if finish and finish>cutoff:fail('Ngày hoàn thành sau thời điểm chốt quý.')
  tid=c.execute('INSERT INTO tasks(evaluation,title,source,axis,grp,product,qty,due,done,corrections,finish,evidence,outstanding,outstanding_note) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(e['id'],title,source,axis,grp,product,qty,due,done,cor,finish,ev,out,note)).lastrowid
  audit(c,uid,'Tự khai nhiệm vụ',e['id'],str(tid));audit(c,uid,'Nội dung nhiệm vụ tự khai',e['id'],title)
 if action=='self_add' and f.get('next_work')=='1':return redirect(f'/eval/{e["id"]}?axis={axis}&add=1#new-work')
 return redirect(f'/eval/{e["id"]}?axis={axis}')
