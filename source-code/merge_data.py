import os
import pandas as pd

# ==============================================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN TỆP
# ==============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
DATASET_DIR = os.path.join(PROJECT_DIR, "dataset")

HASAKI_FILE = os.path.join(DATASET_DIR, "hasaki_cleaned.csv")
GUARDIAN_FILE = os.path.join(DATASET_DIR, "guardian_cleaned.csv")
OUTPUT_FILE = os.path.join(DATASET_DIR, "merged_data.csv")

# Định nghĩa danh sách 15 cột chuẩn cố định
EXPECTED_COLUMNS = [
    'source', 'product_id', 'product_name', 'brand', 'category',
    'volume_weight', 'volume_val', 'volume_unit',
    'current_price', 'original_price', 'discount_percent',
    'rating', 'review_count', 'has_rating', 'product_url'
]

def merge_datasets():
    print("=" * 80)
    print(" QUY TRÌNH HỢP NHẤT DỮ LIỆU ĐÃ LÀM SẠCH (HASAKI & GUARDIAN)")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # KIỂM TRA TỆP ĐẦU VÀO
    # --------------------------------------------------------------------------
    for f_path, f_name in [(HASAKI_FILE, "Hasaki"), (GUARDIAN_FILE, "Guardian")]:
        if not os.path.exists(f_path):
            print(f"❌ Không tìm thấy tệp: {f_path}")
            print(f"👉 Vui lòng chạy clean_{f_name.lower()}.py trước.")
            return

    print("Đang đọc dữ liệu từ hai sàn...")
    df_hasaki = pd.read_csv(HASAKI_FILE, sep=",", encoding="utf-8-sig")
    df_guardian = pd.read_csv(GUARDIAN_FILE, sep=",", encoding="utf-8-sig")

    count_h = len(df_hasaki)
    count_g = len(df_guardian)
    print(f" - Số bản ghi Hasaki   : {count_h:,}")
    print(f" - Số bản ghi Guardian : {count_g:,}")

    # --------------------------------------------------------------------------
    # 1. ĐỊNH NGHĨA VÀ ĐỒNG NHẤT DANH SÁCH 15 CỘT CHUẨN CỐ ĐỊNH
    # --------------------------------------------------------------------------
    df_hasaki = df_hasaki[EXPECTED_COLUMNS]
    df_guardian = df_guardian[EXPECTED_COLUMNS]

    # --------------------------------------------------------------------------
    # 2. HỢP NHẤT DỮ LIỆU (KHÔNG TẠO THÊM CỘT MỚI)
    # --------------------------------------------------------------------------
    print("\nĐang tiến hành hợp nhất dữ liệu...")
    df_merged = pd.concat([df_hasaki, df_guardian], ignore_index=True)
    df_merged = df_merged[EXPECTED_COLUMNS]

    # --------------------------------------------------------------------------
    # 3. KIỂM TRA ĐIỀU KIỆN XUNG ĐỘT KHOÁ KÉP (source + product_id)
    # --------------------------------------------------------------------------
    duplicate_keys = df_merged.duplicated(subset=['source', 'product_id'], keep=False)
    num_duplicates = duplicate_keys.sum()

    if num_duplicates > 0:
        print(f"⚠️ Cảnh báo: Phát hiện {num_duplicates} bản ghi bị trùng cặp khóa (source + product_id)!")
        print(df_merged[duplicate_keys][['source', 'product_id', 'product_name']].head())
    else:
        print("✅ Kiểm tra xung đột khóa: Cặp định danh (source + product_id) là duy nhất 100% trên toàn bộ tập dữ liệu.")

    # --------------------------------------------------------------------------
    # 4. KIỂM TRA TÍNH TOÀN VẸN SỐ DÒNG & Ô TRỐNG (SOLID DATA CHECK)
    # --------------------------------------------------------------------------
    total_actual = len(df_merged)
    total_expected = count_h + count_g

    if total_actual != total_expected:
        print(f"❌ LỖI TOÀN VẸN: Số dòng sau khi gộp ({total_actual:,}) không bằng tổng dự kiến ({total_expected:,})!")
        return
    else:
        print(f"✅ Kiểm tra số lượng: Khớp chính xác 100% ({total_actual:,} dòng).")

    null_count = df_merged.isna().sum().sum()
    if null_count > 0:
        print(f"⚠️ Cảnh báo: Phát hiện {null_count} ô trống phát sinh sau khi hợp nhất.")
    else:
        print("✅ Kiểm tra chất lượng: Dữ liệu sạch đặc 100% (Không phát sinh bất kỳ ô trống nào).")

    # --------------------------------------------------------------------------
    # 5. XUẤT TỆP VÀ BẢO VỆ CHỐNG PERMISSION ERROR
    # --------------------------------------------------------------------------
    try:
        df_merged.to_csv(OUTPUT_FILE, index=False, sep=",", encoding="utf-8-sig")
        print("=" * 80)
        print(f"🎉 HOÀN THÀNH HỢP NHẤT DỮ LIỆU!")
        print(f"   Tệp lưu trữ chính thức: {OUTPUT_FILE}")
        print(f"   Số lượng cột: {len(df_merged.columns)} cột | Số lượng dòng: {len(df_merged):,} dòng")
        print("=" * 80)
    except PermissionError:
        print("\n❌ LỖI TRUY CẬP: Tệp kết quả đang bị khóa bởi Excel hoặc OneDrive!")
        alt_output = OUTPUT_FILE.replace(".csv", "_backup.csv")
        try:
            df_merged.to_csv(alt_output, index=False, sep=",", encoding="utf-8-sig")
            print(f"✅ Đã tự động lưu sang tệp dự phòng: {alt_output}")
            print("👉 Vui lòng đóng tệp Excel đang mở để tránh lỗi khóa tệp.")
        except Exception as e:
            print(f"Không thể lưu tệp: {e}")

if __name__ == "__main__":
    merge_datasets()