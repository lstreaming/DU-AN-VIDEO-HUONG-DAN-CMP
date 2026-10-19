# BẮT ĐẦU — DU-AN-VIDEO-HUONG-DAN-CMP

## AI tiếp quản: giữ đúng thứ tự 3 bước
1. Trong PowerShell, đặt TEMP/TMP vào thư mục tạm của dự án rồi chạy gate đầu phiên:
   ```powershell
   $projectRoot = (Get-Location).Path
   $env:TEMP = Join-Path $projectRoot 'du_lieu\tam_me'
   $env:TMP = $env:TEMP
   python src/gates/kiem_dau_phien.py
   ```
2. Chạy `python src/gates/quet_vo_rong.py` (phải báo 0 vỏ rỗng).
3. Trong workspace riêng đầy đủ, đọc các hồ sơ bàn giao tại chỗ; các hồ sơ nội bộ này không nằm trong kho mã public.

Giữ khóa ngoài Git. Gate đầu phiên cần workspace riêng đầy đủ và các hồ sơ bàn giao nội bộ; bản public chỉ chứa mã nguồn và test.
