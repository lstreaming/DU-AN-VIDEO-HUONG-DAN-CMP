# BẮT ĐẦU — DU-AN-VIDEO-HUONG-DAN-CMP

## AI tiếp quản: làm đúng thứ tự
1. Từ thư mục gốc trong PowerShell, đặt TEMP/TMP trên ổ E rồi chạy gate đầu phiên:
   ```powershell
   $projectRoot = (Get-Location).Path
   $env:TEMP = Join-Path $projectRoot 'du_lieu\tam_me'
   $env:TMP = $env:TEMP
   python src/gates/kiem_dau_phien.py
   ```
2. Chạy `python src/gates/quet_vo_rong.py`; phải báo 0 vỏ rỗng.
3. Trong workspace riêng đầy đủ, đọc `du_lieu/LENH_BAN_GIAO_AI.md`, `du_lieu/SO_VIEC.md`, `du_lieu/YEU_CAU_C2.md` nếu có. Repo public cố ý không chứa các hồ sơ này.

Không xóa/di chuyển/tải dữ liệu hoặc gọi dịch vụ tốn quota nếu chưa được duyệt. Đo dung lượng trước khi tạo dữ liệu; giữ TEMP/TMP trên E:. Bản public chỉ chứa mã, test và hướng dẫn chung.
