import os
import re
import numpy as np
import pandas as pd
from urllib.parse import urlparse

# ==============================================================================
# CẤU HÌNH ĐƯỜNG DẪN TỆP VÀ BỘ QUY TẮC
# ==============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
DATASET_DIR = os.path.join(PROJECT_DIR, "dataset")

files = {
    "Guardian": {"path": os.path.join(DATASET_DIR, "guardian_raw.csv"), "domain": "guardian.com.vn"},
    "Hasaki": {"path": os.path.join(DATASET_DIR, "hasaki_raw.csv"), "domain": "hasaki.vn"}
}

EXPECTED_COLUMNS = [
    "product_id", "product_name", "brand", "category", "volume_weight", 
    "current_price", "original_price", "discount_percent", "rating", 
    "review_count", "source", "product_url"
]

EXPECTED_CATEGORIES = {"Chăm sóc da", "Trang điểm", "Chăm sóc tóc", "Chăm sóc cá nhân"}
SUSPECT_BRANDS = ["SON", "KEM", "SỮA", "NUOC", "NƯỚC", "MẶT", "COMBO", "TINH", "BỘ", "DẦU", "GEL", "BÔNG", "XỊT"]

all_issues = []
stats_by_source = {}

print("=" * 85)
print("BÁO CÁO KIỂM TOÁN CHẤT LƯỢNG TOÀN DIỆN (BẢN FINAL CHỐT CLEAN.PY)")
print("=" * 85)

for source_name, config in files.items():
    file_path = config["path"]
    exp_domain = config["domain"]
    
    print(f"\n" + "-" * 65)
    print(f"KIỂM TOÁN TẬP DỮ LIỆU: {source_name.upper()}")
    print("-" * 65)
    
    if not os.path.exists(file_path):
        print(f"❌ Không tìm thấy tệp: {file_path}")
        continue
        
    df = pd.read_csv(file_path, sep=";", encoding="utf-8-sig")
    total_rows = len(df)
    
    # --------------------------------------------------------------------------
    # 1. KIỂM TRA ĐỦ 12 CỘT BẮT BUỘC ĐẦU VÀO
    # --------------------------------------------------------------------------
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        print(f"⚠️ Phát hiện thiếu cột: {missing_cols}. Đã tự động chèn cột NaN để quét tiếp.")
        for col in missing_cols:
            df[col] = np.nan
    
    # --------------------------------------------------------------------------
    # 2. THỐNG KÊ ĐẶC TÍNH (Không coi là lỗi hệ thống)
    # --------------------------------------------------------------------------
    rev_num = pd.to_numeric(df["review_count"], errors="coerce")
    no_rating_cnt = (df["rating"].isna() & (pd.notna(rev_num) & (rev_num == 0))).sum()
    all_caps_cnt = df["product_name"].dropna().astype(str).str.isupper().sum()
    
    print(f"[ĐẶC TÍNH BỔ SUNG & PHÂN LOẠI HIỂN THỊ]")
    print(f"  - Chưa có đánh giá (Hợp lệ)  : {no_rating_cnt:,}/{total_rows:,} ({no_rating_cnt/total_rows*100:.1f}%)")
    print(f"  - Tên viết hoa toàn bộ       : {all_caps_cnt:,} dòng")

    # --------------------------------------------------------------------------
    # 3. QUÉT SÂU 12 TRƯỜNG DỮ LIỆU (QUẢN LÝ THEO ROW INDEX)
    # --------------------------------------------------------------------------
    cur_p = pd.to_numeric(df["current_price"], errors="coerce")
    orig_p = pd.to_numeric(df["original_price"], errors="coerce")
    disc_num = pd.to_numeric(df["discount_percent"], errors="coerce")
    rat_num = pd.to_numeric(df["rating"], errors="coerce")
    
    # Khắc phục lỗi đếm trùng lặp giả (chỉ xét trùng với các ô có dữ liệu thực)
    dup_ids = df["product_id"].duplicated(keep=False) & df["product_id"].notna()
    dup_names = df["product_name"].duplicated(keep=False) & df["product_name"].notna()
    
    type_counts = {}
    error_count_by_row = {}
    
    for idx, row in df.iterrows():
        pid_raw = row.get("product_id")
        # Đánh dấu dòng lỗi nếu ID trống để dễ tra cứu CSV
        display_pid = str(int(pid_raw)) if pd.notna(pid_raw) and isinstance(pid_raw, (int, float)) else f"[Dòng_{idx + 2}]"
        
        p_name = str(row.get("product_name", "")).strip()
        b_name = str(row.get("brand", "")).strip()
        vol_str = str(row.get("volume_weight", "")).strip().lower()
        
        row_issues = []
        
        # 1. product_id
        if pd.isna(pid_raw) or str(pid_raw).strip() == "":
            row_issues.append(("Thiếu mã sản phẩm", "product_id", "nan"))
        elif dup_ids[idx]:
            row_issues.append(("Mã sản phẩm trùng lặp", "product_id", str(pid_raw)))
            
        # 2. product_name
        if pd.isna(row.get("product_name")) or not p_name:
            row_issues.append(("Thiếu tên sản phẩm", "product_name", "nan"))
        else:
            if re.match(r'^\d+/tháng', p_name, flags=re.IGNORECASE):
                row_issues.append(("Tên cào nhầm badge", "product_name", p_name))
            if dup_names[idx]:
                row_issues.append(("Tên sản phẩm trùng nhau", "product_name", p_name))
                
        # 3. brand
        if pd.isna(row.get("brand")) or not b_name:
            row_issues.append(("Thiếu thương hiệu", "brand", "nan"))
        elif b_name.upper() in SUSPECT_BRANDS:
            row_issues.append(("Thương hiệu nghi vấn", "brand", b_name))
            
        # 4. category
        cat_val = str(row.get("category", "")).strip()
        if pd.isna(row.get("category")) or not cat_val:
            row_issues.append(("Thiếu danh mục", "category", "nan"))
        elif cat_val not in EXPECTED_CATEGORIES:
            row_issues.append(("Danh mục lệch chuẩn", "category", cat_val))
            
        # 5. volume_weight
        if pd.isna(row.get("volume_weight")) or vol_str in ["", "nan", "none"]:
            row_issues.append(("Thiếu dung tích / khối lượng", "volume_weight", "nan"))
            
        # 6. current_price
        if pd.isna(cur_p[idx]):
            row_issues.append(("Giá bán không hợp lệ", "current_price", str(row.get("current_price"))))
        elif cur_p[idx] <= 0:
            row_issues.append(("Giá bán <= 0đ", "current_price", str(row.get("current_price"))))
            
        # 7. original_price (Giá gốc trống không tính là lỗi nếu không có khuyến mãi)
        if pd.notna(orig_p[idx]):
            if orig_p[idx] < 0:
                row_issues.append(("Giá gốc âm", "original_price", str(row.get("original_price"))))
            elif pd.notna(cur_p[idx]) and (orig_p[idx] < cur_p[idx]):
                row_issues.append(("Giá gốc thấp hơn giá bán", "original_price", f"Gốc: {row.get('original_price')} < Bán: {row.get('current_price')}"))
            
        # 8. discount_percent (Khắc phục lỗi lọt lưới NaN)
        if pd.isna(disc_num[idx]):
            row_issues.append(("Giảm giá không hợp lệ", "discount_percent", str(row.get("discount_percent"))))
        elif disc_num[idx] < 0 or disc_num[idx] > 100:
            row_issues.append(("Giảm giá ngoài 0-100%", "discount_percent", str(row.get("discount_percent"))))
        elif pd.notna(orig_p[idx]) and pd.notna(cur_p[idx]) and orig_p[idx] > 0 and cur_p[idx] <= orig_p[idx]:
            exp_disc = round(((orig_p[idx] - cur_p[idx]) / orig_p[idx]) * 100, 1)
            if abs(disc_num[idx] - exp_disc) > 1.5:
                row_issues.append(("Lệch công thức giảm giá", "discount_percent", f"Thực tế: {disc_num[idx]}%, Tính: {exp_disc}%"))
                    
        # 9. rating & 10. review_count (Khắc phục lỗi lọt lưới NaN ở review_count)
        if pd.notna(rat_num[idx]) and (rat_num[idx] < 0 or rat_num[idx] > 5):
            row_issues.append(("Rating ngoài 0-5", "rating", str(row.get("rating"))))
            
        if pd.isna(rev_num[idx]):
            row_issues.append(("Lượt đánh giá không hợp lệ", "review_count", str(row.get("review_count"))))
        else:
            if rev_num[idx] < 0 or (rev_num[idx] % 1 != 0):
                row_issues.append(("Lượt đánh giá sai định dạng", "review_count", str(row.get("review_count"))))
            elif rev_num[idx] > 0 and pd.isna(row.get("rating")):
                row_issues.append(("Có lượt đánh giá nhưng thiếu điểm", "rating", "nan"))
            elif rev_num[idx] == 0 and pd.notna(row.get("rating")):
                row_issues.append(("Có điểm nhưng review=0", "review_count", "0"))
                
        # 11. source
        src_val = str(row.get("source", "")).strip()
        if pd.isna(row.get("source")) or not src_val:
            row_issues.append(("Thiếu nguồn dữ liệu", "source", "nan"))
        elif src_val.lower() != source_name.lower():
            row_issues.append(("Nguồn không đúng website", "source", src_val))
            
        # 12. product_url (Parse Hostname)
        url_val = str(row.get("product_url", "")).strip()
        if pd.isna(row.get("product_url")) or not url_val:
            row_issues.append(("Thiếu URL sản phẩm", "product_url", "nan"))
        else:
            parsed = urlparse(url_val)
            if parsed.scheme not in ["http", "https"]:
                row_issues.append(("URL thiếu http/https", "product_url", url_val))
            elif exp_domain not in str(parsed.netloc).lower():
                row_issues.append(("URL sai tên miền", "product_url", str(parsed.netloc)))
            
        # Ghi nhận lỗi theo DÒNG (Row Index)
        if row_issues:
            error_count_by_row[idx] = len(row_issues)
            
            for err_type, field, cur_val in row_issues:
                type_counts[err_type] = type_counts.get(err_type, 0) + 1
                all_issues.append({
                    "source": source_name,
                    "product_id": display_pid, # ID an toàn đã qua xử lý nội suy
                    "product_name": p_name[:120],
                    "error_type": err_type,
                    "field": field,
                    "current_value": cur_val
                })

    # Bảng thống kê chi tiết
    print(f"\n[BẢNG TỔNG HỢP LỖI TẠI {source_name.upper()}]")
    if type_counts:
        err_df = pd.DataFrame(list(type_counts.items()), columns=["Loại lỗi phát hiện", "Số lượt"])
        err_df = err_df.sort_values("Số lượt", ascending=False)
        print(err_df.to_string(index=False))
    else:
        print("  ✅ Không phát hiện lỗi cần clean.")

    # Thống kê phân bổ theo bản ghi (dòng)
    count_less_than_2 = sum(1 for err_cnt in error_count_by_row.values() if err_cnt < 2)
    count_gte_2 = sum(1 for err_cnt in error_count_by_row.values() if err_cnt >= 2)
    total_err_rows = len(error_count_by_row)
    
    stats_by_source[source_name] = {
        "less_than_2": count_less_than_2,
        "gte_2": count_gte_2,
        "total": total_err_rows,
        "total_rows": total_rows
    }
    
    print(f"\n[THỐNG KÊ THEO BẢN GHI DỮ LIỆU]")
    print(f"  - Số bản ghi bị < 2 lỗi (1 lỗi) : {count_less_than_2:,} dòng")
    print(f"  - Số bản ghi bị >= 2 lỗi        : {count_gte_2:,} dòng")
    print(f"👉 KẾT LUẬN {source_name.upper()}: Có {total_err_rows:,} bản ghi dính lỗi (chiếm {total_err_rows/total_rows*100:.2f}%).")

# ------------------------------------------------------------------------------
# 4. KẾT LUẬN TOÀN HỆ THỐNG VÀ XUẤT TỆP
# ------------------------------------------------------------------------------
print("\n" + "=" * 85)
print("KẾT LUẬN TOÀN BỘ HỆ THỐNG (ĐẾM THEO SỐ BẢN GHI)")
print("=" * 85)
total_sys_records = sum(s["total_rows"] for s in stats_by_source.values())
total_less = sum(s["less_than_2"] for s in stats_by_source.values())
total_gte = sum(s["gte_2"] for s in stats_by_source.values())
total_sys_err_rows = sum(s["total"] for s in stats_by_source.values())

print(f"- Tổng số bản ghi thu thập                  : {total_sys_records:,} bản ghi")
print(f"- Số lượng bản ghi bị < 2 lỗi               : {total_less:,} bản ghi")
print(f"- Số lượng bản ghi bị >= 2 lỗi              : {total_gte:,} bản ghi")
print(f"👉 TỔNG SỐ BẢN GHI LỖI (Tính cả 1 hoặc 2 lỗi) : {total_sys_err_rows:,} bản ghi (chiếm {total_sys_err_rows/total_sys_records*100:.2f}%).")
print(f"  + Tỷ lệ dữ liệu ĐÃ SẠCH HOÀN TOÀN (Dòng)  : {(total_sys_records - total_sys_err_rows)/total_sys_records*100:.2f}%")
print(f"  * Lưu ý: Tỷ lệ này chưa phản ánh độ sạch tuyệt đối do có thể tồn tại các lỗi ẩn chưa định nghĩa.")

# Xuất file log kết quả gồm đúng 6 cột
output_csv = os.path.join(DATASET_DIR, "data_quality_issues.csv")
pd.DataFrame(all_issues, columns=["source", "product_id", "product_name", "error_type", "field", "current_value"]).to_csv(output_csv, index=False, encoding="utf-8-sig")
print(f"\n✅ Đã xuất tệp CSV chứa danh sách lỗi đầu vào tại:\n{output_csv}")
print("=" * 85)