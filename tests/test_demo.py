import os, tempfile, re, sys, io, unittest
from pathlib import Path
TMP=tempfile.TemporaryDirectory()
os.environ['KPI_DEMO_DIR']=TMP.name
os.environ['KPI_HTTPS']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from demo import app, PASS
from fastapi.testclient import TestClient
from openpyxl import load_workbook
def common_data(c,eid,target):
 from common_criteria import DEFAULT,leaves
 import re
 page=c.get(f'/eval/{eid}?part=common').text
 m=re.search(r'name="template_token" value="([^"]+)"',page)
 assert m is not None
 rows=leaves(DEFAULT['3']);data={'template_token':m.group(1)}
 remaining=30-target
 for key,_,maximum in rows:
  reduction=min(remaining,maximum);remaining-=reduction;data['score_'+key]=str(maximum-reduction)
 return data

class DemoTest(unittest.TestCase):
 def client(self): return TestClient(app,base_url='https://testserver')
 def csrf(self,c,path='/'):
  r=c.get(path); m=re.search(r'name="csrf" value="([^"]+)"',r.text);self.assertIsNotNone(m,r.text[:200]);return m.group(1)
 def post(self,c,path,data,source='/',expected=303):
  r=c.post(path,data={'csrf':self.csrf(c,source),**data},follow_redirects=False);self.assertEqual(r.status_code,expected,r.text[:400]);return r
 def login(self,c,name): self.post(c,'/login',{'name':name,'password':PASS},'/login')
 def logout(self,c): self.post(c,'/logout',{})
 def test_demo_full(self):
  c=self.client();other=self.client()
  self.assertEqual(c.get('/healthz').json()['status'],'ok');self.assertNotIn('kpi_demo_workspace',c.cookies)
  self.login(c,'giaovien'); self.login(other,'giaovien')
  self.assertNotEqual(c.cookies['kpi_demo_workspace'],other.cookies['kpi_demo_workspace'])
  self.assertEqual(c.get('/eval/2').status_code,403);self.assertEqual(c.get('/export/eval/2').status_code,403);self.assertEqual(c.get('/export/common/2').status_code,403);self.assertEqual(c.get('/manage').status_code,403)
  self.assertIn('Nội dung công việc',c.get('/eval/1?axis=1').text)
  self.assertNotIn('Chưa có công việc đã lưu',c.get('/eval/1?axis=1').text)
  self.assertNotIn('Lưu ý khi kê khai',c.get('/eval/1?axis=1').text)
  self.assertIn('Bồi dưỡng học sinh giỏi',c.get('/eval/1?axis=1').text)
  self.assertNotIn('Bồi dưỡng học sinh giỏi',c.get('/eval/1?axis=3').text)
  base={'source':'KH giả lập','product':'Sản phẩm mẫu','grp':'1','qty':'1','due':'2026-09-30','done':'1','corrections':'0','finish':'2026-09-30','evidence':'Minh chứng giả lập'}
  self.post(c,'/action/self_add/2',dict(base,axis='1',choice='Bồi dưỡng học sinh giỏi'),'/eval/1',403)
  self.post(c,'/action/self_add/1',dict(base,axis='3',choice='Bồi dưỡng học sinh giỏi'),'/eval/1',400)
  for axis,title in [('1','Bồi dưỡng học sinh giỏi'),('1','Sinh hoạt chuyên môn'),('3','Ứng dụng công nghệ trong dạy học')]:
   self.post(c,'/action/self_add/1',dict(base,axis=axis,choice=title),'/eval/1')
  self.assertIn('Bồi dưỡng học sinh giỏi',c.get('/eval/1?axis=1').text)
  self.post(c,'/action/self_add/1',dict(base,axis='1',choice='Bồi dưỡng học sinh giỏi'),'/eval/1',400)
  self.post(c,'/action/common_detail/1',common_data(c,1,29),'/eval/1');self.post(c,'/action/submit/1',{'confirmed':'1'},'/eval/1')
  self.assertIn('Chờ tổ trưởng đánh giá',c.get('/eval/1').text);self.assertIn('class="workflow-step current" aria-current="step"',other.get('/eval/1').text);self.assertIn('class="personal-flow-content"',other.get('/eval/1').text)
  self.post(c,'/action/common/1',{'common':'30'},'/eval/1',403)
  self.logout(c);self.login(c,'totruong');self.assertEqual(c.get('/eval/5').status_code,403);self.assertEqual(c.get('/export/eval/5').status_code,403)
  pending=c.get('/?period=1&view=team&status=submitted').text
  self.assertIn('href="/eval/1"',pending)
  self.assertIn('href="/eval/3"',pending) # submitted demo sample
  self.assertIn('Tự xếp loại',pending)
  self.assertIn('Xếp loại chính thức',pending)
  self.assertIn('Hoàn thành tốt nhiệm vụ',pending)
  self.assertIn('Xem &amp; duyệt hồ sơ',pending)
  self.assertNotIn('/eval/1?review=approve',pending)
  self.assertIn('/eval/1?review=return#team-return',pending)
  self.assertIn('id="team-approve"',c.get('/eval/1?review=approve').text)
  returned=c.get('/eval/1?review=return').text
  self.assertIn('id="team-return" class="team-return team-action-target" open',returned)
  self.assertIn('action="/action/return/1"',returned)
  self.assertIn('href="/eval/1"',c.get('/?period=1&view=team&status=submitted').text)
  self.post(c,'/action/team/1',{'part':'kpi'},'/eval/1')
  self.assertIn('Đã duyệt 1/2 phần',c.get('/?period=1&view=team&status=submitted').text)
  self.post(c,'/action/return/1',{'note':'Bổ sung minh chứng thử nghiệm'},'/eval/1')
  self.assertIn('Trả lại bổ sung',c.get('/?period=1&view=team&status=returned').text)
  self.assertNotIn('/eval/1?review=approve',c.get('/?period=1&view=team&status=returned').text)
  self.logout(c);self.login(c,'giaovien')
  self.assertIn('Bổ sung minh chứng thử nghiệm',c.get('/eval/1').text)
  self.post(c,'/action/submit/1',{'confirmed':'1'},'/eval/1')
  self.logout(c);self.login(c,'totruong')
  review=c.get('/eval/1').text
  for label in ('QUY TRÌNH LUÂN CHUYỂN HỒ SƠ','<h2>KẾT QUẢ ĐÁNH GIÁ</h2>','TIẾN ĐỘ DUYỆT:','XEM HỒ SƠ ĐÁNH GIÁ','team-flow-frame','Xuất Excel phụ lục chấm','Xuất Excel KPI'):
   self.assertNotIn(label,review)
  self.assertIn('class="review-sections"',review)
  self.assertIn('id="team-approve" class="review-part team-action-target" name="review-section" open',review)
  self.assertIn('id="team-kpi" class="review-part team-action-target" name="review-section">',review)
  self.assertIn('Duyệt phụ lục',review)
  self.assertIn('Duyệt KPI',review)
  self.assertIn('class="sheet-table sheet-common"',review)
  self.assertIn('class="sheet-table sheet-kpi"',review)
  self.assertIn('colspan="19"',review)
  self.assertIn('<details class="declared-evidence">',review)
  self.assertIn('Hiện minh chứng (3 công việc)',review)
  self.assertIn('TỔNG ĐIỂM TIÊU CHÍ CHUNG',review)
  self.assertIn('TỔNG ĐIỂM PHẦN B',review)
  self.assertIn('Bồi dưỡng học sinh giỏi',review)
  self.assertIn('action="/action/team/1"',review)
  self.assertIn('action="/action/return/1"',review)
  self.post(c,'/action/team/1',{'part':'common','common':'28','note':'Tổ đã rà soát'},'/eval/1')
  after=c.get('/eval/1').text
  self.assertIn('✓ Đã duyệt',after)
  self.assertIn('id="team-kpi" class="review-part team-action-target" name="review-section" open',after)
  self.assertIn('Đã duyệt 1/2 phần',c.get('/?period=1&view=team&status=submitted').text)
  self.post(c,'/action/team/1',{'part':'common','common':'28'},'/eval/1',409)
  self.post(c,'/action/team/1',{'part':'kpi'},'/eval/1')
  self.assertIn('Đã duyệt đủ hai phần. Hồ sơ đã chuyển BGH.',c.get('/eval/1').text)
  self.assertIn('Đã chuyển BGH',c.get('/?period=1&view=team&status=team').text)
  self.assertNotIn('action="/action/team/1"',c.get('/eval/1').text)
  self.assertNotIn('/eval/1?review=approve',c.get('/?period=1&view=team&status=team').text)
  self.logout(c);self.login(c,'bangiamhieu');self.assertEqual(c.get('/manage').status_code,200)
  self.post(c,'/action/approve/1',{'common':'28','level':'Hoàn thành tốt nhiệm vụ','note':'BGH duyệt mẫu','confirmed':'1'},'/eval/1')
  self.assertIn('Hồ sơ đã được BGH phê duyệt',c.get('/eval/1').text)
  r=c.get('/export/eval/1');self.assertEqual(r.status_code,200); w=load_workbook(io.BytesIO(r.content),data_only=True);self.assertEqual(w.sheetnames,['CONG CHUC']);total=next(row for row in w.active.iter_rows() if str(row[0].value).startswith('TỔNG ĐIỂM PHẦN B'));self.assertAlmostEqual(total[17].value,70);self.assertAlmostEqual(total[16].value,70);self.assertIn('KPI_',r.headers['content-disposition'])
  r=c.get('/export/common/1');self.assertEqual(r.status_code,200);w=load_workbook(io.BytesIO(r.content),data_only=True);self.assertEqual(w.sheetnames,['Tiêu chí chung']);total=next(row for row in w.active.iter_rows() if row[0].value=='TỔNG ĐIỂM TIÊU CHÍ CHUNG');self.assertEqual(total[3].value,29);self.assertIn('Phu_luc_3_cham_',r.headers['content-disposition'])
  r=c.get('/export/period/1');self.assertEqual(r.status_code,200);w=load_workbook(io.BytesIO(r.content),data_only=True);self.assertEqual(len(w.sheetnames),3)
  self.logout(c);self.login(c,'giaovien');self.assertIn('Hồ sơ đã được BGH phê duyệt',c.get('/eval/1').text)
  self.assertIn('class="workflow-step current" aria-current="step"',other.get('/eval/1').text);self.assertIn('class="personal-flow-content"',other.get('/eval/1').text)
  self.post(c,'/password',{'old':PASS,'new':'NewPassword!123','confirm':'NewPassword!123'},'/',403)
 def test_compact_teacher_home(self):
  c=self.client();self.login(c,'giaovien')
  landing=c.get('/',follow_redirects=False)
  self.assertEqual(landing.status_code,200)
  self.assertIn('CHỌN KỲ ĐÁNH GIÁ',landing.text)
  for q in range(1,5):self.assertIn('QUÝ '+str(q),landing.text)
  self.assertIn('href="/my-period/1"',landing.text)
  self.assertIn('KHỞI TẠO HỒ SƠ',c.get('/my-period/1').text)
  self.post(c,'/action/period_start/1',{'mode':'new'},'/my-period/1')
  self.assertEqual(c.get('/my-period/1',follow_redirects=False).headers['location'],'/eval/1')
  page=c.get('/eval/1').text
  self.assertIn('class="header-account"',page)
  self.assertIn('<strong>Giáo viên Tin học mẫu</strong>',page)
  self.assertNotIn('Danh sách hồ sơ',page)
  self.assertNotIn('Mở hồ sơ',page)
  self.assertNotIn('<h1>Tổng quan</h1>',page)
  self.assertNotIn('name="period"',page)
  self.assertNotIn('class="panel personal-step-heading"',page)
  self.assertNotIn('BƯỚC 1. CÁ NHÂN TỰ ĐÁNH GIÁ',page)
  self.assertLess(page.index('QUY TRÌNH LUÂN CHUYỂN HỒ SƠ'),page.index('PHẦN I. TIÊU CHÍ CHUNG'))
  self.assertIn('PHẦN I. TIÊU CHÍ CHUNG',page)
  self.assertNotIn('Trạng thái: Cá nhân đang tự đánh giá',page)
  self.assertIn('class="personal-flow-frame"',page)
  self.assertIn('class="panel workflow workflow-connected"',page)
  self.assertIn('class="personal-flow-content"',page)
  self.assertLess(page.index('class="personal-flow-content"'),page.index('PHẦN I. TIÊU CHÍ CHUNG'))
  summary=c.get('/eval/1?axis=7').text
  self.assertIn('XUẤT EXCEL HỒ SƠ ĐÁNH GIÁ',summary)
  self.assertIn('summary-scores',summary)
 def test_workflow_and_leader_views(self):
  from workflow import states,render
  self.assertEqual(states('draft'),['current','pending','pending','pending'])
  self.assertEqual(states('submitted',False),['done','skip','current','pending'])
  self.assertEqual(states('team'),['done','done','current','pending'])
  self.assertEqual(states('approved',True,False),['done','skip','done','done'])
  self.assertEqual(states('returned')[0],'returned')
  self.assertEqual(render('draft').count('class="workflow-arrow"'),3)
  for status in ('draft','submitted','team','returned','approved'):
   html=render(status,omit_team=True)
   self.assertEqual(html.count('class="workflow-arrow"'),2)
   self.assertIn('workflow-three',html)
   self.assertNotIn('<b>TỔ TRƯỞNG</b>',html)
   self.assertNotIn('BƯỚC 4',html)
  self.assertIn('Chờ BGH đánh giá',render('submitted',omit_team=True))
  c=self.client();self.login(c,'totruong')
  personal=c.get('/?period=1&view=self')
  self.assertEqual(personal.status_code,200)
  self.assertIn('ĐÁNH GIÁ CÁ NHÂN',personal.text)
  self.assertIn('ĐÁNH GIÁ TỔ VIÊN',personal.text)
  self.assertEqual(personal.url.path,'/eval/2')
  self.assertIn('workflow-three',personal.text)
  self.assertNotIn('<b>TỔ TRƯỞNG</b>',personal.text)
  self.assertNotIn('BƯỚC 4',personal.text)
  self.assertLess(personal.text.index('QUY TRÌNH LUÂN CHUYỂN HỒ SƠ'),personal.text.index('ĐÁNH GIÁ CÁ NHÂN'))
  self.assertIn('class="personal-flow-content"',personal.text)
  self.assertIn('PHỤ LỤC 2',personal.text)
  self.assertNotIn('DANH SÁCH TỔ VIÊN',personal.text)
  self.assertNotIn('action="/action/team/2"',personal.text)
  team=c.get('/?period=1&view=team')
  self.assertIn('DANH SÁCH TỔ VIÊN',team.text)
  self.assertIn('QUY TRÌNH LUÂN CHUYỂN HỒ SƠ CÁ NHÂN',team.text)
  self.assertNotIn('<b>TỔ TRƯỞNG</b>',team.text)
  self.assertLess(team.text.index('QUY TRÌNH LUÂN CHUYỂN HỒ SƠ'),team.text.index('ĐÁNH GIÁ CÁ NHÂN'))
  self.assertIn('Tiêu chí chung /30',team.text)
  self.assertIn('KPI /70',team.text)
  self.assertIn('class="team-filters"',team.text)
  self.assertIn('class="member-name"',team.text)
  self.assertIn('Xem &amp; duyệt hồ sơ',team.text)
  self.assertIn('Tự xếp loại',team.text)
  self.assertIn('Xếp loại chính thức',team.text)
  self.assertNotIn('/eval/3?review=approve',team.text)
  self.assertIn('/eval/3?review=return#team-return',team.text)
  self.assertIn('team-action-disabled" disabled',team.text)
  self.assertNotIn('/eval/1?review=approve',team.text)
  self.assertNotIn('/eval/1?review=return',team.text)
  self.assertLess(team.text.index('<th>Xếp loại chính thức</th>'),team.text.index('<th>Hồ sơ / Thao tác</th>'))
  self.assertIn('id="team-approve"',c.get('/eval/3?review=approve').text)
  self.assertIn('href="/eval/1"',team.text)
  self.assertIn('href="/eval/2"',team.text) # personal navigation, not a row
  self.assertNotIn('href="/eval/5"',team.text)
  self.assertNotIn('<td>Tổ trưởng Tin học mẫu</td>',team.text)
  self.assertIn('name="q"',team.text)
  searched=c.get('/?period=1&view=team&q=DEMO03')
  self.assertIn('href="/eval/3"',searched.text)
  self.assertNotIn('href="/eval/1"',searched.text)
  empty=c.get('/?period=1&view=team&status=submitted&q=khongcogiaoviennay')
  self.assertIn('Không có hồ sơ phù hợp.',empty.text)
  self.assertEqual(c.get('/eval/5').status_code,403)
  self.post(c,'/action/team/2',{'common':'30','note':'Không được tự duyệt'},'/eval/2',403)
  self.assertIn('QUY TRÌNH LUÂN CHUYỂN HỒ SƠ',c.get('/eval/2').text)
  member=c.get('/eval/1').text
  self.assertNotIn('QUY TRÌNH LUÂN CHUYỂN HỒ SƠ',member)
  self.assertIn('class="review-sections"',member)
 def test_sequential_work_cards(self):
  c=self.client();self.login(c,'giaovien')
  base={'source':'KH thử','product':'Sản phẩm thử','grp':'1','qty':'1','due':'2026-09-30','done':'1','corrections':'0','finish':'2026-09-30','evidence':'Minh chứng mẫu'}
  first=self.post(c,'/action/self_add/1',dict(base,axis='1',choice='Bồi dưỡng học sinh giỏi',next_work='1'),'/eval/1')
  self.assertEqual(first.headers['location'],'/eval/1?axis=1&add=1#axis-workspace')
  page=c.get('/eval/1?axis=1&add=1').text
  self.assertIn('Công việc 1: Bồi dưỡng học sinh giỏi',page)
  self.assertIn('Nhập thêm công việc 2',page)
  self.assertNotIn('CÔNG VIỆC ĐÃ LƯU',page)
  self.assertNotIn('Chưa nhập công việc',page)
  self.assertIn('KPI: 70.00/70.00',page)
  other_axis=c.get('/eval/1?axis=2').text
  self.assertIn('KPI: 70.00/70.00',other_axis)
  self.assertNotIn('Chưa nhập công việc',other_axis)
  summary=c.get('/eval/1?axis=7').text
  self.assertIn('Bồi dưỡng học sinh giỏi',summary)
  self.assertNotIn('Công việc đã lưu',summary)
  self.assertNotIn('Điểm tạm tính',summary)
  self.assertEqual(page.count('class="panel axis-workspace" id="axis-workspace"'),1)
  self.assertIn('class="axis-intro"',page)
  self.assertNotIn('class="axis-progress"',page)
  self.assertIn('class="new-work-panel"',page)
  self.assertNotIn('class="panel new-work-panel"',page)
  self.assertIn('<details class="task work-card" name="axis-work">',page)
  self.assertIn('<details class="new-work" name="axis-work" open>',page)
  self.post(c,'/action/self_add/1',dict(base,axis='1',choice='Sinh hoạt chuyên môn',next_work='0'),'/eval/1')
  page=c.get('/eval/1?axis=1').text
  self.assertIn('Công việc 1: Bồi dưỡng học sinh giỏi',page)
  self.assertIn('Công việc 2: Sinh hoạt chuyên môn',page)
  self.assertIn('Nhập thêm công việc 3',page)
  self.assertEqual(page.count('<details class="task work-card" name="axis-work">'),2)
  self.assertIn('<details class="new-work" name="axis-work">',page)
  self.post(c,'/action/self_add/1',dict(base,axis='1',choice='Công tác chủ nhiệm lớp',done='',evidence='',finish=''),'/eval/1')
  self.post(c,'/action/axis_next/1',{'axis':'1'},'/eval/1',400)
  ids=re.findall(r'/action/task/(\d+)',c.get('/eval/1?axis=1').text)
  self.assertEqual(len(ids),3)
  self.post(c,'/action/task/'+ids[-1],{'done':'1','corrections':'0','finish':'2026-09-30','evidence':'Minh chứng'},'/eval/1')
  nxt=self.post(c,'/action/axis_next/1',{'axis':'1'},'/eval/1')
  self.assertEqual(nxt.headers['location'],'/eval/1?axis=2')
  self.assertIn('Công việc 1: Bồi dưỡng học sinh giỏi',c.get('/eval/1?axis=1').text)
 def test_quarter_work_fields(self):
  c=self.client();self.login(c,'giaovien')
  page=c.get('/eval/1?axis=1').text
  self.assertIn('Thời gian hoàn thành thực tế',page)
  self.assertIn('value="quarter" selected>Quý III/2026',page)
  base={'source':'KH mẫu','product':'Sản phẩm mẫu','grp':'1','qty':'1','done':'1','corrections':'0','axis':'1','evidence':'Minh chứng mẫu'}
  self.post(c,'/action/self_add/1',dict(base,choice='Bồi dưỡng học sinh giỏi',due='quarter',finish='quarter'),'/eval/1')
  page=c.get('/eval/1?axis=1').text
  self.assertIn('value="quarter" selected>Quý III/2026',page)
  self.assertIn('KPI: 70.00/70.00',page)
  self.post(c,'/action/self_add/1',dict(base,choice='Sinh hoạt chuyên môn',due='exact',due_exact='2026-09-25',finish='quarter'),'/eval/1',400)
  self.post(c,'/action/self_add/1',dict(base,choice='Sinh hoạt chuyên môn',due='exact',due_exact='2026-09-25',finish='exact',finish_exact='2026-09-30'),'/eval/1')
  page=c.get('/eval/1?axis=1').text
  ids=re.findall(r'/action/task/(\d+)',page)
  self.assertEqual(len(ids),2)
  self.post(c,'/action/task/'+ids[1],dict(done='1',corrections='0',finish='quarter',evidence='Minh chứng'),'/eval/1',400)
  self.post(c,'/action/task/'+ids[0],dict(done='1',corrections='0',finish='quarter',evidence='Minh chứng'),'/eval/1')
  r=c.get('/export/eval/1');self.assertEqual(r.status_code,200)
  w=load_workbook(io.BytesIO(r.content),data_only=True);sh=w.active
  rows={row[1].value:row for row in sh.iter_rows() if row[1].value in ('Bồi dưỡng học sinh giỏi','Sinh hoạt chuyên môn')}
  self.assertEqual(rows['Bồi dưỡng học sinh giỏi'][6].value,'Quý III/2026')
  self.assertEqual(rows['Bồi dưỡng học sinh giỏi'][12].value,'Quý III/2026')
  self.assertEqual(rows['Sinh hoạt chuyên môn'][6].value.strftime('%Y-%m-%d'),'2026-09-25')
  self.assertEqual(rows['Sinh hoạt chuyên môn'][12].value.strftime('%Y-%m-%d'),'2026-09-30')
  self.assertLess(rows['Sinh hoạt chuyên môn'][13].value,100)
 def test_quick_entry_and_evidence(self):
  c=self.client();self.login(c,'totruong')
  self.assertIn('Danh mục nhiệm vụ chuẩn',c.get('/quick?period=1').text)
  template={'department':'1','title':'Nhiệm vụ chuẩn thử','axis':'1','grp':'2','product':'Sản phẩm thử','source':'KH giả lập 02','qty':'3','due':'quarter'}
  self.post(c,'/action/quick_template/1',dict(template,department='2'),'/quick',403)
  self.post(c,'/action/quick_template/1',template,'/quick')
  self.post(c,'/action/quick_evidence/1',{'scope':'team','title':'Biên bản thử của tổ','reference':'BB 02 giả lập','task_title':template['title']},'/quick')
  self.logout(c);self.login(c,'giaovientoan')
  self.assertNotIn('Biên bản thử của tổ',c.get('/quick?period=1').text)
  self.assertNotIn('Nhiệm vụ chuẩn thử',c.get('/eval/5?axis=1').text)
  self.logout(c);self.login(c,'giaovien')
  page=c.get('/eval/1?axis=1').text
  self.assertNotIn('Nhập nhanh công việc',page)
  self.assertIn(template['title'],page)
  self.post(c,'/action/quick_template/1',template,'/quick',403)
  self.post(c,'/action/quick_evidence/1',{'scope':'school','title':'Không hợp lệ','reference':'Mẫu'},'/quick',403)
  ids=re.findall(r'name="tpl_(\d+)"',page)
  self.assertGreaterEqual(len(ids),2)
  self.post(c,'/action/quick_add/1',{'axis':'1',**{'tpl_'+i:'1' for i in ids}},'/eval/1')
  page=c.get('/eval/1?axis=1').text
  self.assertNotIn('CÔNG VIỆC ĐÃ LƯU',page)
  self.assertNotIn('Nhập nhanh công việc',page)
  self.assertNotIn('name="done_',page)
  import re as _re
  tid=None
  for match in _re.finditer(r'<form method="post" action="/action/task/(\d+)".*?</form>',page,_re.S):
   if template['title'] in match.group(0) and 'Biên bản thử của tổ' in match.group(0):
    tid=match.group(1)
    ev=_re.search(r'name="ev_(\d+)"',match.group(0)).group(1)
    break
  self.assertIsNotNone(tid)
  self.post(c,'/action/task/'+tid,{'done':'3','corrections':'0','finish':'quarter','evidence':'','inline_evidence':'1','ev_'+ev:'1'},'/eval/1')
  page=c.get('/eval/1?axis=1').text
  self.assertIn('Biên bản thử của tổ',page)
  self.assertIn('Lưu công việc',page)
  self.post(c,'/action/quick_link/'+tid,{'ev_999999':'1','confirmed':'1'},'/eval/1',403)
  r=c.get('/export/eval/1');self.assertEqual(r.status_code,200)
  w=load_workbook(io.BytesIO(r.content),data_only=True)
  row=next(row for row in w.active.iter_rows() if row[1].value==template['title'])
  self.assertIn('Biên bản thử của tổ',row[18].value)
  self.logout(c);self.login(c,'bangiamhieu')
  self.post(c,'/action/period',{'year':'2026','quarter':'4','mode':'task','confirmed':'1'},'/manage')
  self.logout(c);self.login(c,'giaovien')
  landing=c.get('/').text
  target=re.findall(r'href="/my-period/(\d+)"',landing)[-1]
  self.post(c,'/action/period_start/'+target,{'mode':'new'},'/my-period/'+target)
  path='/eval/'+target
  page=c.get(path+'?axis=1').text
  self.assertNotIn('Nhập nhanh công việc',page)
  self.assertNotIn('name="old_',page)
  self.assertNotIn('Biên bản thử của tổ',page)
  self.assertIn('Nhập thêm công việc',page)
 def test_simple_axis_picker(self):
  c=self.client();self.login(c,'giaovien')
  page=c.get('/eval/1?axis=1').text
  self.assertIn('CHỌN CÁC CÔNG VIỆC ĐÃ THỰC HIỆN',page)
  self.assertLess(page.index('id="axis-picker"'),page.index('class="axis-task-list"'))
  self.assertIn('Nhập thêm công việc',page)
  self.assertNotIn('Điểm tạm tính',page)
  self.assertNotIn('Nhóm 1 · SL 10',page)
  self.assertNotIn('Chọn công việc, kiểm tra thông tin và lưu lần lượt.',page)
  self.assertNotIn('Đã nhập hết công việc của trục?',page)
  ids=re.findall(r'name="sug_([a-f0-9]+)"',page)
  self.assertGreaterEqual(len(ids),2)
  res=self.post(c,'/action/quick_add/1',{'axis':'1','sug_'+ids[0]:'1','sug_'+ids[1]:'1'},'/eval/1')
  self.assertIn('&focus=',res.headers['location'])
  page=c.get(res.headers['location']).text
  tasks=re.findall(r'/action/task/(\d+)',page)
  self.assertEqual(len(tasks),2)
  self.assertEqual(page.count('name="axis-work" open'),1)
  self.assertNotIn('Thông tin nhiệm vụ · Nhóm',page)
  self.assertNotIn('class="work-metadata"',page)
  self.assertIn('class="work-actions"',page)
  self.assertIn('Xóa công việc',page)
  self.assertIn('data-delete-work',page)
  self.post(c,'/action/task/'+tasks[0],{'done':'1','corrections':'0','finish':'quarter','evidence':'Mẫu'},'/eval/1',400)
  title=re.search(r'Công việc 1: ([^<]+)',page).group(1)
  saved=self.post(c,'/action/task/'+tasks[0],{'edit_meta':'1','choice':title,'source':'KH thử','product':'Sản phẩm thử','grp':'1','qty':'1','due':'quarter','done':'1','corrections':'0','finish':'quarter','evidence':'Mẫu','next_after':'1'},'/eval/1')
  self.assertIn('&focus='+tasks[1],saved.headers['location'])
  page=c.get(saved.headers['location']).text
  self.assertIn('Lưu công việc',page)
  self.assertIn('Lưu công việc',page)
  self.assertNotIn('CÔNG VIỆC ĐÃ LƯU',page)
  self.post(c,'/action/axis_next/1',{'axis':'1'},'/eval/1',400)
  self.post(c,'/action/self_delete/'+tasks[1],{},'/eval/1',400)
  self.post(c,'/action/self_delete/'+tasks[1],{'confirmed':'1'},'/eval/1')
  page=c.get('/eval/1?axis=1').text
  self.assertEqual(re.findall(r'/action/task/(\d+)',page),[tasks[0]])
  self.assertNotIn('Chưa nhập công việc',page)
  self.assertNotIn('Cần bổ sung ·',page)
  self.assertNotIn('Thông tin nhiệm vụ · Nhóm',page)
  self.post(c,'/action/axis_next/1',{'axis':'1'},'/eval/1')
 def test_quarter_defaults_and_evidence_files(self):
  c=self.client();self.login(c,'giaovien')
  page=c.get('/eval/1?axis=1').text
  self.assertGreaterEqual(page.count('value="quarter" selected>Quý III/2026'),2)
  self.assertIn('class="evidence-entry"',page)
  self.assertNotIn('Điểm đã lưu: A',page)
  self.assertNotIn('Nhật ký hồ sơ',page)
  self.assertNotIn('Tệp TXT mẫu',page)
  ids=re.findall(r'name="tpl_(\d+)"',page)
  self.assertTrue(ids)
  r=self.post(c,'/action/quick_add/1',{'axis':'1','tpl_'+ids[0]:'1'},'/eval/1')
  page=c.get(r.headers['location']).text
  tid=re.search(r'/action/task/(\d+)',page).group(1)
  self.assertGreaterEqual(page.count('value="quarter" selected>Quý III/2026'),4)
  token=self.csrf(c,'/eval/1?axis=1')
  data={'csrf':token,'done':'1','corrections':'0','finish':'quarter','evidence':''}
  r=c.post('/action/task/'+tid,data=data,files=[('file',('bao-cao.pdf',b'%PDF-1.4 demo','application/pdf')),('file',('minh-chung.zip',b'PK demo','application/zip'))],follow_redirects=False)
  self.assertEqual(r.status_code,303,r.text)
  page=c.get('/eval/1?axis=1').text
  self.assertIn('bao-cao.pdf',page);self.assertIn('minh-chung.zip',page)
  files=re.findall(r'/attachment/(\d+)',page)
  self.assertEqual(len(files),2)
  self.assertEqual(c.get('/attachment/'+files[0]).content,b'%PDF-1.4 demo')
  self.logout(c);self.login(c,'giaovientoan')
  self.assertEqual(c.get('/attachment/'+files[0]).status_code,403)
 def test_metadata_suggestions(self):
  c=self.client();self.login(c,'totruong')
  self.post(c,'/action/quick_evidence/1',{'scope':'team','title':'Quyết định phân công mẫu','reference':'QĐ DEMO 214 (giả lập)','task_title':'Công tác chủ nhiệm lớp'},'/quick')
  self.logout(c);self.login(c,'giaovien')
  page=c.get('/eval/1?axis=1').text
  self.assertIn('data-work-suggestions',page)
  self.assertIn('data-suggest="source"',page)
  self.assertIn('data-suggest="product"',page)
  self.assertIn('QĐ DEMO 214 (giả lập)',page)
  self.assertIn('Hồ sơ, sổ chủ nhiệm',page)
  self.assertIn('Quyết định phân công nhiệm vụ giảng dạy và chủ nhiệm lớp',page)
  self.assertNotIn('Loại văn bản:',page)
  self.assertIn('Biên bản sinh hoạt',page)
  import json,html
  data=json.loads(html.unescape(re.search(r'data-work-suggestions="([^"]+)"',page).group(1)))
  self.assertEqual(data['Công tác chủ nhiệm lớp']['source'][0]['value'],'QĐ DEMO 214 (giả lập)')
  self.assertNotIn('QĐ DEMO 214 (giả lập)',str(data['Soạn kế hoạch bài dạy']))
  self.logout(c);self.login(c,'giaovientoan')
  self.assertNotIn('QĐ DEMO 214 (giả lập)',c.get('/eval/5?axis=1').text)
 def test_compact_suggestions_outstanding(self):
  c=self.client();self.login(c,'giaovien')
  page=c.get('/eval/1?axis=1').text
  self.assertIn('data-suggest-value="source"',page)
  self.assertIn('value="__custom__"',page)
  self.assertIn('name="outstanding" value="0" checked',page)
  self.assertIn('data-outstanding-details hidden',page)
  self.assertNotIn('name="outstanding_evidence"',page)
  self.assertIn('class="evidence-entry outstanding-entry"',page)
  self.assertIn('rows="1" maxlength="2000" data-outstanding-note',page)
  self.assertIn('name="outstanding_file"',page)
  ids=re.findall(r'name="tpl_(\d+)"',page)
  r=self.post(c,'/action/quick_add/1',{'axis':'1','tpl_'+ids[0]:'1'},'/eval/1')
  page=c.get(r.headers['location']).text
  tid=re.search(r'/action/task/(\d+)',page).group(1)
  base={'done':'10','corrections':'0','finish':'quarter','evidence':'Sản phẩm đã thực hiện','outstanding':'1','outstanding_note':'Kết quả cao hơn yêu cầu'}
  self.post(c,'/action/task/'+tid,base,'/eval/1',400)
  self.post(c,'/action/task/'+tid,dict(base,outstanding_evidence='Báo cáo kết quả vượt mức'),'/eval/1')
  page=c.get('/eval/1?axis=1').text
  self.assertIn('name="outstanding" value="1" checked',page)
  r=c.get('/export/eval/1');self.assertEqual(r.status_code,200)
  w=load_workbook(io.BytesIO(r.content),data_only=True)
  self.assertTrue(any('Báo cáo kết quả vượt mức' in str(cell.value) for row in w.active.iter_rows() for cell in row))
  token=self.csrf(c,'/eval/1?axis=1')
  r=c.post('/action/task/'+tid,data={'csrf':token,**base,'outstanding_evidence':''},files={'outstanding_file':('ket-qua.pdf',b'%PDF demo','application/pdf')},follow_redirects=False)
  self.assertEqual(r.status_code,303,r.text)
  page=c.get('/eval/1?axis=1').text
  self.assertIn('ket-qua.pdf',page)
  r=c.get('/export/eval/1');self.assertEqual(r.status_code,200)
  w=load_workbook(io.BytesIO(r.content),data_only=True)
  self.assertTrue(any('Minh chứng vượt yêu cầu:' in str(cell.value) and 'ket-qua.pdf' in str(cell.value) for row in w.active.iter_rows() for cell in row))
  self.post(c,'/action/task/'+tid,dict(base,outstanding='0'),'/eval/1')
  page=c.get('/eval/1?axis=1').text
  self.assertNotIn('name="outstanding" value="1" checked',page)
  self.post(c,'/action/self_delete/'+tid,{'confirmed':'1'},'/eval/1')
  self.assertNotIn('ket-qua.pdf',c.get('/eval/1?axis=1').text)
 def test_period_inheritance(self):
  c=self.client();self.login(c,'giaovien')
  from axis_self import SUGGESTIONS
  old=[]
  for axis in range(1,7):
   title=SUGGESTIONS[axis][0]
   data={'axis':str(axis),'choice':title,'source':'Căn cứ cũ '+str(axis),'product':'Sản phẩm '+str(axis),'grp':'2','qty':'3','due':'quarter','done':'3','corrections':'2','finish':'quarter','evidence':'Minh chứng quý cũ'}
   self.post(c,'/action/self_add/1',data,'/eval/1')
   old.append(re.search(r'/action/task/(\d+)',c.get('/eval/1?axis='+str(axis)).text).group(1))
  self.logout(c);self.login(c,'bangiamhieu')
  self.post(c,'/action/period',{'year':'2026','quarter':'4','mode':'task','confirmed':'1'},'/manage')
  self.logout(c);self.login(c,'giaovien')
  landing=c.get('/').text
  dest=re.findall(r'href="/my-period/(\d+)"',landing)[-1]
  self.assertNotEqual(dest,'1')
  start='/my-period/'+dest
  page=c.get(start).text
  self.assertIn('Kế thừa công việc từ kỳ đánh giá trước',page)
  for tid in old:self.assertRegex(page,r'name="task_'+tid+r'" value="1" checked')
  data={'mode':'copy','source':'1','confirmed':'1',**{'task_'+tid:'1' for tid in old}}
  self.post(c,'/action/period_start/'+dest,dict(data,source='2'),start,403)
  self.post(c,'/action/period_start/'+dest,dict(data,task_999999='1'),start,403)
  r=self.post(c,'/action/period_start/'+dest,data,start)
  self.assertEqual(r.headers['location'],'/eval/'+dest+'?axis=1')
  self.assertEqual(c.get(start,follow_redirects=False).headers['location'],'/eval/'+dest)
  self.post(c,'/action/period_start/'+dest,data,start,409)
  for axis in range(1,7):
   page=c.get('/eval/'+dest+'?axis='+str(axis)).text
   self.assertIn('Công việc 1: '+SUGGESTIONS[axis][0],page)
   self.assertIn('Căn cứ cũ '+str(axis),page)
   self.assertIn('Sản phẩm '+str(axis),page)
   self.assertNotIn('Minh chứng quý cũ',page)
   self.assertRegex(page,r'name="done" type="number" value="1"')
   self.assertRegex(page,r'name="qty" type="number" value="3"')
   self.assertIn('Quý IV/2026',page)
   self.assertNotIn('name="outstanding" value="1" checked',page)
   self.assertNotEqual(re.search(r'/action/task/(\d+)',page).group(1),old[axis-1])
  page=c.get('/eval/'+dest+'?axis=1').text
  tid=re.search(r'/action/task/(\d+)',page).group(1)
  self.post(c,'/action/task/'+tid,{'edit_meta':'1','choice':SUGGESTIONS[1][0],'source':'Căn cứ mới','product':'Sản phẩm mới','grp':'3','qty':'5','due':'quarter','done':'5','corrections':'0','finish':'quarter','evidence':'Minh chứng quý mới'},'/eval/'+dest)
  self.assertIn('Căn cứ mới',c.get('/eval/'+dest+'?axis=1').text)
  self.assertNotIn('Căn cứ mới',c.get('/eval/1?axis=1').text)
  self.assertIn('Minh chứng quý cũ',c.get('/eval/1?axis=1').text)
  self.post(c,'/action/self_delete/'+tid,{'confirmed':'1'},'/eval/'+dest)
  self.assertIn('Công việc 1: '+SUGGESTIONS[1][0],c.get('/eval/1?axis=1').text)
  self.assertNotIn('Công việc 1: '+SUGGESTIONS[1][0],c.get('/eval/'+dest+'?axis=1').text)
  self.logout(c);self.login(c,'giaovientoan')
  self.assertEqual(c.get(start).status_code,403)
if __name__=='__main__':unittest.main(verbosity=2)
