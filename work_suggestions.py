"""Editable suggestions; catalogue records are scoped to the evaluation."""
from core import normalize

# General suggestions are document types and potential products, not actual assignments.
GENERAL={
'Thực hiện kế hoạch giảng dạy':(['Quyết định phân công nhiệm vụ giảng dạy','Kế hoạch giáo dục nhà trường','Kế hoạch giáo dục của tổ chuyên môn'],['Kế hoạch giảng dạy, sổ đầu bài','Tiết dạy theo kế hoạch']),
'Soạn kế hoạch bài dạy':(['Kế hoạch giáo dục của tổ chuyên môn','Phân công giảng dạy'],['Kế hoạch bài dạy','Giáo án, học liệu bài dạy']),
'Kiểm tra, đánh giá học sinh':(['Kế hoạch kiểm tra, đánh giá','Phân công ra đề, coi và chấm kiểm tra'],['Đề kiểm tra, ma trận, đặc tả và hướng dẫn chấm','Bảng điểm, kết quả đánh giá học sinh']),
'Sinh hoạt chuyên môn':(['Kế hoạch hoạt động tổ chuyên môn','Lịch sinh hoạt chuyên môn'],['Biên bản sinh hoạt chuyên môn','Báo cáo chuyên đề']),
'Công tác chủ nhiệm lớp':(['Quyết định phân công nhiệm vụ giảng dạy và chủ nhiệm lớp','Kế hoạch công tác chủ nhiệm'],['Kế hoạch chủ nhiệm lớp','Hồ sơ, sổ chủ nhiệm','Báo cáo kết quả công tác chủ nhiệm']),
'Bồi dưỡng học sinh giỏi':(['Kế hoạch bồi dưỡng học sinh giỏi','Quyết định hoặc phân công bồi dưỡng đội tuyển'],['Kế hoạch và chuyên đề bồi dưỡng','Hồ sơ, kết quả bồi dưỡng đội tuyển']),
'Phụ đạo học sinh':(['Kế hoạch phụ đạo học sinh','Phân công phụ đạo'],['Kế hoạch, tài liệu phụ đạo','Báo cáo kết quả phụ đạo']),
'Thực hiện hồ sơ chuyên môn':(['Kế hoạch chuyên môn','Quy định hồ sơ chuyên môn'],['Hồ sơ chuyên môn','Kế hoạch giáo dục cá nhân']),
'Coi thi, chấm thi':(['Quyết định phân công coi thi, chấm thi','Kế hoạch tổ chức kỳ thi'],['Biên bản coi thi','Phiếu chấm, kết quả chấm thi']),
'Xây dựng hoặc góp ý quy chế nhà trường':(['Kế hoạch xây dựng, rà soát quy chế'],['Dự thảo quy chế','Văn bản góp ý']),
'Xây dựng quy trình chuyên môn':(['Kế hoạch chuyên môn','Phân công xây dựng quy trình'],['Dự thảo hoặc quy trình chuyên môn']),
'Tham gia kiểm tra nội bộ':(['Kế hoạch kiểm tra nội bộ','Quyết định thành lập tổ kiểm tra'],['Biên bản kiểm tra','Báo cáo kết quả kiểm tra']),
'Rà soát hồ sơ, kế hoạch theo phân công':(['Kế hoạch rà soát hồ sơ','Phân công rà soát'],['Phiếu rà soát','Báo cáo kết quả rà soát']),
'Thực hiện nhiệm vụ quản lý được giao':(['Quyết định phân công nhiệm vụ quản lý'],['Kế hoạch công tác','Báo cáo kết quả nhiệm vụ']),
'Ứng dụng công nghệ trong dạy học':(['Kế hoạch ứng dụng công nghệ thông tin','Kế hoạch giáo dục tổ chuyên môn'],['Bài giảng số','Sản phẩm công nghệ hỗ trợ dạy học']),
'Xây dựng học liệu số':(['Kế hoạch xây dựng học liệu số'],['Bài giảng, video, học liệu số']),
'Thực hiện nhiệm vụ chuyển đổi số':(['Kế hoạch chuyển đổi số','Phân công nhiệm vụ chuyển đổi số'],['Sản phẩm số','Báo cáo kết quả chuyển đổi số']),
'Nghiên cứu khoa học':(['Kế hoạch nghiên cứu khoa học'],['Đề tài, báo cáo nghiên cứu']),
'Thực hiện sáng kiến':(['Kế hoạch công tác sáng kiến'],['Báo cáo sáng kiến','Sản phẩm áp dụng sáng kiến']),
'Hướng dẫn học sinh nghiên cứu khoa học':(['Kế hoạch tổ chức hoạt động nghiên cứu khoa học','Phân công hướng dẫn học sinh'],['Hồ sơ đề tài, sản phẩm nghiên cứu của học sinh']),
'Thực hiện nhiệm vụ công tác Đảng':(['Nghị quyết, kế hoạch công tác Đảng','Phân công nhiệm vụ'],['Báo cáo, hồ sơ thực hiện nhiệm vụ']),
'Tham gia công tác Công đoàn':(['Kế hoạch hoạt động Công đoàn','Phân công nhiệm vụ'],['Báo cáo, hồ sơ hoạt động Công đoàn']),
'Tham gia công tác Đoàn thanh niên':(['Kế hoạch hoạt động Đoàn','Phân công nhiệm vụ'],['Kế hoạch, báo cáo hoạt động Đoàn']),
'Thực hiện nhiệm vụ xây dựng tổ chức theo phân công':(['Kế hoạch xây dựng tổ chức','Phân công nhiệm vụ'],['Hồ sơ, báo cáo kết quả']),
'Tổ chức hoạt động trải nghiệm, hướng nghiệp':(['Kế hoạch hoạt động trải nghiệm, hướng nghiệp','Phân công tổ chức hoạt động'],['Kế hoạch, hồ sơ hoạt động','Báo cáo kết quả hoạt động']),
'Giáo dục kỹ năng sống':(['Kế hoạch giáo dục kỹ năng sống'],['Tài liệu, chuyên đề giáo dục kỹ năng sống','Báo cáo hoạt động']),
'Hỗ trợ học sinh có hoàn cảnh khó khăn':(['Kế hoạch hỗ trợ học sinh','Phân công hỗ trợ'],['Hồ sơ, báo cáo hỗ trợ học sinh']),
'Tổ chức hoạt động văn hóa, văn nghệ, thể thao':(['Kế hoạch tổ chức hoạt động văn hóa, thể thao'],['Kế hoạch, hồ sơ và báo cáo hoạt động']),
'Tham gia hoạt động cộng đồng':(['Kế hoạch hoạt động cộng đồng','Phân công tham gia'],['Báo cáo kết quả hoạt động']),
'Thực hiện nhiệm vụ giáo dục quốc phòng - an ninh':(['Kế hoạch giáo dục quốc phòng - an ninh','Phân công nhiệm vụ'],['Kế hoạch, hồ sơ giáo dục quốc phòng - an ninh']),
'Tham gia công tác an toàn trường học':(['Kế hoạch an toàn trường học'],['Biên bản, báo cáo công tác an toàn']),
'Tuyên truyền phòng chống tệ nạn xã hội':(['Kế hoạch tuyên truyền phòng chống tệ nạn xã hội'],['Tài liệu, báo cáo tuyên truyền']),
'Tham gia phòng cháy, chữa cháy theo phân công':(['Kế hoạch phòng cháy, chữa cháy','Phân công nhiệm vụ'],['Hồ sơ, biên bản hoặc báo cáo hoạt động']),
'Thực hiện nhiệm vụ đối ngoại, hợp tác quốc tế':(['Kế hoạch đối ngoại, hợp tác quốc tế','Phân công nhiệm vụ'],['Hồ sơ, báo cáo kết quả hợp tác'])
}
FALLBACK=(['Kế hoạch công tác được phê duyệt','Quyết định hoặc văn bản phân công nhiệm vụ'],['Báo cáo kết quả thực hiện nhiệm vụ','Hồ sơ, sản phẩm công việc'])

def catalogue(c,e,axis,names):
 import quick
 templates=quick.templates(c,e,axis)
 evidence=quick.available(c,e)
 library=c.execute('SELECT title,product FROM library WHERE axis=?',(axis,)).fetchall()
 out={}
 for title in names:
  key=normalize(title)
  source=[];product=[]
  def add(items,value,label=None):
   value=(value or '').strip()
   if value and len(value)<=500 and all(normalize(x['value'])!=normalize(value) for x in items):
    items.append({'value':value,'label':label or value})
  for t in templates:
   if normalize(t['title'])==key:
    add(source,t['source']);add(product,t['product'])
  for r in evidence:
   if normalize(r['task_title'])==key:
    ref=r['reference'] or r['title']
    add(source,ref,'Kho: '+r['title']+(' · '+r['reference'] if r['reference'] else ''))
  for r in library:
   if normalize(r['title'])==key:add(product,r['product'])
  src,prod=GENERAL.get(title,FALLBACK)
  for x in src:add(source,x,'Loại văn bản: '+x)
  for x in prod:add(product,x)
  out[title]={'source':source,'product':product}
 return out
