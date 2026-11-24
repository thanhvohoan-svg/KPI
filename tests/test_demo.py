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
  self.post(c,'/action/task/13',{'done':'2','corrections':'0','finish':'2026-09-30','evidence':'Minh chứng giả lập'},'/eval/1')
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
if __name__=='__main__':unittest.main(verbosity=2)
