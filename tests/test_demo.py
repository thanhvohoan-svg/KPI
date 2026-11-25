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
  self.assertIn('Đã nộp',c.get('/eval/1').text);self.assertIn('Bản nháp',other.get('/eval/1').text)
  self.post(c,'/action/common/1',{'common':'30'},'/eval/1',403)
  self.logout(c);self.login(c,'totruong');self.assertEqual(c.get('/eval/5').status_code,403);self.assertEqual(c.get('/export/eval/5').status_code,403)
  self.post(c,'/action/team/1',{'common':'28','note':'Tổ đã rà soát'},'/eval/1')
  self.logout(c);self.login(c,'bangiamhieu');self.assertEqual(c.get('/manage').status_code,200)
  self.post(c,'/action/approve/1',{'common':'28','level':'Hoàn thành tốt nhiệm vụ','note':'BGH duyệt mẫu','confirmed':'1'},'/eval/1')
  self.assertIn('BGH đã duyệt',c.get('/eval/1').text)
  r=c.get('/export/eval/1');self.assertEqual(r.status_code,200); w=load_workbook(io.BytesIO(r.content),data_only=True);self.assertEqual(w.sheetnames,['CONG CHUC']);total=next(row for row in w.active.iter_rows() if str(row[0].value).startswith('TỔNG ĐIỂM PHẦN B'));self.assertAlmostEqual(total[17].value,70);self.assertAlmostEqual(total[16].value,70);self.assertIn('KPI_',r.headers['content-disposition'])
  r=c.get('/export/common/1');self.assertEqual(r.status_code,200);w=load_workbook(io.BytesIO(r.content),data_only=True);self.assertEqual(w.sheetnames,['Tiêu chí chung']);total=next(row for row in w.active.iter_rows() if row[0].value=='TỔNG ĐIỂM TIÊU CHÍ CHUNG');self.assertEqual(total[3].value,29);self.assertIn('Phu_luc_3_cham_',r.headers['content-disposition'])
  r=c.get('/export/period/1');self.assertEqual(r.status_code,200);w=load_workbook(io.BytesIO(r.content),data_only=True);self.assertEqual(len(w.sheetnames),3)
  self.logout(c);self.login(c,'giaovien');self.assertIn('BGH đã duyệt',c.get('/eval/1').text)
  self.assertIn('Bản nháp',other.get('/eval/1').text)
  self.post(c,'/password',{'old':PASS,'new':'NewPassword!123','confirm':'NewPassword!123'},'/',403)
 def test_compact_teacher_home(self):
  c=self.client();self.login(c,'giaovien')
  landing=c.get('/',follow_redirects=False)
  self.assertEqual(landing.status_code,303)
  self.assertEqual(landing.headers['location'],'/eval/1')
  page=c.get('/').text
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
  c=self.client();self.login(c,'totruong')
  personal=c.get('/?period=1&view=self')
  self.assertEqual(personal.status_code,200)
  self.assertIn('ĐÁNH GIÁ CÁ NHÂN',personal.text)
  self.assertIn('ĐÁNH GIÁ TỔ VIÊN',personal.text)
  self.assertIn('href="/eval/2"',personal.text)
  self.assertNotIn('href="/eval/1"',personal.text)
  team=c.get('/?period=1&view=team')
  self.assertIn('href="/eval/1"',team.text)
  self.assertNotIn('href="/eval/2"',team.text)
  self.assertNotIn('href="/eval/5"',team.text)
  self.assertIn('QUY TRÌNH LUÂN CHUYỂN HỒ SƠ',c.get('/eval/2').text)
  self.assertIn('workflow-step current',c.get('/eval/1').text)
 def test_sequential_work_cards(self):
  c=self.client();self.login(c,'giaovien')
  base={'source':'KH thử','product':'Sản phẩm thử','grp':'1','qty':'1','due':'2026-09-30','done':'1','corrections':'0','finish':'2026-09-30','evidence':'Minh chứng mẫu'}
  first=self.post(c,'/action/self_add/1',dict(base,axis='1',choice='Bồi dưỡng học sinh giỏi',next_work='1'),'/eval/1')
  self.assertEqual(first.headers['location'],'/eval/1?axis=1&add=1#new-work')
  page=c.get('/eval/1?axis=1&add=1').text
  self.assertIn('Công việc 1: Bồi dưỡng học sinh giỏi',page)
  self.assertIn('Nhập công việc 2',page)
  self.assertEqual(page.count('class="panel axis-workspace"'),1)
  self.assertIn('class="axis-intro"',page)
  self.assertIn('class="axis-progress"',page)
  self.assertIn('class="new-work-panel"',page)
  self.assertNotIn('class="panel new-work-panel"',page)
  self.assertIn('<details class="task work-card" name="axis-work">',page)
  self.assertIn('<details class="new-work" name="axis-work" open>',page)
  self.post(c,'/action/self_add/1',dict(base,axis='1',choice='Sinh hoạt chuyên môn',next_work='0'),'/eval/1')
  page=c.get('/eval/1?axis=1').text
  self.assertIn('Công việc 1: Bồi dưỡng học sinh giỏi',page)
  self.assertIn('Công việc 2: Sinh hoạt chuyên môn',page)
  self.assertIn('Nhập công việc 3',page)
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
if __name__=='__main__':unittest.main(verbosity=2)
