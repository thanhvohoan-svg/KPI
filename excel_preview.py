"""Read-only HTML previews of the actual generated Excel workbooks."""
from datetime import date, datetime
from html import escape
from openpyxl import load_workbook
import personal_exports as pe

def value_text(cell):
 v=cell.value
 if v is None:return ''
 if isinstance(v,(datetime,date)):return v.strftime('%d/%m/%Y')
 if isinstance(v,(int,float)) and not isinstance(v,bool):
  if '%' in cell.number_format:return f'{v:.2%}'
  if '0.00' in cell.number_format:return f'{v:.2f}'
  return str(v)
 return str(v)

def color(c):
 return str(c.rgb)[-6:].upper() if c is not None and c.type=='rgb' else ''

def cell_classes(cell):
 classes=['sheet-cell']
 if cell.font.bold:classes.append('sheet-bold')
 if cell.font.italic:classes.append('sheet-italic')
 if cell.alignment.horizontal in ('center','right'):classes.append('sheet-'+cell.alignment.horizontal)
 if cell.alignment.vertical=='top':classes.append('sheet-top')
 if cell.fill.patternType=='solid':
  palette={'F4B183':'sheet-group','FCE4D6':'sheet-head','DDEBF7':'sheet-axis','E2F0D9':'sheet-total'}
  classes.append(palette.get(color(cell.fill.fgColor),'sheet-fill'))
 if color(cell.font.color)=='C00000':classes.append('sheet-red')
 if any(getattr(getattr(cell.border,k,None),'style',None) for k in ('left','right','top','bottom')):classes.append('sheet-bordered')
 return ' '.join(classes)

def render_sheet(sh,kind):
 last=19 if kind=='kpi' else 5
 anchors={};covered=set()
 for m in sh.merged_cells.ranges:
  if m.min_col>last:continue
  end=min(m.max_col,last)
  anchors[(m.min_row,m.min_col)]=(m.max_row-m.min_row+1,end-m.min_col+1)
  for r in range(m.min_row,m.max_row+1):
   for col in range(m.min_col,end+1):
    if (r,col)!=(m.min_row,m.min_col):covered.add((r,col))
 out='<div class="sheet-scroll" tabindex="0" role="region" aria-label="Bảng xem Excel, cuộn ngang để xem đủ cột"><table class="sheet-table sheet-'+kind+'" aria-label="Xem trước Excel '+('KPI' if kind=='kpi' else 'tiêu chí chung')+'"><colgroup>'
 for col in range(1,last+1):out+='<col class="sheet-col-'+str(col)+'">'
 out+='</colgroup><tbody>'
 for r in range(1,sh.max_row+1):
  out+='<tr>'
  for col in range(1,last+1):
   if (r,col) in covered:continue
   cell=sh.cell(r,col);rs,cs=anchors.get((r,col),(1,1))
   attr=(' rowspan="'+str(rs)+'"' if rs>1 else '')+(' colspan="'+str(cs)+'"' if cs>1 else '')
   tag='th' if (kind=='kpi' and r<=5) or (kind=='common' and r<=4) else 'td'
   out+='<'+tag+' class="'+cell_classes(cell)+'"'+attr+'>'+escape(value_text(cell))+'</'+tag+'>'
  out+='</tr>'
 return out+'</tbody></table></div>'

def evidence_panel(c,calc):
 from app import h
 items=[]
 for t,z in calc['rows']:
  desc=(t['evidence'] or '').strip()
  files=c.execute('SELECT id,filename FROM attachments WHERE task=? ORDER BY id',(t['id'],)).fetchall()
  if not desc and not files:continue
  body='<li><b>Trục '+str(t['axis'])+' · '+h(t['title'])+'</b>'
  if desc:body+='<p class="evidence-text">'+h(desc)+'</p>'
  if files:body+='<div class="evidence-files">'+''.join('<a class="btn small secondary" href="/attachment/'+str(f['id'])+'">'+h(f['filename'])+'</a>' for f in files)+'</div>'
  items.append(body+'</li>')
 if not items:return ''
 return '<details class="declared-evidence"><summary>Hiện minh chứng ('+str(len(items))+' công việc)</summary><ol>'+''.join(items)+'</ol></details>'

def preview(c,e,calc,csrf='',active=False):
 from app import workbook
 import team_review_parts as tr
 saved=tr.read(c,e)
 b,w=workbook();pe.common_sheet(w,c,e);w.close();b.seek(0);book=load_workbook(b,data_only=True)
 try:common=render_sheet(book.active,'common')
 finally:book.close()
 b,w=workbook();pe.kpi_sheet(w,c,e,calc,hide_evidence=True);w.close();b.seek(0);book=load_workbook(b,data_only=True)
 try:kpi=render_sheet(book.active,'kpi')
 finally:book.close()
 out='<section class="panel excel-preview"><h2>XEM HỒ SƠ ĐÁNH GIÁ</h2>'+tr.progress(e,saved)
 out+='<section id="team-approve" class="review-part team-action-target"><h3>PHỤ LỤC CHẤM TIÊU CHÍ CHUNG</h3>'+common+tr.approval_form(e,'common',saved,csrf,active)+'</section>'
 out+='<section id="team-kpi" class="review-part team-action-target"><h3>BẢNG ĐÁNH GIÁ KPI</h3>'+kpi+evidence_panel(c,calc)+tr.approval_form(e,'kpi',saved,csrf,active)+'</section>'
 return out+'</section>'
