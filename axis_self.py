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

def metadata(t=None):
 from app import field,textarea,select
 t=t or {}
 return field('Tên công việc / nhiệm vụ','title',t.get('title',''),attrs='required maxlength="500" placeholder="Nhập công việc thực tế được giao"')+field('Căn cứ giao nhiệm vụ','source',t.get('source',''),attrs='required maxlength="500" placeholder="Số kế hoạch, quyết định, văn bản phân công..."')+textarea('Sản phẩm cụ thể','product',t.get('product',''),attrs='required maxlength="500"')+ '<div class="formgrid">'+select('Phân nhóm đề xuất','grp',[('','Chọn nhóm'),(1,'Nhóm 1 · 100 điểm'),(2,'Nhóm 2 · 150 điểm'),(3,'Nhóm 3 · 200 điểm'),(4,'Nhóm 4 · 250 điểm')],t.get('grp',''),attrs='required')+field('Số lượng phải hoàn thành','qty',t.get('qty',1),'number','min="1" max="1000000" required')+field('Thời hạn hoàn thành','due',t.get('due',''),'date','required')+'</div>'

def add_panel(e,csrf,axis,has_tasks):
 from app import field,textarea,check,form
 fields=metadata()+ '<div class="formgrid">'+field('Số lượng thực tế hoàn thành','done','','number','min="0" max="1000000"')+field('Số lần chỉnh sửa do lỗi chủ quan','corrections',0,'number','min="0" max="1000000"')+field('Ngày hoàn thành thực tế','finish','','date')+'</div>'+textarea('Minh chứng','evidence',attrs='maxlength="2000" placeholder="Số văn bản, ngày, tên sản phẩm hoặc đường dẫn..."')+check('Đề xuất vượt yêu cầu','outstanding')+textarea('Kết quả nổi trội, hiệu quả','outstanding_note',attrs='maxlength="2000"')
 return '<section class="panel"><details'+('' if has_tasks else ' open')+'><summary><b>＋ Thêm công việc vào trục</b></summary><p>Giáo viên tự khai tên công việc. Nhóm và kết quả là tự đề xuất, cần được người có thẩm quyền rà soát.</p>'+form(f'/action/self_add/{e["id"]}',csrf,f'<input type="hidden" name="axis" value="{axis}">'+fields,'Lưu công việc')+'</details></section>'

def manage_panel(c,e,t,csrf):
 from app import form,check
 if not manageable(c,e,t):return ''
 tid=t['id']
 return '<details><summary>Sửa tên, phân nhóm, sản phẩm hoặc hạn công việc tự khai</summary>'+form(f'/action/self_edit/{tid}',csrf,metadata(dict(t)),'Lưu nội dung công việc')+'</details><details><summary>Xóa công việc tự khai / mẫu</summary>'+form(f'/action/self_delete/{tid}',csrf,check('Xác nhận xóa công việc này và minh chứng đi kèm','confirmed'),'Xóa công việc')+'</details>'

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
 title=required(f,'title');source=required(f,'source');product=required(f,'product');grp=integer(f,'grp',1,4);qty=integer(f,'qty',1,1000000);due=datefield(f,'due');cutoff=end_of_quarter(e['year'],e['quarter']).isoformat()
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
 return redirect(f'/eval/{e["id"]}?axis={axis}')
