"""Personal export: school KPI layout and a separate common-criteria appendix."""
import re, unicodedata, datetime as dt
import common_criteria as cc
from axis_self import AXES
from core import ROLES, STATUSES, LEVELS, suggestion

ROMAN={1:'I',2:'II',3:'III',4:'IV'}
def filename(prefix,e):
 name=unicodedata.normalize('NFD',e['name']).replace('đ','d').replace('Đ','D')
 name=''.join(ch for ch in name if not unicodedata.combining(ch))
 name=re.sub(r'[^A-Za-z0-9]+','_',name).strip('_') or 'Ca_nhan'
 return f'{prefix}_{name}_Quy_{ROMAN[e["quarter"]]}_{e["year"]}.xlsx'
def formats(w):
 base={'font_name':'Times New Roman','font_size':12,'text_wrap':True,'valign':'vcenter','font_color':'#000000'}
 specs={
 'title':{'bold':True,'font_size':13,'align':'center','border':1},
 'group':{'bold':True,'bg_color':'#F4B183','border':1,'align':'center'},
 'head':{'bold':True,'bg_color':'#FCE4D6','border':1,'align':'center'},
 'index':{'bold':True,'font_size':11,'border':1,'align':'center'},
 'axis':{'bold':True,'font_size':13,'bg_color':'#DDEBF7','border':1},
 'axisnum':{'bold':True,'bg_color':'#DDEBF7','border':1,'num_format':'0.00','align':'center'},
 'body':{'border':1},'center':{'border':1,'align':'center'},
 'num':{'border':1,'align':'center','num_format':'0.00'},
 'pct':{'border':1,'align':'center','num_format':'0.00%'},
 'date':{'border':1,'align':'center','num_format':'dd/mm/yyyy'},
 'total':{'bold':True,'bg_color':'#E2F0D9','font_color':'#C00000','border':1},
 'totalnum':{'bold':True,'bg_color':'#E2F0D9','font_color':'#C00000','border':1,'num_format':'0.00','align':'center'},
 'bold':{'bold':True,'border':1},'section':{'bold':True,'font_size':14},
 'plain':{},'sign':{'bold':True,'font_size':13,'align':'center'},
 'signsub':{'italic':True,'align':'center'}
 }
 return {k:w.add_format(dict(base,**v)) for k,v in specs.items()}
def put(sh,row,col,val,fmt):
 if val is None or val=='':sh.write_blank(row,col,None,fmt)
 elif isinstance(val,str):sh.write_string(row,col,val,fmt)
 else:sh.write(row,col,val,fmt)
def merge(sh,row,a,b,val,fmt):
 sh.merge_range(row,a,row,b,'',fmt);put(sh,row,a,val,fmt)
def page(sh,landscape=True):
 if landscape:sh.set_landscape();sh.set_paper(8)
 else:sh.set_portrait();sh.set_paper(9)
 sh.fit_to_pages(1,0);sh.set_margins(.25,.25,.4,.4);sh.hide_gridlines(2);sh.set_footer('&CTrang &P / &N')
def export_buttons(eid):
 return '<div class="export-actions"><a class="btn secondary" href="/export/common/'+str(eid)+'">Xuất Excel phụ lục chấm</a><a class="btn" href="/export/eval/'+str(eid)+'">Xuất Excel KPI</a></div>'
def common_sheet(w,c,e):
 f=formats(w);sh=w.add_worksheet('Tiêu chí chung');page(sh,False)
 sh.set_column('A:A',11);sh.set_column('B:B',86);sh.set_column('C:D',14);sh.set_column('E:E',25)
 k,data,scores=cc.get(c,e)
 sh.merge_range('A1:E1','PHỤ LỤC '+k+' – KHUNG TIÊU CHÍ ĐÁNH GIÁ',f['title']);sh.set_row(0,30)
 sh.merge_range('A2:E2',cc.NAMES[k].upper(),f['title']);sh.set_row(1,30)
 sh.merge_range('A3:E3','Họ và tên: '+e['name']+' | Quý '+ROMAN[e['quarter']]+'/'+str(e['year'])+' | '+(e['dept'] or 'Chưa phân tổ'),f['plain']);sh.set_row(2,30)
 for col,v in enumerate(['STT','TIÊU CHÍ ĐÁNH GIÁ','ĐIỂM CHUẨN','ĐIỂM TỰ CHẤM','GHI CHÚ']):put(sh,3,col,v,f['head'])
 sh.set_row(3,32);r=4;groups=[]
 for group,items in data:
  gr=r;groups.append(gr+1);merge(sh,r,0,1,group,f['axis']);put(sh,r,2,cc.points(items),f['axisnum']);put(sh,r,4,'',f['axis']);sh.set_row(r,38);r+=1
  start=r+1
  for key,desc,maximum in items:
   for col,val in enumerate([key,desc,maximum,scores.get(key),'']):put(sh,r,col,val,f['body'] if col==1 or col==4 else f['center'])
   sh.set_row(r,max(32,min(150,16*(2+len(desc)//82))));r+=1
  if all(x[0] in scores for x in items):sh.write_formula(gr,3,f'=SUM(D{start}:D{r})',f['axisnum'],sum(scores[x[0]] for x in items))
  else:put(sh,gr,3,None,f['axisnum'])
 merge(sh,r,0,1,'TỔNG ĐIỂM TIÊU CHÍ CHUNG',f['total']);put(sh,r,2,30,f['totalnum'])
 if scores and len(scores)==len(cc.leaves(data)):sh.write_formula(r,3,'='+ '+'.join('D'+str(x) for x in groups),f['totalnum'],sum(scores.values()))
 else:put(sh,r,3,None,f['totalnum'])
 put(sh,r,4,'',f['total']);r+=2
 merge(sh,r,0,4,'Điểm sau rà soát: '+(str(e['final_common']) if e['final_common'] is not None else str(e['team_common']) if e['team_common'] is not None else 'Chưa xác nhận'),f['plain']);r+=1
 if not scores:merge(sh,r,0,4,'Chưa có phiếu chấm chi tiết đã lưu; không suy diễn điểm từng tiêu chí từ điểm tổng cũ.',f['plain']);sh.set_row(r,32);r+=1
 r+=1;merge(sh,r,0,1,'CÁ NHÂN TỰ ĐÁNH GIÁ',f['sign']);merge(sh,r,2,4,'NGƯỜI ĐÁNH GIÁ',f['sign']);r+=1;merge(sh,r,0,1,'(Ký, ghi rõ họ tên)',f['signsub']);merge(sh,r,2,4,'(Ký, ghi rõ họ tên)',f['signsub']);sh.set_row(r+1,65)
 sh.freeze_panes(4,2);sh.repeat_rows(3);sh.print_area(0,0,r+1,4)
 return k
def kpi_sheet(w,c,e,calc,hide_evidence=False):
 f=formats(w);sh=w.add_worksheet('CONG CHUC');page(sh)
 for j,width in enumerate([4,82,13.4,6.7,43,6,10.6,11,7.4,8.4,7.1,5.6,13.8,5.6,10,9,7,10.5,32]):sh.set_column(j,j,width)
 sh.set_column('T:T',4);sh.set_column('U:U',12,None,{'hidden':True})
 role=c.execute('SELECT role FROM users WHERE id=?',(e['user'],)).fetchone()['role']
 title='PHỤ LỤC 2\nNHIỆM VỤ SẢN PHẨM CÔNG VIỆC CÁ NHÂN CHUẨN QUÝ '+ROMAN[e['quarter']]+' NĂM '+str(e['year'])+'\nHọ và tên: '+e['name']+'\nChức vụ, đơn vị công tác: '+ROLES.get(role,role)+' - '+(e['dept'] or 'Chưa phân tổ')+' - Trường THPT Chuyên Trần Hưng Đạo\nTrên cơ sở chương trình, kế hoạch công tác của cơ quan, đơn vị và vị trí, chức danh, nhiệm vụ được giao, cá nhân xác định mục tiêu, nhiệm vụ, sản phẩm công việc trong quý như sau:\nKẾT QUẢ THỰC HIỆN NHIỆM VỤ ĐƯỢC GIAO (/70 điểm)'
 merge(sh,0,0,18,title,f['title']);sh.set_row(0,110)
 merge(sh,1,0,7,'Danh mục nhiệm vụ được duyệt + Nhiệm vụ phát sinh',f['group']);merge(sh,1,8,17,'Kết quả thực hiện',f['group']);sh.merge_range(1,18,3,18,'Ghi chú',f['head']);sh.set_row(1,30)
 heads={0:'TT',1:'Nhiệm vụ được giao',2:'Phân nhóm (Độ khó, mới, phức tạp; phạm vi tác động)',3:'Điểm chấm nhiệm vụ',4:'Sản phẩm cụ thể',5:'Số lượng',6:'Thời hạn hoàn thành',7:'Điểm chấm',14:'Tổng điểm chấm thực tế',15:'Điểm KPI (%)',16:'Điểm tối đa',17:'Điểm đạt'}
 for col,txt in heads.items():sh.merge_range(2,col,3,col,txt,f['head'])
 for a,b,txt in [(8,9,'Số lượng (A)'),(10,11,'Chất lượng (B)'),(12,13,'Tiến độ (C)')]:merge(sh,2,a,b,txt,f['head'])
 for j,txt in enumerate(['Thực tế hoàn thành','Điểm chấm','Số lần yêu cầu chỉnh sửa (mỗi lần trừ 5%)','Điểm chấm','Ngày hoàn thành (trễ 01 ngày làm việc trừ 5%)','Điểm chấm'],8):put(sh,3,j,txt,f['head'])
 sh.set_row(2,33);sh.set_row(3,125)
 for j in range(19):put(sh,4,j,{7:'(8)=(4)*(6)' if e['mode']=='product' else '(8)=(4)',9:'(10)=(8)*(9)',14:'(15)=(10+12+14)/3',17:'(18)=16*17'}.get(j,'('+str(j+1)+')'),f['index'])
 sh.set_row(4,32)
 grouped={i:[] for i in range(1,7)}
 for t,z in calc['rows']:grouped[t['axis']].append((t,z))
 r=5;axisrows=[]
 for axis,items in grouped.items():
  ar=r;ax=ar+1;axisrows.append(ax);r+=1
  base=sum(z['base'] for t,z in items);earned=sum(z['kpi'] for t,z in items);weight=sum(z['max'] for t,z in items)
  merge(sh,ar,0,6,'TRỤC ('+str(axis)+') '+AXES[axis][0],f['axis']);sh.set_row(ar,38)
  sh.write_formula(ar,7,f'=SUM(H{r+1}:H{r+len(items)})' if items else '=0',f['axisnum'],base)
  merge(sh,ar,8,15,'Không có nhiệm vụ' if not items else '',f['axis'])
  sh.write_formula(ar,16,f'=IFERROR(H{ax}/$U$6*70,0)',f['axisnum'],weight)
  sh.write_formula(ar,17,f'=SUM(R{r+1}:R{r+len(items)})' if items else '=0',f['axisnum'],earned);put(sh,ar,18,'',f['axis'])
  for j,(t,z) in enumerate(items,1):
   rr=r+1;note='Căn cứ: '+t['source']+('' if hide_evidence else '; Minh chứng: '+(t['evidence'] or ''))+'; Chậm chủ quan: '+str(z['late'])+' ngày làm việc'
   if t['outstanding_note']:note+='; '+t['outstanding_note']
   if t['cancelled']:note+='; Dừng: '+t['cancel_reason']
   vals=[j,t['title'],'Nhóm '+str(t['grp'])+' ('+str(50+t['grp']*50)+'đ)',50+t['grp']*50,t['product'],t['qty'],None,None,z['ratio'] if t['done'] is not None else None,None,t['corrections'],None,None,None,None,None,None,None,note]
   for col,val in enumerate(vals):put(sh,r,col,val,f['body'] if col in (1,4,18) else f['center'])
   for col,val in [(6,t['effective_due'] or t['due']),(12,t['finish'])]:
    if val:
     from axis_self import date_label
     label=date_label(e,val)
     if label.startswith('Quý '):sh.write(r,col,label,f['center'])
     else:sh.write_datetime(r,col,dt.datetime.fromisoformat(val),f['date'])
   put(sh,r,8,vals[8],f['pct'])
   h='H'+str(rr);jcell='J'+str(rr)
   sh.write_formula(r,7,'=0' if t['cancelled'] else f'=D{rr}'+(f'*F{rr}' if e['mode']=='product' else ''),f['num'],z['base'])
   sh.write_formula(r,9,f'={h}*I{rr}',f['num'],z['a'])
   b=f'MAX(0,{h}*(1-5%*K{rr}))'; b=f'MIN({jcell},{b})' if z['ratio']<1 else b
   cf=f'MAX(0,{h}*(1-5%*{z["late"]}))';cf=f'MIN({jcell},{cf})' if z['ratio']<1 and not t['finish'] else cf
   sh.write_formula(r,11,'='+b,f['num'],z['b']);sh.write_formula(r,13,'='+cf,f['num'],z['c'])
   sh.write_formula(r,14,f'=AVERAGE(J{rr},L{rr},N{rr})',f['num'],z['actual'])
   sh.write_formula(r,15,f'=IFERROR(O{rr}/$H${ax},0)',f['pct'],z['actual']/base if base else 0)
   sh.write_formula(r,16,f'=$Q${ax}',f['num'],weight)
   sh.write_formula(r,17,f'=P{rr}*Q{rr}',f['num'],z['kpi'])
   sh.set_row(r,max(34,min(95,15*(2+max(len(t['title'])//78,len(t['product'])//39,len(note)//32)))));r+=1
 sh.write_formula('U6','='+ '+'.join('H'+str(x) for x in axisrows),f['num'],calc['base'])
 total=r+1;merge(sh,r,0,15,'TỔNG ĐIỂM PHẦN B - KẾT QUẢ THỰC HIỆN NHIỆM VỤ ĐƯỢC GIAO',f['total']);sh.write_formula(r,16,'='+ '+'.join('Q'+str(x) for x in axisrows),f['totalnum'],70 if calc['base'] else 0);sh.write_formula(r,17,'='+ '+'.join('R'+str(x) for x in axisrows),f['totalnum'],calc['kpi']);put(sh,r,18,'',f['total']);sh.set_row(r,32);r+=1
 for line in ['(1) Tổng điểm tối đa 06 trục là 70 khi có nhiệm vụ hợp lệ. Trục không có nhiệm vụ có trọng số 0.','(2) Điểm chuẩn theo nhóm và quy tắc trọng số của kỳ: '+e['mode']+'.','(3) Điểm A, B, C và số ngày chậm lấy theo hồ sơ đã lưu. Không làm tròn trọng số từng trục để bảo toàn tổng điểm 70.']:
  merge(sh,r,0,18,line,f['plain']);sh.set_row(r,24);r+=1
 r+=1;merge(sh,r,1,3,'Tổng điểm chuẩn toàn bộ nhiệm vụ:',f['plain']);sh.write_formula(r,4,'=U6',f['num'],calc['base']);merge(sh,r,7,9,'Tổng điểm KPI quy đổi:',f['plain']);sh.write_formula(r,10,f'=R{total}',f['num'],calc['kpi']);sh.set_row(r,30)
 r+=2;merge(sh,r,0,18,'II. TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ CÁ NHÂN',f['section']);r+=1
 for a,b,v in [(0,4,'Nội dung'),(5,8,'Điểm tối đa'),(9,13,'Cá nhân tự chấm'),(14,18,'Điểm sau rà soát')]:merge(sh,r,a,b,v,f['head'])
 r+=1
 self_common=e['common'];review=e['final_common'] if e['final_common'] is not None else e['team_common'];common_row=r+1;kpi_row=r+2
 for label,maximum,own,checked in [('Nhóm tiêu chí chung theo biểu mẫu của cơ quan Đảng',30,self_common,review),('Kết quả thực hiện nhiệm vụ theo KPI',70,calc['kpi'],calc['kpi'] if review is not None else None)]:
  for a,b,v in [(0,4,label),(5,8,maximum),(9,13,own),(14,18,checked)]:merge(sh,r,a,b,v,f['body'] if a==0 else f['num'])
  if maximum==70:sh.write_formula(r,9,f'=R{total}',f['num'],calc['kpi'])
  sh.set_row(r,32);r+=1
 for a,b,v in [(0,4,'TỔNG ĐIỂM'),(5,8,100),(9,13,None),(14,18,None)]:merge(sh,r,a,b,v,f['bold'])
 if self_common is not None:sh.write_formula(r,9,f'=SUM(J{common_row}:J{kpi_row})',f['num'],self_common+calc['kpi'])
 if review is not None:sh.write_formula(r,14,f'=SUM(O{common_row}:O{kpi_row})',f['num'],review+calc['kpi'])
 r+=2;merge(sh,r,0,18,'III. TỰ ĐỀ XUẤT MỨC XẾP LOẠI',f['section']);r+=1
 for a,b,v in [(1,3,'Mức xếp loại'),(4,11,'Khung điểm và điều kiện'),(12,16,'Cá nhân tự đề xuất')]:merge(sh,r,a,b,v,f['head'])
 level=e['self_level'] or suggestion(calc,self_common)
 for lev,cond in zip(LEVELS,['Từ 90 điểm trở lên và đáp ứng đầy đủ điều kiện kèm theo','Từ 70 đến dưới 90 điểm và đáp ứng điều kiện của mức xếp loại','Từ 50 đến dưới 70 điểm và đáp ứng điều kiện của mức xếp loại','Dưới 50 điểm hoặc thuộc trường hợp phải xếp loại không hoàn thành']):
  r+=1
  for a,b,v in [(1,3,lev),(4,11,cond),(12,16,'X' if lev==level else '')]:merge(sh,r,a,b,v,f['body'] if a!=12 else f['center'])
  sh.set_row(r,32)
 r+=2;merge(sh,r,0,18,'Kết quả, sản phẩm nổi trội hoặc vượt mức yêu cầu: '+(' ; '.join(t['outstanding_note'] for t,z in calc['rows'] if t['outstanding'] and t['outstanding_note'] and not t['cancelled']) or 'Chưa có nội dung đã lưu'),f['plain']);sh.set_row(r,60)
 r+=1;merge(sh,r,0,18,'Trạng thái: '+STATUSES[e['status']]+' | Xếp loại chính thức: '+(e['final_level'] or 'Chưa xác nhận'),f['plain'])
 r+=2
 for a,b,v in [(0,4,'CÁ NHÂN TỰ ĐÁNH GIÁ'),(5,11,'NGƯỜI TRỰC TIẾP NHẬN XÉT, ĐỀ XUẤT'),(12,18,'NGƯỜI CÓ THẨM QUYỀN XÁC NHẬN')]:merge(sh,r,a,b,v,f['sign']);merge(sh,r+1,a,b,'(Ký, ghi rõ họ tên)',f['signsub'])
 sh.set_row(r,32);sh.set_row(r+2,70);sh.freeze_panes(5,2);sh.repeat_rows(1,4);sh.print_area(0,0,r+2,18)
