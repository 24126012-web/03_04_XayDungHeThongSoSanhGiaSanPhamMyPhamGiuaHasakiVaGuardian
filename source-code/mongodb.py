import os
import pandas as pd
from pymongo import MongoClient, ASCENDING, TEXT

# ==============================================================================
# 1. CẤU HÌNH KẾT NỐI MONGODB & ĐƯỜNG DẪN DỮ LIỆU
# ==============================================================================
MONGO_URI = "mongodb+srv://24126012_db_user:AL1501@cluster0.wl44gdr.mongodb.net/"
DB_NAME = "cosmetics_db"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
DATASET_DIR = os.path.join(PROJECT_DIR, "dataset")

# Tự động tìm file merged_data.csv trong thư mục dataset hoặc cùng thư mục
if os.path.exists(os.path.join(DATASET_DIR, "merged_data.csv")):
    INPUT_FILE = os.path.join(DATASET_DIR, "merged_data.csv")
else:
    INPUT_FILE = os.path.join(CURRENT_DIR, "merged_data.csv")

# ==============================================================================
# 2. HÀM CHUẨN HÓA THƯƠNG HIỆU (GỘP CÁC BIẾN THỂ CỦA 2 SÀN)
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

def load_data_to_mongodb():
    print("=" * 80)
    print(" BẮT ĐẦU NẠP DỮ LIỆU ĐÃ CHUẨN HÓA VÀO MONGODB")
    print("=" * 80)

    # Kiểm tra file dữ liệu
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Không tìm thấy tệp: {INPUT_FILE}")
        return

    # Kết nối MongoDB
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client[DB_NAME]
        print(f"✅ Kết nối MongoDB thành công! Cơ sở dữ liệu: '{DB_NAME}'\n")
    except Exception as e:
        print(f"❌ Lỗi kết nối MongoDB: {e}")
        print("👉 Vui lòng mở MongoDB Compass hoặc kiểm tra đường truyền mạng.")
        return

    # Dọn dẹp collection users cũ nếu có
    db.drop_collection("users")

    # Đọc dữ liệu
    df = pd.read_csv(INPUT_FILE, sep=",", encoding="utf-8-sig", dtype={"product_id": str, "source": str})
    
    # --------------------------------------------------------------------------
    # CHUẨN HÓA DỮ LIỆU TRƯỚC KHI ĐẨY LÊN DATABASE
    # --------------------------------------------------------------------------
    print("🧹 Đang thực hiện chuẩn hóa Brand và Volume Unit...")
    df["brand"] = df["brand"].apply(normalize_brand)
    
    # Gom các đơn vị tính đóng gói lẻ về combo/sp
    df["volume_unit"] = df["volume_unit"].replace({
        "set": "combo",
        "cặp": "combo",
        "hộp": "combo",
        "chai": "sp"
    })
    print(f"📊 Đã chuẩn hóa xong {len(df):,} bản ghi từ: {os.path.basename(INPUT_FILE)}")

    # --------------------------------------------------------------------------
    # COLLECTION 1: products
    # --------------------------------------------------------------------------
    print("\n[1/3] Đang tạo và nạp Collection 'products'...")
    col_products = db["products"]
    col_products.drop()

    docs_products = []
    for _, row in df.iterrows():
        source_str = str(row["source"]).strip()
        product_id_str = str(row["product_id"]).strip()
        doc_id = f"{source_str[0]}_{product_id_str}"

        doc = {
            "_id": str(doc_id),
            "source": source_str,
            "product_id": str(product_id_str),
            "product_name": row["product_name"],
            "brand": row["brand"],
            "category": row["category"],
            "specifications": {
                "volume_weight": row["volume_weight"],
                "volume_val": float(row["volume_val"]),
                "volume_unit": row["volume_unit"]
            },
            "pricing": {
                "current_price": int(row["current_price"]),
                "original_price": int(row["original_price"]),
                "discount_percent": float(row["discount_percent"])
            },
            "ratings": {
                "rating": float(row["rating"]),
                "review_count": int(row["review_count"]),
                "has_rating": int(row["has_rating"])
            },
            "product_url": row["product_url"]
        }
        docs_products.append(doc)

    if docs_products:
        col_products.insert_many(docs_products)

    # Tạo Index
    col_products.create_index([("brand", ASCENDING), ("category", ASCENDING)])
    col_products.create_index([("pricing.current_price", ASCENDING)])
    col_products.create_index([("product_name", TEXT)])
    print(f"  -> Đã nạp thành công {len(docs_products):,} sản phẩm.")

    # --------------------------------------------------------------------------
    # COLLECTION 2: category_analytics
    # --------------------------------------------------------------------------
    print("\n[2/3] Đang tính toán và nạp Collection 'category_analytics'...")
    col_category = db["category_analytics"]
    col_category.drop()

    categories = df["category"].unique()
    docs_category = []

    for cat in categories:
        cat_str = str(cat)
        df_cat = df[df["category"] == cat]
        df_h = df_cat[df_cat["source"] == "Hasaki"]
        df_g = df_cat[df_cat["source"] == "Guardian"]

        doc_cat = {
            "_id": cat_str,
            "category_name": cat_str,
            "total_products": len(df_cat),
            "price_overall": {
                "min_price": int(df_cat["current_price"].min()),
                "max_price": int(df_cat["current_price"].max()),
                "avg_price": round(float(df_cat["current_price"].mean()), 2)
            },
            "hasaki_stats": {
                "product_count": len(df_h),
                "min_price": int(df_h["current_price"].min()) if len(df_h) > 0 else 0,
                "max_price": int(df_h["current_price"].max()) if len(df_h) > 0 else 0,
                "avg_price": round(float(df_h["current_price"].mean()), 2) if len(df_h) > 0 else 0,
                "avg_discount": round(float(df_h["discount_percent"].mean()), 2) if len(df_h) > 0 else 0
            },
            "guardian_stats": {
                "product_count": len(df_g),
                "min_price": int(df_g["current_price"].min()) if len(df_g) > 0 else 0,
                "max_price": int(df_g["current_price"].max()) if len(df_g) > 0 else 0,
                "avg_price": round(float(df_g["current_price"].mean()), 2) if len(df_g) > 0 else 0,
                "avg_discount": round(float(df_g["discount_percent"].mean()), 2) if len(df_g) > 0 else 0
            }
        }
        docs_category.append(doc_cat)

    if docs_category:
        col_category.insert_many(docs_category)
    print(f"  -> Đã nạp {len(docs_category)} ngành hàng.")

    # --------------------------------------------------------------------------
    # COLLECTION 3: brand_analytics
    # --------------------------------------------------------------------------
    print("\n[3/3] Đang tổng hợp và nạp Collection 'brand_analytics'...")
    col_brand = db["brand_analytics"]
    col_brand.drop()

    brand_counts = df["brand"].value_counts()
    major_brands = brand_counts[brand_counts >= 5].index

    docs_brand = []
    for b in major_brands:
        b_str = str(b)
        df_b = df[df["brand"] == b]
        df_b_h = df_b[df_b["source"] == "Hasaki"]
        df_b_g = df_b[df_b["source"] == "Guardian"]

        doc_b = {
            "_id": b_str,
            "brand_name": b_str,
            "total_products": len(df_b),
            "sources_distribution": df_b["source"].value_counts().to_dict(),
            "overall_stats": {
                "min_price": int(df_b["current_price"].min()),
                "max_price": int(df_b["current_price"].max()),
                "avg_price": round(float(df_b["current_price"].mean()), 2),
                "avg_discount": round(float(df_b["discount_percent"].mean()), 2)
            },
            "avg_price_by_source": {
                "Hasaki": round(float(df_b_h["current_price"].mean()), 2) if len(df_b_h) > 0 else None,
                "Guardian": round(float(df_b_g["current_price"].mean()), 2) if len(df_b_g) > 0 else None
            }
        }
        docs_brand.append(doc_b)

    if docs_brand:
        col_brand.insert_many(docs_brand)
    print(f"  -> Đã nạp {len(docs_brand)} thương hiệu tiêu biểu (đã gộp chuẩn hóa).")

    print("\n" + "=" * 80)
    print("🎉 HOÀN TẤT NẠP DỮ LIỆU!")
    print(f"   Cơ sở dữ liệu : {DB_NAME}")
    print(f"   Danh sách     : ['products', 'category_analytics', 'brand_analytics']")
    print("=" * 80)

if __name__ == "__main__":
    load_data_to_mongodb()