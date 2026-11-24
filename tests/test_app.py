import os,sys,tempfile,re,io,unittest
from pathlib import Path
TMP=tempfile.TemporaryDirectory();os.environ['KPI_DB']=str(Path(TMP.name)/'test.sqlite3');sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import app
from core import *
from fastapi.testclient import TestClient
from openpyxl import load_workbook
class AppTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with closing(connect()) as c, c:
   c.execute('INSERT INTO departments(name) VALUES(?)',('Tổ Toán',));c.execute('INSERT INTO departments(name) VALUES(?)',('Tổ Văn',))
   for code,name,role,dep in [('ADMIN','Quản trị thử','admin',None),('T1','Giáo viên A','teacher',1),('T2','Giáo viên B','teacher',2),('L1','Tổ trưởng A','leader',1)]:
    c.execute('INSERT INTO users(code,name,login,role,department,password,must_change) VALUES(?,?,?,?,?,?,?)',(code,name,normalize(name),role,dep,password_hash('0900000001'),int(code=='T1')))
 def token(self,client,url='/'):
  r=client.get(url);m=re.search(r'name="csrf" value="([^"]+)"',r.text);self.assertIsNotNone(m,r.text[:300]);return m.group(1)
 def login(self,name,change=False):
  cl=TestClient(app);tok=self.token(cl,'/login');r=cl.post('/login',data={'csrf':tok,'name':name,'password':'0900000001'},follow_redirects=False);self.assertEqual(r.status_code,303)
  if change:
   self.assertEqual(r.headers['location'],'/password');self.assertEqual(cl.get('/manage',follow_redirects=False).headers['location'],'/password');r=cl.post('/password',data={'csrf':self.token(cl,'/password'),'old':'0900000001','new':'MatKhauMoi123!','confirm':'MatKhauMoi123!'},follow_redirects=False);self.assertEqual(r.status_code,303,r.text)
  return cl
 def post(self,cl,path,data,source='/',code=303):
  r=cl.post(path,data={'csrf':self.token(cl,source),**data},follow_redirects=False);self.assertEqual(r.status_code,code,r.text[:500]);return r
 def test_01_formula(self):
  t=dict(grp=2,qty=4,cancelled=0,done=3,corrections=2,finish=None,due='2026-09-25',effective_due=None,late_override=None,evidence='Biên bản',outstanding=0,outstanding_note='');z=score_task(t,'task',['2026-09-28'],'2026-09-30');self.assertEqual(z['base'],150);self.assertEqual(z['late'],2);self.assertEqual(z['a'],112.5);self.assertEqual(z['b'],112.5);self.assertEqual(z['c'],112.5);self.assertEqual(score_task(t,'product')['base'],600);self.assertEqual(quota(3),1);self.assertEqual(quota(2),0)
 def test_02_full_workflow(self):
  admin=self.login('Quản trị thử');a=self.login('Giáo viên A',True);b=self.login('Giáo viên B');leader=self.login('Tổ trưởng A')
  self.post(admin,'/action/period',{'year':'2026','quarter':'3','mode':'task','confirmed':'1'},'/manage')
  with closing(connect()) as c, c:
   p=c.execute('SELECT id FROM periods').fetchone()[0];es={x['code']:x['id'] for x in c.execute('SELECT e.id,u.code FROM evaluations e JOIN users u ON e.user=u.id')};eid=es['T1'];other=es['T2']
  self.post(leader,f'/action/assign/{p}',{'title':'Giảng dạy','source':'KH 01','axis':'1','grp':'1','product':'Sổ đầu bài','qty':'4','due':'2026-09-30','target':'selected',f'e_{eid}':'1'},'/assign')
  with closing(connect()) as c, c:tid=c.execute('SELECT id FROM tasks WHERE evaluation=?',(eid,)).fetchone()[0]
  self.assertEqual(b.get(f'/eval/{eid}').status_code,403);self.assertEqual(leader.get(f'/eval/{other}').status_code,403);self.assertEqual(b.get(f'/export/eval/{eid}').status_code,403)
  self.post(b,f'/action/task/{tid}',{'done':'4','corrections':'0'},code=403)
  self.assertEqual(a.post(f'/action/common/{eid}',data={'common':28}).status_code,403)
  self.post(a,f'/action/task/{tid}',{'done':'4','corrections':'0','finish':'2026-09-29','evidence':'Sổ đầu bài'},f'/eval/{eid}')
  upload=a.post(f'/action/upload/{tid}',data={'csrf':self.token(a,f'/eval/{eid}')},files={'file':('test.txt',b'check','text/plain')},follow_redirects=False);self.assertEqual(upload.status_code,303)
  with closing(connect()) as c, c:aid=c.execute('SELECT id FROM attachments').fetchone()[0]
  self.assertEqual(b.get(f'/attachment/{aid}').status_code,403);self.assertEqual(a.get(f'/attachment/{aid}').content,b'check')
  self.post(a,f'/action/common/{eid}',{'common':'28'},f'/eval/{eid}');self.post(a,f'/action/submit/{eid}',{'confirmed':'1'},f'/eval/{eid}')
  self.post(a,f'/action/common/{eid}',{'common':'30'},f'/eval/{eid}',403)
  self.post(admin,f'/action/approve/{eid}',{'common':'28','level':LEVELS[1],'note':'Duyệt','confirmed':'1'},f'/eval/{eid}',400)
  self.post(leader,f'/action/team/{eid}',{'common':'27','note':'Đã kiểm tra'},f'/eval/{eid}')
  self.post(admin,f'/action/approve/{eid}',{'common':'27','level':LEVELS[0],'note':'Không đủ điều kiện','confirmed':'1'},f'/eval/{eid}',400)
  self.post(admin,f'/action/approve/{eid}',{'common':'27','level':LEVELS[1],'note':'Đã kiểm tra','confirmed':'1'},f'/eval/{eid}')
  r=a.get(f'/export/eval/{eid}');self.assertEqual(r.status_code,200);w=load_workbook(io.BytesIO(r.content),data_only=True);sh=w.active;self.assertEqual(sh['R7'].value,70);self.assertEqual(sh['R8'].value,70);self.assertEqual(sh['H7'].value,100)
  r=leader.get(f'/export/period/{p}');self.assertEqual(r.status_code,200);w=load_workbook(io.BytesIO(r.content),data_only=True);self.assertEqual(len(w.sheetnames),3);self.assertNotIn('Giáo viên B',[x.value for row in w.worksheets[0] for x in row]);self.assertEqual(a.get(f'/export/period/{p}').status_code,403)
  self.post(admin,f'/action/lock/{p}',{'confirmed':'1'},f'/period/{p}',400)
  self.post(admin,f'/action/reopen/{eid}',{'note':'Kiểm tra lại'},f'/eval/{eid}');self.post(a,f'/action/common/{eid}',{'common':'28'},f'/eval/{eid}')
if __name__=='__main__':unittest.main(verbosity=2)
