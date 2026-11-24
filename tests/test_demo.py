import os, tempfile, re, sys, io, unittest
from pathlib import Path
TMP=tempfile.TemporaryDirectory()
os.environ['KPI_DEMO_DIR']=TMP.name
os.environ['KPI_HTTPS']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from demo import app, PASS
from fastapi.testclient import TestClient
from openpyxl import load_workbook
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
  self.assertEqual(c.get('/eval/2').status_code,403);self.assertEqual(c.get('/export/eval/2').status_code,403);self.assertEqual(c.get('/manage').status_code,403)
  self.assertIn('Nội dung công việc',c.get('/eval/1?axis=1').text)
  self.assertIn('Không có nhiệm vụ cần nhập',c.get('/eval/1?axis=1').text)
  self.assertIn('Bồi dưỡng học sinh giỏi',c.get('/eval/1?axis=1').text)
  self.assertNotIn('Bồi dưỡng học sinh giỏi',c.get('/eval/1?axis=3').text)
  base={'source':'KH giả lập','product':'Sản phẩm mẫu','grp':'1','qty':'1','due':'2026-09-30','done':'1','corrections':'0','finish':'2026-09-30','evidence':'Minh chứng giả lập'}
  self.post(c,'/action/self_add/2',dict(base,axis='1',choice='Bồi dưỡng học sinh giỏi'),'/eval/1',403)
  self.post(c,'/action/self_add/1',dict(base,axis='3',choice='Bồi dưỡng học sinh giỏi'),'/eval/1',400)
  for axis,title in [('1','Bồi dưỡng học sinh giỏi'),('1','Sinh hoạt chuyên môn'),('3','Ứng dụng công nghệ trong dạy học')]:
   self.post(c,'/action/self_add/1',dict(base,axis=axis,choice=title),'/eval/1')
  self.assertIn('Bồi dưỡng học sinh giỏi',c.get('/eval/1?axis=1').text)
  self.post(c,'/action/self_add/1',dict(base,axis='1',choice='Bồi dưỡng học sinh giỏi'),'/eval/1',400)
  self.post(c,'/action/common/1',{'common':'29'},'/eval/1');self.post(c,'/action/submit/1',{'confirmed':'1'},'/eval/1')
  self.assertIn('Đã nộp',c.get('/eval/1').text);self.assertIn('Bản nháp',other.get('/eval/1').text)
  self.post(c,'/action/common/1',{'common':'30'},'/eval/1',403)
  self.logout(c);self.login(c,'totruong');self.assertEqual(c.get('/eval/5').status_code,403);self.assertEqual(c.get('/export/eval/5').status_code,403)
  self.post(c,'/action/team/1',{'common':'28','note':'Tổ đã rà soát'},'/eval/1')
  self.logout(c);self.login(c,'bangiamhieu');self.assertEqual(c.get('/manage').status_code,200)
  self.post(c,'/action/approve/1',{'common':'28','level':'Hoàn thành tốt nhiệm vụ','note':'BGH duyệt mẫu','confirmed':'1'},'/eval/1')
  self.assertIn('BGH đã duyệt',c.get('/eval/1').text)
  r=c.get('/export/eval/1');self.assertEqual(r.status_code,200); w=load_workbook(io.BytesIO(r.content),data_only=True);self.assertEqual(w.active['R10'].value,70)
  r=c.get('/export/period/1');self.assertEqual(r.status_code,200);w=load_workbook(io.BytesIO(r.content),data_only=True);self.assertEqual(len(w.sheetnames),3)
  self.logout(c);self.login(c,'giaovien');self.assertIn('BGH đã duyệt',c.get('/eval/1').text)
  self.assertIn('Bản nháp',other.get('/eval/1').text)
  self.post(c,'/password',{'old':PASS,'new':'NewPassword!123','confirm':'NewPassword!123'},'/',403)
 def test_sequential_work_cards(self):
  c=self.client();self.login(c,'giaovien')
  base={'source':'KH thử','product':'Sản phẩm thử','grp':'1','qty':'1','due':'2026-09-30','done':'1','corrections':'0','finish':'2026-09-30','evidence':'Minh chứng mẫu'}
  first=self.post(c,'/action/self_add/1',dict(base,axis='1',choice='Bồi dưỡng học sinh giỏi',next_work='1'),'/eval/1')
  self.assertEqual(first.headers['location'],'/eval/1?axis=1&add=1#new-work')
  page=c.get('/eval/1?axis=1&add=1').text
  self.assertIn('Công việc 1: Bồi dưỡng học sinh giỏi',page)
  self.assertIn('Nhập công việc 2',page)
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
