import os
import re
import numpy as np
import pandas as pd
from urllib.parse import unquote

# ==============================================================================
# CẤU HÌNH ĐƯỜNG DẪN TỆP
# ==============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
DATASET_DIR = os.path.join(PROJECT_DIR, "dataset")

INPUT_FILE = os.path.join(DATASET_DIR, "guardian_raw.csv")
OUTPUT_FILE = os.path.join(DATASET_DIR, "guardian_cleaned.csv")

SUSPECT_BRANDS = ["SON", "KEM", "SỮA", "NUOC", "NƯỚC", "MẶT", "COMBO", "TINH", "BỘ", "DẦU", "GEL", "BÔNG", "XỊT"]

# Từ điển các hãng phổ biến
BRAND_MAPPING = {
    "L'OREAL": "L'Oreal", "MAYBELLINE": "Maybelline", "LA ROCHE-POSAY": "La Roche-Posay",
    "LA ROCHE POSAY": "La Roche-Posay", "VICHY": "Vichy", "CERA VE": "CeraVe", 
    "CERAVE": "CeraVe", "SKIN1004": "Skin1004", "DEAR KLAIRS": "Klairs", 
    "KLAIRS": "Klairs", "PAULA'S CHOICE": "Paula's Choice", "D-PROGRAM": "d program", 
    "D PROGRAM": "d program", "3CE": "3CE", "MAC": "MAC", "PERFECT DIARY": "Perfect Diary", 
    "DR.ALTHEA": "Dr.Althea", "ST.IVES": "St.Ives", "ST. IVES": "St.Ives", 
    "VASELINE": "Vaseline", "CETAPHIL": "Cetaphil", "SIMPLE": "Simple",
    "GARNIER": "Garnier", "BIODERMA": "Bioderma", "HATOMUGI": "Hatomugi",
    "COLORKEY": "Colorkey", "BEPLAIN": "Beplain"
}

def extract_volume(text, url):
    """Quét dung tích mở rộng từ Tên sản phẩm, nếu không có thì quét tiếp trong URL."""
    pattern = r'(\d+(?:[\.,]\d+)?)\s*(ml|g|kg|l|miếng|tờ|viên|cây|gói|chai|lọ|set|hộp|cặp|tuýp|oz)'
    
    if pd.notna(text):
        match = re.search(pattern, str(text), flags=re.IGNORECASE)
        if match:
            return match.group(1).replace(',', '.'), match.group(2).lower()
            
    if pd.notna(url):
        decoded_url = unquote(str(url))
        match_url = re.search(pattern, decoded_url, flags=re.IGNORECASE)
        if match_url:
            return match_url.group(1).replace(',', '.'), match_url.group(2).lower()
            
    return "1.0", "sp"

def clean_guardian_data():
    print("=" * 70)
    print(" BẮT ĐẦU LÀM SẠCH VÀ ĐIỀN KHUYẾT DỮ LIỆU SÀN GUARDIAN")
    print("=" * 70)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Không tìm thấy file: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE, sep=";", encoding="utf-8-sig")
    print(f"Đã tải {len(df)} bản ghi từ Guardian.")

    # --------------------------------------------------------------------------
    # 1. ĐIỀN KHUYẾT VÀ CHUẨN HÓA TÊN SẢN PHẨM (Đổi 127 dòng ALL-CAPS)
    # --------------------------------------------------------------------------
    df['product_name'] = df['product_name'].astype(str).str.strip()
    df['product_name'] = df['product_name'].replace(['nan', 'None', ''], np.nan)
    df['product_name'] = df['product_name'].fillna("Sản phẩm Guardian chưa cập nhật")
    
    # Hàm chuyển đổi thông minh (chỉ hạ chữ viết hoa toàn bộ để không hỏng từ như 3CE, AHA)
    def smart_title(text):
        if str(text).isupper():
            return text.title()
        return text
    
    df['product_name'] = df['product_name'].apply(smart_title)

    # --------------------------------------------------------------------------
    # 2. ĐIỀN KHUYẾT VÀ CHUẨN HÓA THƯƠNG HIỆU
    # --------------------------------------------------------------------------
    df['brand'] = df['brand'].astype(str).str.strip()
    df['brand'] = df['brand'].replace(['nan', 'None', ''], np.nan)
    
    for idx, row in df.iterrows():
        b_name = str(row['brand']).strip()
        p_name = str(row['product_name']).strip()
        
        # Nếu brand bị trống hoặc dính chữ nghi vấn (SON, KEM, v.v.)
        if pd.isna(row['brand']) or b_name.upper() in SUSPECT_BRANDS:
            found_brand = False
            for key, correct_brand in BRAND_MAPPING.items():
                if key in p_name.upper():
                    df.at[idx, 'brand'] = correct_brand
                    found_brand = True
                    break
            # Nếu quét vẫn không ra, đánh dấu "No Brand"
            if not found_brand:
                df.at[idx, 'brand'] = "No Brand"
        else:
            if b_name.upper() in BRAND_MAPPING:
                df.at[idx, 'brand'] = BRAND_MAPPING[b_name.upper()]

    # --------------------------------------------------------------------------
    # 3. TRIỆT TIÊU Ô TRỐNG Ở CỘT DUNG TÍCH (Lấp đầy 100%)
    # --------------------------------------------------------------------------
    df['volume_weight'] = df['volume_weight'].astype(str).str.strip()
    df['volume_weight'] = df['volume_weight'].replace(['nan', 'none', ''], np.nan)
    
    df['volume_val'] = np.nan
    df['volume_unit'] = ""
    
    for idx, row in df.iterrows():
        val, unit = extract_volume(row['volume_weight'] if pd.notna(row['volume_weight']) else row['product_name'], row['product_url'])
        df.at[idx, 'volume_val'] = float(val)
        df.at[idx, 'volume_unit'] = unit
        df.at[idx, 'volume_weight'] = f"{val}{unit}"

    # --------------------------------------------------------------------------
    # 4. CHUẨN HÓA GIÁ VÀ TỈ LỆ GIẢM (Sửa triệt để ca 21925)
    # --------------------------------------------------------------------------
    df['current_price'] = pd.to_numeric(df['current_price'], errors='coerce').fillna(0).abs()
    df['original_price'] = pd.to_numeric(df['original_price'], errors='coerce').fillna(0).abs()
    
    mask_fix_price = (df['original_price'] == 0) | (df['original_price'] < df['current_price'])
    df.loc[mask_fix_price, 'original_price'] = df.loc[mask_fix_price, 'current_price']
    
    df['discount_percent'] = np.where(
        df['original_price'] > 0,
        np.round(((df['original_price'] - df['current_price']) / df['original_price']) * 100, 1),
        0.0
    )

    # --------------------------------------------------------------------------
    # 5. TRIỆT TIÊU Ô TRỐNG ĐÁNH GIÁ (Lấp đầy Rating = 0.0)
    # --------------------------------------------------------------------------
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0.0)
    df['review_count'] = pd.to_numeric(df['review_count'], errors='coerce').fillna(0).astype(int)
    
    df.loc[df['review_count'] < 0, 'review_count'] = 0
    df['has_rating'] = np.where((df['rating'] > 0) & (df['review_count'] > 0), 1, 0)

    # --------------------------------------------------------------------------
    # 6. SẮP XẾP VÀ XUẤT FILE 
    # --------------------------------------------------------------------------
    df['category'] = df['category'].fillna('Chưa phân loại')
    df['product_id'] = df['product_id'].fillna('Unknown')

    final_cols = [
        'source', 'product_id', 'product_name', 'brand', 'category', 
        'volume_weight', 'volume_val', 'volume_unit', 
        'current_price', 'original_price', 'discount_percent', 
        'rating', 'review_count', 'has_rating', 'product_url'
    ]
    df = df[final_cols]
    
    # BẢO VỆ CHỐNG LỖI PERMISSION ERROR KHI LƯU FILE
    try:
        df.to_csv(OUTPUT_FILE, index=False, sep=",", encoding="utf-8-sig")
        print("=" * 70)
        print(f"🎉 HOÀN TẤT! Đã triệt tiêu toàn bộ chỗ trống.")
        print(f"   File Guardian sạch đặc 100% được lưu tại:\n   {OUTPUT_FILE}")
        print("=" * 70)
    except PermissionError:
        print("\n❌ LỖI QUYỀN TRUY CẬP: FILE ĐANG BỊ MỞ HOẶC KHÓA!")
        print(f"Không thể ghi đè lên file: {OUTPUT_FILE}")
        
        alt_file = OUTPUT_FILE.replace(".csv", "_new.csv")
        try:
            df.to_csv(alt_file, index=False, sep=";", encoding="utf-8-sig")
            print(f"\n✅ Đã tự động lưu dữ liệu sang file dự phòng:\n   {alt_file}")
            print("👉 Cách xử lý: Hãy đóng file Excel đang mở cũ, sau đó sử dụng file '_new.csv' này nhé.")
        except Exception as e:
            print(f"\n⚠️ Vẫn không thể lưu file. Lỗi hệ thống: {e}")
            print("👉 Vui lòng TẮT HẲN EXCEL và chạy lại script.")

if __name__ == "__main__":
    clean_guardian_data()