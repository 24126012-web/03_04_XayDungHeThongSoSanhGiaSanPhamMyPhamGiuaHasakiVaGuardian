import os
import re
import pandas as pd
from difflib import SequenceMatcher

# ==============================================================================
# 1. ĐƯỜNG DẪN DỮ LIỆU
# ==============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
DATASET_DIR = os.path.join(PROJECT_DIR, "dataset")

# Tự động tìm tệp merged_data.csv
if os.path.exists(os.path.join(DATASET_DIR, "merged_data.csv")):
    INPUT_FILE = os.path.join(DATASET_DIR, "merged_data.csv")
    OUTPUT_FILE = os.path.join(DATASET_DIR, "matched_products.csv")
else:
    INPUT_FILE = os.path.join(CURRENT_DIR, "merged_data.csv")
    OUTPUT_FILE = os.path.join(CURRENT_DIR, "matched_products.csv")

print(f"⏳ Đang đọc dữ liệu từ: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE, sep=";", encoding="utf-8-sig")

# ==============================================================================
# 2. CHUẨN HÓA BRAND & LÀM SẠCH VĂN BẢN
# ==============================================================================
def normalize_brand(b):
    if pd.isna(b): 
        return "Khác"
    b_clean = str(b).strip()
    b_upper = b_clean.upper()
    
    mapping = {
        "L'OREAL PARIS": "L'Oreal",
        "L'ORÉAL PARIS": "L'Oreal",
        "L'OREAL PROFESSIONNEL": "L'Oreal",
        "L'OREAL PROFESSIONNEL PARIS": "L'Oreal",
        "L'OREAL": "L'Oreal",
        "MAYBELLINE NEW YORK": "Maybelline",
        "MAYBELLINE": "Maybelline",
        "BOM": "B.O.M",
        "B.O.M": "B.O.M",
        "LA ROCHE POSAY": "La Roche-Posay",
        "LA ROCHE-POSAY": "La Roche-Posay",
        "MANNINGS GUARDIAN": "Mannings",
        "COCOON": "Cocoon",
        "NIVEA": "Nivea",
        "VASELINE": "Vaseline",
        "BIODERMA": "Bioderma",
        "SENKA": "Senka",
        "ANESSA": "Anessa",
        "CETAPHIL": "Cetaphil",
        "SUNPLAY": "Sunplay",
        "ROHTO": "Rohto",
        "HADA LABO": "Hada Labo",
        "DOVE": "Dove",
        "TRESEMME": "Tresemme",
        "CLEAR": "Clear",
        "PANTENE": "Pantene",
        "HEAD & SHOULDERS": "Head & Shoulders",
        "COLGATE": "Colgate",
        "P/S": "P/S",
        "CLOSEUP": "Closeup",
        "ORAL-B": "Oral-B",
        "LISTERINE": "Listerine",
        "KOTEX": "Kotex",
        "DIANA": "Diana",
        "LAURIER": "Laurier",
        "SILCOT": "Silcot",
        "JOMI": "Jomi"
    }
    if b_upper in mapping:
        return mapping[b_upper]
    return b_clean.title()

def clean_text(text):
    if pd.isna(text): 
        return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    stopwords = {'cho', 'da', 'dưỡng', 'chính', 'hãng', 'và', 'làm', 'sạch', 'cao', 'cấp', 'mới'}
    return " ".join([w for w in tokens if w not in stopwords])

# Áp dụng chuẩn hóa
df['brand_norm'] = df['brand'].apply(normalize_brand)
df_h = df[df['source'] == 'Hasaki'].copy()
df_g = df[df['source'] == 'Guardian'].copy()

df_h['clean_name'] = df_h['product_name'].apply(clean_text)
df_g['clean_name'] = df_g['product_name'].apply(clean_text)

# Tìm các thương hiệu chung giữa 2 sàn
common_brands = set(df_h['brand_norm']).intersection(set(df_g['brand_norm']))
shared_brands = [b for b in common_brands if b not in ['', 'Khác', 'Mannings', 'No Brand']]

# ==============================================================================
# 3. THUẬT TOÁN GHÉP CẶP SẢN PHẨM (FUZZY MATCHING)
# ==============================================================================
print("⏳ Đang tiến hành ghép cặp sản phẩm tương đương...")
matched_pairs = []

for brand in shared_brands:
    sub_h = df_h[df_h['brand_norm'] == brand]
    sub_g = df_g[df_g['brand_norm'] == brand]
    
    for _, rh in sub_h.iterrows():
        best_match = None
        best_score = 0.0
        for _, rg in sub_g.iterrows():
            # Kiểm tra tương đồng về dung tích/khối lượng
            vh, vg = rh['volume_val'], rg['volume_val']
            if pd.notna(vh) and pd.notna(vg) and vh > 0 and vg > 0:
                if abs(vh - vg) > 0.01:
                    continue  # Bỏ qua nếu khác dung tích
            
            score = SequenceMatcher(None, rh['clean_name'], rg['clean_name']).ratio()
            if score > best_score:
                best_score = score
                best_match = rg
                
        # Ngưỡng tương đồng tối thiểu 55%
        if best_match is not None and best_score >= 0.55:
            gia_h = int(rh['current_price'])
            gia_g = int(best_match['current_price'])
            chenh_lech = gia_g - gia_h
            
            matched_pairs.append({
                'product_name_hasaki': rh['product_name'],
                'product_name_guardian': best_match['product_name'],
                'brand': brand,
                'category': rh['category'],
                'volume_weight': rh['volume_weight'],
                'gia_hasaki': gia_h,
                'gia_guardian': gia_g,
                'chenh_lech_gia': chenh_lech,
                'ben_re_hon': 'Hasaki rẻ hơn' if chenh_lech > 0 else ('Guardian rẻ hơn' if chenh_lech < 0 else 'Bằng giá'),
                'url_hasaki': rh['product_url'],
                'url_guardian': best_match['product_url']
            })

df_res = pd.DataFrame(matched_pairs)
# Loại bỏ trùng lặp sản phẩm bên Guardian (chỉ chọn sản phẩm có độ tương đồng cao nhất)
df_res = df_res.drop_duplicates(subset=['product_name_guardian'])

# Lưu tệp CSV chuẩn UTF-8 có BOM để mở bằng Excel/Power BI không bị lỗi font
df_res.to_csv(OUTPUT_FILE, sep=';', index=False, encoding='utf-8-sig')

print(f"🎉 Đã xuất thành công {len(df_res):,} sản phẩm ghép cặp!")
print(f"📁 Tệp kết quả lưu tại: {OUTPUT_FILE}")
