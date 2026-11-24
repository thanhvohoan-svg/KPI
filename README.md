# KPI SCHOOL ONLINE DEMO – Hướng dẫn triển khai miễn phí

Phiên bản 1.1 DEMO • FastAPI + SQLite • Dữ liệu giả lập, không dùng cho hồ sơ thật.

## 1. Tạo GitHub repository
1. Tải và giải nén KPI_SCHOOL_ONLINE_DEMO.zip trên máy tính.
2. Đăng nhập https://github.com/ rồi mở https://github.com/new.
3. Repository name: `kpi-school-online-demo`. Chọn Private (Render sẽ được cấp quyền đọc). Có thể chọn Public nếu muốn chia sẻ mã nguồn demo; không bao giờ tải danh sách giáo viên thật lên đây.
4. Bấm Create repository. Trong repository mới, bấm `uploading an existing file` (hoặc Add file > Upload files nếu đã có file).
5. Mở thư mục đã giải nén; kéo **các file và thư mục bên trong** vào vùng tải file của GitHub, gồm `app.py`, `core.py`, `demo.py`, `requirements.txt`, `render.yaml`, thư mục `static`, cùng các file hướng dẫn/kiểm thử. Không tải nguyên file ZIP. Kiểm tra `static/style.css` nằm trong thư mục static trên GitHub; nếu tải thư mục không được, tải file bằng Add file > Create new file với đường dẫn `static/style.css` và sao chép nội dung file.
6. Bấm Commit changes. Các file app.py, demo.py, core.py, requirements.txt phải ở gốc repository; không đặt trong thư mục lồng.

## 2. Tạo Web Service trên Render (không cần cài Python)
1. Mở https://dashboard.render.com/register và đăng ký/đăng nhập (có thể dùng GitHub).
2. Dashboard > New > Web Service. Chọn Git Provider / GitHub và cấp quyền đọc repository `kpi-school-online-demo` khi được yêu cầu.
3. Chọn repository vừa tạo. Điền các thông tin sau:

| Trường | Giá trị |
|---|---|
| Name | kpi-school-online-demo (hoặc tên khác còn trống) |
| Branch | main (hoặc nhánh mặc định của repo) |
| Root Directory | Để trống nếu các file ở gốc repo |
| Language / Runtime | Python 3 |
| Region | Singapore nếu có; hoặc khu vực phù hợp |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn demo:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |
| Health Check Path (Advanced) | `/healthz` |

4. Environment Variables: thêm `PYTHON_VERSION` = `3.12.10` và `KPI_HTTPS` = `1` (cookie bảo mật HTTPS). Không cần thêm database, secret hay persistent disk cho demo.
5. Kiểm tra lại Instance Type là Free; không chọn dịch vụ trả phí. Bấm Deploy Web Service. Mở trang Logs kiểm tra có `Application startup complete` và `Uvicorn running`.
6. Khi trạng thái Live, mở đường dẫn HTTPS do Render hiển thị. Ví dụ minh họa `https://kpi-school-online-demo.onrender.com` (tên thật do Render cấp, không bảo đảm còn trống). Kiểm tra `/healthz` trả về JSON status ok.

Có thể dùng New > Blueprint và chọn repo nếu muốn Render đọc `render.yaml`. Chỉ chọn một phương thức, không tạo cả hai dịch vụ. Cấu hình đã khai báo gói Free.

## 3. Tài khoản và kịch bản thực hành
Mật khẩu chung: **KpiDemo2026!** (chữ K viết hoa; có dấu ! cuối).

| Tên đăng nhập | Vai trò |
|---|---|
| giaovien | Giáo viên Tin học mẫu |
| totruong | Tổ trưởng Tin học mẫu |
| bangiamhieu | BGH / quản trị demo |
| giaovien2 | Giáo viên Tin học B |
| giaovien3 | Giáo viên Tin học C |
| giaovientoan | Giáo viên Toán mẫu |
| totruongtoan | Tổ trưởng Toán mẫu |

Hãy **dùng cùng một trình duyệt và cùng cửa sổ thông thường** trong cả quá trình đổi vai trò. Đăng xuất, không xóa cookie. Mỗi trình duyệt/hồ sơ trình duyệt khác có dữ liệu giả lập riêng, không đồng bộ giữa thiết bị. Để thử lại từ đầu, mở cửa sổ ẩn danh mới (đóng toàn bộ cửa sổ ẩn danh trước đó) hoặc xóa cookie của riêng website.

### A. Giáo viên
- Đăng nhập giaovien. Quý III/2026 đã có hồ sơ và 3 nhiệm vụ mẫu.
- Chọn Mở hồ sơ. Điểm chung đã điền 28; có thể nhập 29, bấm Lưu điểm.
- Ở nhiệm vụ Ứng dụng công nghệ trong dạy học, sửa số lượng hoàn thành thành 2, số lần chỉnh sửa 0, ngày hoàn thành 30/09/2026, ghi Minh chứng giả lập. Bấm Lưu kết quả nhiệm vụ.
- Có thể tải tệp MINH_CHUNG_MAU.txt lên để thử đính kèm. Chỉ dùng tệp TXT giả lập.
- Điểm KPI sẽ đạt 70/70 nếu cả 3 nhiệm vụ hoàn thành đúng hạn, không lỗi. Nếu nhập 29 điểm chung thì tổng 99/100; không mặc nhiên xếp loại xuất sắc.
- Bấm Xuất Excel cá nhân, mở file .xlsx; đánh dấu xác nhận và Gửi duyệt. Đăng xuất.

### B. Tổ trưởng
- Đăng nhập totruong. Xem danh sách tổ Tin học; không thấy tổ Toán.
- Mở hồ sơ Giáo viên Tin học mẫu đang Đã nộp. Nhập điểm chung sau rà soát 28, nhận xét `Tổ đã rà soát`, bấm Tổ xác nhận. Có thể thử Trả lại bổ sung thay thế rồi nộp lại.
- Xuất tổng hợp Excel tổ, sau đó đăng xuất.

### C. Ban Giám hiệu
- Đăng nhập bangiamhieu. Xem 6 hồ sơ giả lập thuộc 2 tổ.
- Mở hồ sơ Giáo viên Tin học mẫu (Tổ đã duyệt). Nhập 28 điểm chung, chọn Hoàn thành tốt nhiệm vụ, nhập nhận xét, đánh dấu xác nhận, bấm BGH duyệt. Tổng 98/100; chưa đủ điều kiện xuất sắc nếu không có nhiệm vụ vượt mức yêu cầu.
- Xuất tổng hợp Excel (3 sheet: Phụ lục III, Kiểm soát tỷ lệ, So sánh HTXS). Mục Quản trị cho phép thêm tổ, mở kỳ, thêm mẫu nhiệm vụ; Giao nhiệm vụ hỗ trợ giao theo phạm vi quyền.
- Đăng xuất, đăng nhập giaovien để thấy kết quả BGH đã duyệt; tải Excel cá nhân đã cập nhật.

## 4. Các giới hạn và lựa chọn thiết kế
- DEMO sử dụng 7 tài khoản cố định (6 hồ sơ đánh giá và 1 BGH quản trị), không sử dụng GiaoVien.xlsx. Không thể đổi mật khẩu, phân quyền hay đặt lại mật khẩu trong DEMO. Bản V1 gốc vẫn có các chức năng này.
- Dữ liệu tách theo cookie trình duyệt; tối đa 40 không gian thử đồng thời, hết hạn sau 6 giờ không sử dụng. Mỗi phiên tối đa 8 kỳ, giới hạn nhiệm vụ gần 400; tệp TXT tối đa 100 KB/tệp và tổng 1 MB/phiên. Không tải hồ sơ thật.
- Render Free có thể ngủ sau 15 phút không có lưu lượng truy cập; khi ngủ, restart hoặc deploy lại, dữ liệu SQLite có thể mất. Hệ thống tự tạo dữ liệu mẫu khi khởi động. Không dùng demo làm hồ sơ chính thức. Có giới hạn tài nguyên miễn phí theo tài khoản/workspace.
- Demo mặc định chấm theo điểm chuẩn nhiệm vụ (mục 5–6 của Công văn 5142); có chế độ trọng số theo số sản phẩm khi mở quý mới để đối chiếu. Cách xử lý chất lượng/tiến độ với nhiệm vụ chưa hoàn thành và điều kiện xếp loại còn cần nhà trường thống nhất trước khi áp dụng chính thức. Danh mục nhiệm vụ và trục mẫu không phải danh mục bắt buộc của Sở.
- Excel giữ cấu trúc 19 cột và các phần tổng hợp của Phụ lục II/III, không phải bản sao y tuyệt đối mẫu gốc.
- Kiểm thử chạy trong môi trường tạo gói, gồm luồng đăng nhập, phân quyền, chấm điểm, duyệt và xuất Excel. Chưa triển khai vào tài khoản Render thật, chưa thử tải 101 người cùng lúc, chưa kiểm định bảo mật độc lập.
- Khi triển khai thật: cần cơ sở dữ liệu bền vững, lưu minh chứng có phân quyền, sao lưu, HTTPS, tài khoản cá nhân, xác nhận cơ cấu tổ và công thức. Không chuyển dữ liệu thật vào gói này.

## 5. Xử lý lỗi thường gặp
- ModuleNotFoundError: kiểm tra file requirements.txt, lệnh build và Root Directory.
- Không tìm thấy static: kiểm tra GitHub có `static/style.css`.
- Port scan timeout: lệnh start phải là `uvicorn demo:app --host 0.0.0.0 --port $PORT`.
- Đăng nhập bị trả về login: mở URL HTTPS của Render; chấp nhận cookie của site; không thử qua HTTP.
- Mất dữ liệu: đúng đặc điểm gói Free; nhập lại dữ liệu mẫu hoặc mở phiên mới.
- Nếu báo lỗi, gửi ảnh trang Logs (che token hoặc thông tin tài khoản).

## 6. Nguồn hướng dẫn Render
- https://render.com/docs/deploy-fastapi
- https://render.com/docs/your-first-deploy
- https://render.com/docs/free
- https://render.com/docs/web-services
