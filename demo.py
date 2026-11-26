"""Disposable, isolated browser workspaces for the Render demo."""
import os, shutil, threading, time, re, secrets
from pathlib import Path
os.environ['KPI_DEMO']='1'
ROOT=Path(os.environ.get('KPI_DEMO_DIR','/tmp/kpi-school-demo')).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
TEMPLATE=ROOT/'template.sqlite3'
os.environ['KPI_DB']=str(TEMPLATE)
from app import app, SECURE
from core import connect, closing, password_hash, normalize, DB_OVERRIDE, LEVELS
from fastapi.responses import PlainTextResponse
from fastapi import Request
LOCK=threading.Lock()
TTL=6*3600
LIMIT=40
PASS='KpiDemo2026!'

def seed():
    with closing(connect()) as c,c:
        if c.execute('SELECT count(*) FROM users').fetchone()[0]:return
        c.executemany('INSERT INTO departments(name) VALUES(?)',[('Tổ Tin học (mẫu)',),('Tổ Toán (mẫu)',)])
        for code, name, login, role, dep, subject in [
            ('ADMIN','Ban Giám hiệu mẫu','bangiamhieu','admin',None,''),
            ('DEMO01','Giáo viên Tin học mẫu','giaovien','teacher',1,'Tin học'),
            ('DEMO02','Tổ trưởng Tin học mẫu','totruong','leader',1,'Tin học'),
            ('DEMO03','Giáo viên Tin học B','giaovien2','teacher',1,'Tin học'),
            ('DEMO04','Giáo viên Tin học C','giaovien3','teacher',1,'Tin học'),
            ('DEMO05','Giáo viên Toán mẫu','giaovientoan','teacher',2,'Toán'),
            ('DEMO06','Tổ trưởng Toán mẫu','totruongtoan','leader',2,'Toán')]:
            c.execute('INSERT INTO users(code,name,login,role,department,subject,cohort,password,must_change) VALUES(?,?,?,?,?,?,?,?,0)',(code,name,normalize(login),role,dep,subject,'Tổ trưởng' if role=='leader' else 'Giáo viên',password_hash(PASS)))
        c.execute('INSERT INTO periods(year,quarter,mode) VALUES(2026,3,"task")')
        c.execute('INSERT INTO evaluations(period,user,department,cohort,common) SELECT 1,id,department,cohort,28 FROM users WHERE code<>"ADMIN"')
        tasks=[('Thực hiện kế hoạch giảng dạy',1,1,'Kế hoạch, sổ đầu bài',10,'2026-09-30'),('Sinh hoạt chuyên môn',1,1,'Biên bản sinh hoạt',4,'2026-09-25'),('Ứng dụng công nghệ trong dạy học',2,3,'Sản phẩm số',2,'2026-09-30')]
        for title,grp,axis,product,qty,due in tasks:
            c.execute('INSERT INTO library(title,grp,axis,product) VALUES(?,?,?,?)',(title,grp,axis,product))
            for e in c.execute('SELECT id,user FROM evaluations WHERE user<>2').fetchall():
                # Primary teacher starts blank and selects tasks; other records illustrate workflow.
                done=qty if e['user']!=2 or axis!=2 else 1
                finish=due if done==qty else None
                c.execute('INSERT INTO tasks(evaluation,title,source,axis,grp,product,qty,due,done,corrections,finish,evidence) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(e['id'],title,'KH DEMO 01 (giả lập)',axis,grp,product,qty,due,done,0,finish,'Minh chứng mẫu, không phải hồ sơ thật'))
        c.execute('UPDATE evaluations SET status="approved",team_common=28,final_common=28,final_level=?,self_level=?,note="Dữ liệu mẫu đã duyệt" WHERE user IN (5,6)',(LEVELS[1],LEVELS[1]))
        # A fully scored fictitious teacher is waiting for the leader in a new demo.
        from common_criteria import DEFAULT,leaves,pack,setup
        from core import calculate,suggestion
        setup(c)
        e=c.execute('SELECT id FROM evaluations WHERE user=4').fetchone()
        eid=e['id'];data=DEFAULT['3'];remaining=2;scores={}
        for key,_,maximum in leaves(data):
            reduction=min(remaining,maximum);remaining-=reduction;scores[key]=maximum-reduction
        common=round(sum(scores.values()),2)
        c.execute('INSERT INTO common_scores(evaluation,appendix,template,scores) VALUES(?,?,?,?)',(eid,'3',pack(data),pack(scores)))
        calc=calculate(c.execute('SELECT * FROM tasks WHERE evaluation=? ORDER BY axis,id',(eid,)).fetchall(),'task',(),'2026-09-30')
        level=suggestion(calc,common)
        import json
        snapshot=json.dumps({'common':common,'calc':calc,'level':level},ensure_ascii=False,default=lambda x:dict(x))
        c.execute('UPDATE evaluations SET status="submitted",common=?,self_level=?,self_snapshot=?,note="" WHERE id=?',(common,level,snapshot,eid))
    with closing(connect()) as c:
        c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
seed()

@app.get('/healthz')
def health():
    return {'status':'ok','mode':'demo'}

@app.middleware('http')
async def workspace(request:Request,call_next):
    if request.url.path=='/healthz' or request.url.path.startswith('/static/'):
        return await call_next(request)
    key=request.cookies.get('kpi_demo_workspace','')
    now=time.time()
    with LOCK:
        path=ROOT/f'{key}.sqlite3' if re.fullmatch(r'[a-f0-9]{48}',key) else None
        if path is None or not path.is_file() or now-path.stat().st_mtime>TTL:
            if request.method not in ('GET','HEAD'):
                return PlainTextResponse('Phiên demo hết hạn. Mở lại trang chủ để bắt đầu.',status_code=409)
            for p in ROOT.glob('*.sqlite3'):
                if p!=TEMPLATE and now-p.stat().st_mtime>TTL:
                    for suffix in ('','-wal','-shm'):
                        Path(str(p)+suffix).unlink(missing_ok=True)
            if len(list(ROOT.glob('*.sqlite3')))>=LIMIT+1:
                return PlainTextResponse('Demo đang đạt giới hạn phiên thử. Vui lòng thử lại sau hoặc triển khai bản demo riêng.',status_code=503)
            key=secrets.token_hex(24);path=ROOT/f'{key}.sqlite3';shutil.copyfile(TEMPLATE,path)
        os.utime(path,None)
    token=DB_OVERRIDE.set(path)
    try:
        response=await call_next(request)
    finally:
        DB_OVERRIDE.reset(token)
    response.set_cookie('kpi_demo_workspace',key,httponly=True,secure=SECURE,samesite='lax',max_age=TTL,path='/')
    return response
