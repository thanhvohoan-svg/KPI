import datetime as dt, hashlib, hmac, math, re, secrets, sqlite3, unicodedata, os
from pathlib import Path
from contextlib import closing
from contextvars import ContextVar
DB=Path(os.environ.get('KPI_DB',str(Path(__file__).parent/'data'/'kpi.sqlite3')))
DB_OVERRIDE=ContextVar('kpi_db_override',default=None)
ROLES={'teacher':'Giáo viên','deputy':'Tổ phó','leader':'Tổ trưởng','manager':'Ban Giám hiệu','admin':'Quản trị viên'}
STATUSES={'draft':'Bản nháp','submitted':'Đã nộp','returned':'Trả lại','team':'Tổ đã duyệt','approved':'BGH đã duyệt'}
LEVELS=['Hoàn thành xuất sắc nhiệm vụ','Hoàn thành tốt nhiệm vụ','Hoàn thành nhiệm vụ','Không hoàn thành nhiệm vụ']
SCHEMA='''
CREATE TABLE IF NOT EXISTS departments(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, login TEXT UNIQUE NOT NULL, subject TEXT DEFAULT '', department INTEGER REFERENCES departments(id), cohort TEXT DEFAULT 'Giáo viên', role TEXT NOT NULL DEFAULT 'teacher', password TEXT NOT NULL, must_change INTEGER DEFAULT 1, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS periods(id INTEGER PRIMARY KEY, year INTEGER NOT NULL, quarter INTEGER NOT NULL, mode TEXT NOT NULL, locked INTEGER DEFAULT 0, UNIQUE(year,quarter));
CREATE TABLE IF NOT EXISTS holidays(period INTEGER REFERENCES periods(id), day TEXT, PRIMARY KEY(period,day));
CREATE TABLE IF NOT EXISTS evaluations(id INTEGER PRIMARY KEY, period INTEGER NOT NULL REFERENCES periods(id), user INTEGER NOT NULL REFERENCES users(id), department INTEGER REFERENCES departments(id), cohort TEXT NOT NULL, status TEXT DEFAULT 'draft', common REAL, self_snapshot TEXT, self_level TEXT, team_common REAL, final_common REAL, final_level TEXT, note TEXT DEFAULT '', UNIQUE(period,user));
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, evaluation INTEGER NOT NULL REFERENCES evaluations(id), title TEXT NOT NULL, source TEXT NOT NULL, axis INTEGER NOT NULL, grp INTEGER NOT NULL, product TEXT NOT NULL, qty INTEGER NOT NULL, due TEXT NOT NULL, effective_due TEXT, extension_reason TEXT DEFAULT '', done INTEGER, corrections INTEGER, finish TEXT, late_override INTEGER, late_reason TEXT DEFAULT '', evidence TEXT DEFAULT '', outstanding INTEGER DEFAULT 0, outstanding_note TEXT DEFAULT '', cancelled INTEGER DEFAULT 0, cancel_reason TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS team_section_reviews(evaluation INTEGER NOT NULL REFERENCES evaluations(id),part TEXT NOT NULL CHECK(part IN ('common','kpi')),actor INTEGER NOT NULL REFERENCES users(id),score REAL,note TEXT NOT NULL DEFAULT '',at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(evaluation,part));
CREATE TABLE IF NOT EXISTS attachments(id INTEGER PRIMARY KEY, task INTEGER NOT NULL REFERENCES tasks(id), filename TEXT NOT NULL, body BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user INTEGER REFERENCES users(id), csrf TEXT NOT NULL, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS attempts(key TEXT PRIMARY KEY, count INTEGER NOT NULL, until INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, at TEXT DEFAULT CURRENT_TIMESTAMP, actor INTEGER REFERENCES users(id), action TEXT, evaluation INTEGER, detail TEXT);
CREATE TABLE IF NOT EXISTS library(id INTEGER PRIMARY KEY, title TEXT UNIQUE NOT NULL, grp INTEGER NOT NULL, axis INTEGER NOT NULL, product TEXT NOT NULL);
'''
def connect():
 path=DB_OVERRIDE.get() or DB
 path.parent.mkdir(parents=True,exist_ok=True)
 c=sqlite3.connect(path, timeout=15); c.row_factory=sqlite3.Row
 c.execute('PRAGMA foreign_keys=ON'); c.execute('PRAGMA journal_mode=WAL'); return c
def init():
 with closing(connect()) as c, c: c.executescript(SCHEMA)
def normalize(s): return ' '.join(unicodedata.normalize('NFC',str(s)).casefold().split())
def password_hash(s):
 salt=secrets.token_hex(16); return salt+'$'+hashlib.pbkdf2_hmac('sha256',s.encode(),bytes.fromhex(salt),600000).hex()
def check_password(s,stored):
 try:
  salt,expected=stored.split('$'); return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',s.encode(),bytes.fromhex(salt),600000).hex(),expected)
 except (ValueError,TypeError): return False
def token_hash(s): return hashlib.sha256(s.encode()).hexdigest()
def audit(c,u,action,e=None,detail=''): c.execute('INSERT INTO audit(actor,action,evaluation,detail) VALUES(?,?,?,?)',(u,action,e,detail))
def end_of_quarter(year,q):
 import calendar
 m=q*3; return dt.date(year,m,calendar.monthrange(year,m)[1])
def working_days(start,end,holidays=()):
 start=dt.date.fromisoformat(start) if isinstance(start,str) else start; end=dt.date.fromisoformat(end) if isinstance(end,str) else end
 holidays=set(holidays); return sum((start+dt.timedelta(days=i)).weekday()<5 and (start+dt.timedelta(days=i)).isoformat() not in holidays for i in range(1,max(0,(end-start).days)+1))
def score_task(t,mode='task',holidays=(),cutoff=None):
 t=dict(t); p=50+50*t['grp']; base=p*(t['qty'] if mode=='product' else 1)
 if t['cancelled']: return dict(base=0,a=0,b=0,c=0,actual=0,late=0,ratio=0,ready=True,complete=False)
 ready=t['done'] is not None and t['corrections'] is not None
 done=t['done'] or 0; finish=t['finish']; ratio=min(1,done/t['qty']); due=t['effective_due'] or t['due']
 end=finish or cutoff or due
 late=t['late_override'] if t['late_override'] is not None else working_days(due,end,holidays)
 a=base*ratio; b=base*max(0,1-.05*(t['corrections'] or 0))
 # Conservative cap for unfinished product; approved local interpretation required.
 if ratio<1: b=min(b,a)
 c=base*max(0,1-.05*late)
 if ratio<1 and not finish: c=min(c,a)
 complete=ratio==1 and bool(finish) and (not cutoff or finish<=cutoff)
 ready=ready and (ratio<1 or bool(finish))
 return dict(base=base,a=a,b=b,c=c,actual=(a+b+c)/3,late=late,ratio=ratio,ready=ready,complete=complete)
def calculate(tasks,mode='task',holidays=(),cutoff=None):
 rows=[(dict(t),score_task(t,mode,holidays,cutoff)) for t in tasks]; base=sum(s['base'] for _,s in rows); actual=sum(s['actual'] for _,s in rows)
 active=[(t,s) for t,s in rows if s['base']]; n=len(active); outstanding=sum(bool(t['outstanding'] and t['outstanding_note'] and t['evidence'] and t.get('outstanding_proof',t['evidence']) and s['complete'] and s['late']==0) for t,s in active)
 for t,s in rows: s['max']=70*s['base']/base if base else 0; s['kpi']=70*s['actual']/base if base else 0
 return dict(rows=rows,base=base,kpi=70*actual/base if base else 0,n=n,outstanding=outstanding,late=sum(not s['complete'] or s['late']>0 for _,s in active),ready=bool(n) and all(s['ready'] and t['evidence'] and (not t['outstanding'] or (t['outstanding_note'] and t.get('outstanding_proof',t['evidence']))) for t,s in active),all_complete=bool(n) and all(s['complete'] and s['late']==0 for _,s in active))
def eligible_xs(calc,common): return common is not None and common+calc['kpi']>=90-1e-8 and calc['all_complete'] and calc['outstanding']*10>=calc['n']*3 and calc['ready']
def suggestion(calc,common):
 if common is None or not calc['n']: return 'Chưa đủ dữ liệu'
 total=common+calc['kpi']; return LEVELS[0] if eligible_xs(calc,common) else LEVELS[1] if total>=70-1e-8 else LEVELS[2] if total>=50-1e-8 else LEVELS[3]
def quota(n): return (int(n)+2)//5
