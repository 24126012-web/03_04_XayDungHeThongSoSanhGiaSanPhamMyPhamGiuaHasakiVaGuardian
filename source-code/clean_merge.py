
# ==============================================================
# 2.2. LAM SACH, CHUAN HOA VA GOP DU LIEU MY PHAM
# NGUON: GUARDIAN + HASAKI
# ==============================================================

# Cai thu vien neu chua co:
# pip install pandas numpy openpyxl

from pathlib import Path
import re
import unicodedata
import numpy as np
import pandas as pd


# ==============================================================
# 1. CAU HINH DUONG DAN
# ==============================================================

# File Python nam trong BIG DATA/source-code/clean_merge.py
BASE_DIR = Path(__file__).resolve().parent

# Lui len mot cap: BIG DATA/
PROJECT_DIR = BASE_DIR.parent

# Du lieu dau vao va dau ra deu nam trong BIG DATA/dataset/
DATASET_DIR = PROJECT_DIR / "dataset"

GUARDIAN_FILE = DATASET_DIR / "guardian_raw.csv"
HASAKI_FILE = DATASET_DIR / "hasaki_raw.csv"

OUTPUT_FILE = DATASET_DIR / "my_pham_cleaned_merged.xlsx"


# ==============================================================
# 2. CAC COT DU LIEU CHUAN
# ==============================================================

STANDARD_COLUMNS = [
    "product_id",
    "product_name",
    "brand",
    "category",
    "volume_weight",
    "current_price",
    "original_price",
    "discount_percent",
    "rating",
    "review_count",
]


# ==============================================================
# 3. CHUAN HOA TEN COT
# ==============================================================

def normalize_column_name(name):
    name = str(name).strip().lower()
    name = name.replace("\ufeff", "")
    name = remove_accents(name)
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


COLUMN_ALIASES = {
    "id": "product_id",
    "productid": "product_id",
    "product_id": "product_id",
    "sku": "product_id",
    "ma_san_pham": "product_id",

    "name": "product_name",
    "product": "product_name",
    "title": "product_name",
    "product_name": "product_name",
    "ten_san_pham": "product_name",

    "brand": "brand",
    "brand_name": "brand",
    "thuong_hieu": "brand",

    "category": "category",
    "category_name": "category",
    "danh_muc": "category",

    "volume": "volume_weight",
    "weight": "volume_weight",
    "size": "volume_weight",
    "volume_weight": "volume_weight",
    "dung_tich": "volume_weight",
    "khoi_luong": "volume_weight",

    "price": "current_price",
    "sale_price": "current_price",
    "current_price": "current_price",
    "gia": "current_price",
    "gia_ban": "current_price",

    "originalprice": "original_price",
    "original_price": "original_price",
    "old_price": "original_price",
    "list_price": "original_price",
    "gia_goc": "original_price",

    "discount": "discount_percent",
    "discount_percent": "discount_percent",
    "discount_percentage": "discount_percent",
    "discount_percent_": "discount_percent",
    "gia_tri_giam": "discount_percent",

    "rating": "rating",
    "stars": "rating",
    "star_rating": "rating",
    "danh_gia": "rating",

    "review": "review_count",
    "reviews": "review_count",
    "review_count": "review_count",
    "rating_count": "review_count",
    "num_reviews": "review_count",
    "so_luot_danh_gia": "review_count",
}


# ==============================================================
# 4. HAM LAM SACH VAN BAN
# ==============================================================

def remove_accents(value):
    value = unicodedata.normalize("NFD", str(value))
    value = "".join(
        char for char in value
        if unicodedata.category(char) != "Mn"
    )
    return value.replace("đ", "d").replace("Đ", "D")


def clean_text(value):
    if pd.isna(value):
        return np.nan

    value = str(value)
    value = value.replace("\ufeff", "")
    value = value.replace("\xa0", " ")
    value = re.sub(r"[\r\n\t]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    if value.lower() in {
        "", "nan", "none", "null", "n/a", "na", "-"
    }:
        return np.nan

    return value


# ==============================================================
# 5. DOC FILE CSV
# ==============================================================

def read_csv_file(file_path):
    if not file_path.exists():
        raise FileNotFoundError(
            f"\nKhong tim thay file:\n{file_path}\n"
            "Hay kiem tra lai ten file va thu muc dataset."
        )

    df = None
    errors = []

    # Thu cac encoding va dau phan cach thong dung
    for encoding in ["utf-8-sig", "utf-8", "cp1258", "latin1"]:
        for separator in [",", ";", "\t"]:
            try:
                temp = pd.read_csv(
                    file_path,
                    sep=separator,
                    dtype=str,
                    encoding=encoding,
                    on_bad_lines="error"
                )

                # Chap nhan file co nhieu cot
                if len(temp.columns) > 1:
                    df = temp
                    break

            except (UnicodeDecodeError, pd.errors.ParserError) as e:
                errors.append(str(e))

        if df is not None:
            break

    if df is None:
        raise ValueError(
            f"Khong doc duoc file: {file_path}\n"
            "Kiem tra dinh dang CSV, encoding va dau phan cach."
        )

    # Chuan hoa ten cot va anh xa ve ten chuan
    renamed_columns = {}

    for col in df.columns:
        normalized = normalize_column_name(col)
        renamed_columns[col] = COLUMN_ALIASES.get(
            normalized, normalized
        )

    df = df.rename(columns=renamed_columns)

    # Neu nhieu cot cung duoc anh xa vao mot ten chuan,
    # uu tien cot co du lieu, khong ghi de du lieu bang cot rong.
    if df.columns.duplicated().any():
        new_df = pd.DataFrame(index=df.index)

        for col in dict.fromkeys(df.columns):
            same_name = df.loc[:, df.columns == col]

            if same_name.shape[1] == 1:
                new_df[col] = same_name.iloc[:, 0]
            else:
                new_df[col] = same_name.bfill(axis=1).iloc[:, 0]

        df = new_df

    # Dam bao cac cot chuan deu ton tai
    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    # Luu lai cac cot khong su dung de kiem tra nguon
    return df[STANDARD_COLUMNS].copy()


# ==============================================================
# 6. CHUYEN CHUOI SANG SO
# ==============================================================

def parse_number(value):
    if pd.isna(value):
        return np.nan

    s = str(value).strip().lower()

    if s in {"", "nan", "none", "null", "n/a", "-", "na"}:
        return np.nan

    s = (
        s.replace("₫", "")
         .replace("đ", "")
         .replace("vnđ", "")
         .replace("vnd", "")
         .replace("%", "")
         .replace(" ", "")
    )

    # Xu ly dinh dang so co ca dau phay va dau cham
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            # Vi du 1.250,50 -> 1250.50
            s = s.replace(".", "").replace(",", ".")
        else:
            # Vi du 1,250.50 -> 1250.50
            s = s.replace(",", "")

    elif "," in s:
        parts = s.split(",")

        if len(parts) > 1 and len(parts[-1]) == 3:
            # Vi du 125,000 -> 125000
            s = "".join(parts)
        else:
            s = s.replace(",", ".")

    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):
        # Vi du 125.000 -> 125000
        s = s.replace(".", "")

    s = re.sub(r"[^0-9.\-]", "", s)

    try:
        return float(s)
    except (ValueError, TypeError):
        return np.nan


# ==============================================================
# 7. CHUAN HOA DANH MUC
# ==============================================================

def normalize_category(value):
    if pd.isna(value):
        return "Chưa phân loại"

    category = remove_accents(str(value).lower().strip())

    if any(x in category for x in [
        "trang diem", "makeup", "make up"
    ]):
        return "Trang điểm"

    if any(x in category for x in [
        "cham soc toc", "hair care", "haircare",
        "dau goi", "duong toc"
    ]):
        return "Chăm sóc tóc"

    if any(x in category for x in [
        "cham soc ca nhan", "personal care",
        "ve sinh ca nhan", "body care"
    ]):
        return "Chăm sóc cá nhân"

    if any(x in category for x in [
        "cham soc da", "skincare", "skin care",
        "mat na", "sua rua mat", "duong da"
    ]):
        return "Chăm sóc da mặt"

    return "Chưa phân loại"


# ==============================================================
# 8. CHUAN HOA DUNG TICH VA KHOI LUONG
# ==============================================================

def normalize_volume(value):
    if pd.isna(value):
        return np.nan

    value = str(value).strip().lower()
    value = re.sub(r"\s+", " ", value)

    value = re.sub(r"\bgr\b", "g", value)
    value = re.sub(r"\bgam\b", "g", value)

    value = re.sub(
        r"(\d+(?:[.,]\d+)?)\s*(ml|mg|kg|g|l)\b",
        r"\1 \2",
        value
    )

    return value if value else np.nan


# ==============================================================
# 9. LAM SACH MOT NGUON DU LIEU
# ==============================================================

def clean_source(file_path, source_name):
    print("\n" + "=" * 60)
    print(f"DANG XU LY: {source_name}")
    print("=" * 60)

    df = read_csv_file(file_path)
    rows_before = len(df)

    # Bao cao truoc lam sach
    missing_name_before = int(
        df["product_name"].map(clean_text).isna().sum()
    )

    # 9.1 Lam sach van ban
    text_columns = [
        "product_id", "product_name", "brand",
        "category", "volume_weight"
    ]

    for col in text_columns:
        df[col] = df[col].map(clean_text)

    # 9.2 Gan nguon du lieu
    df["source"] = source_name

    # 9.3 Loai dong khong co ten san pham
    df = df.dropna(subset=["product_name"]).copy()

    # 9.4 Chuan hoa danh muc va dung tich
    df["category"] = df["category"].map(normalize_category)
    df["volume_weight"] = df["volume_weight"].map(normalize_volume)

    # 9.5 Chuyen cac cot so
    numeric_columns = [
        "current_price", "original_price",
        "discount_percent", "rating", "review_count"
    ]

    for col in numeric_columns:
        df[col] = df[col].map(parse_number)

    # 9.6 Gia phai lon hon 0
    for col in ["current_price", "original_price"]:
        df.loc[df[col] <= 0, col] = np.nan

    # 9.7 Rating hop le trong khoang 1-5
    df.loc[
        ~df["rating"].between(1, 5),
        "rating"
    ] = np.nan

    # 9.8 Review count khong duoc am
    df.loc[df["review_count"] < 0, "review_count"] = np.nan
    df["review_count"] = df["review_count"].round().astype("Int64")

    # 9.9 Kiem tra discount
    # Neu co du gia goc va gia hien tai, tinh lai discount
    has_both_prices = (
        df["current_price"].notna()
        & df["original_price"].notna()
    )

    lower_price = (
        has_both_prices
        & (df["original_price"] > df["current_price"])
    )

    equal_price = (
        has_both_prices
        & (df["original_price"] == df["current_price"])
    )

    higher_current_price = (
        has_both_prices
        & (df["original_price"] < df["current_price"])
    )

    df.loc[lower_price, "discount_percent"] = (
        (
            df.loc[lower_price, "original_price"]
            - df.loc[lower_price, "current_price"]
        )
        / df.loc[lower_price, "original_price"]
        * 100
    ).round(1)

    df.loc[equal_price, "discount_percent"] = 0.0

    # Gia hien tai lon hon gia goc: khong tinh discount
    df.loc[higher_current_price, "discount_percent"] = np.nan

    # Discount nam ngoai 0-100 la khong hop le
    df.loc[
        ~df["discount_percent"].between(0, 100),
        "discount_percent"
    ] = np.nan

    # 9.10 Tao co danh dau du lieu rating/review dang nghi
    # Khong tu dong xoa rating=1 va review_count=1.
    # Chi danh dau de nguoi dung kiem tra lai.
    df["quality_flag"] = ""

    suspicious = (
        df["rating"].eq(1)
        & df["review_count"].eq(1)
    )

    df.loc[suspicious, "quality_flag"] = (
        "Kiem tra rating=1 va review_count=1"
    )

    # 9.11 Loai ban ghi trung trong cung website
    def make_key(series):
        return (
            series.fillna("")
            .astype(str)
            .str.lower()
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

    df["_name_key"] = make_key(df["product_name"])
    df["_brand_key"] = make_key(df["brand"])
    df["_category_key"] = make_key(df["category"])

    duplicate_mask = df.duplicated(
        subset=[
            "source",
            "_name_key",
            "_brand_key",
            "_category_key"
        ],
        keep="first"
    )

    duplicate_removed = int(duplicate_mask.sum())
    df = df.loc[~duplicate_mask].copy()

    # 9.12 Tao ma ban ghi rieng cho tung website
    df["record_id"] = (
        df["source"].str.lower()
        + "_"
        + df["product_id"].astype(str)
    )

    # 9.13 Chuan hoa kieu du lieu cuoi cung
    df["current_price"] = df["current_price"].round(0).astype("Int64")
    df["original_price"] = df["original_price"].round(0).astype("Int64")
    df["discount_percent"] = df["discount_percent"].round(1)
    df["rating"] = df["rating"].round(1)

    # Sap xep cot dau ra
    final_columns = [
        "record_id",
        "product_id",
        "product_name",
        "brand",
        "category",
        "volume_weight",
        "current_price",
        "original_price",
        "discount_percent",
        "rating",
        "review_count",
        "source",
        "quality_flag"
    ]

    df = df[final_columns].reset_index(drop=True)

    # 9.14 Tao bao cao
    report = {
        "Nguồn": source_name,
        "Số dòng ban đầu": rows_before,
        "Dòng thiếu tên trước xử lý": missing_name_before,
        "Dòng trùng đã loại": duplicate_removed,
        "Số dòng sau làm sạch": len(df),
        "Số dòng cần kiểm tra rating/review": int(
            df["quality_flag"].ne("").sum()
        ),
        "Thiếu thương hiệu": int(df["brand"].isna().sum()),
        "Thiếu giá hiện tại": int(df["current_price"].isna().sum()),
        "Thiếu giá gốc": int(df["original_price"].isna().sum()),
        "Thiếu giảm giá": int(df["discount_percent"].isna().sum()),
        "Thiếu rating": int(df["rating"].isna().sum()),
        "Thiếu review_count": int(df["review_count"].isna().sum())
    }

    print(f"So dong ban dau: {rows_before:,}")
    print(f"So dong trung da loai: {duplicate_removed:,}")
    print(f"So dong sau lam sach: {len(df):,}")

    return df, report


# ==============================================================
# 10. XUAT FILE EXCEL VA DINH DANG
# ==============================================================

def export_excel(merged, reports):
    # Bao cao tong hop
    report_df = pd.DataFrame(reports)

    # Thong ke gia tri thieu
    missing_df = pd.DataFrame({
        "Tên cột": merged.columns,
        "Số giá trị thiếu": [
            int(merged[col].isna().sum())
            for col in merged.columns
        ],
        "Tỷ lệ thiếu (%)": [
            round(merged[col].isna().mean() * 100, 2)
            for col in merged.columns
        ]
    })

    # Thong ke danh muc theo nguon
    category_df = (
        merged.groupby(["source", "category"], dropna=False)
        .size()
        .reset_index(name="Số sản phẩm")
    )

    # Thong ke tong quan tung website
    source_df = (
        merged.groupby("source")
        .agg(
            So_san_pham=("product_id", "count"),
            So_thuong_hieu=("brand", "nunique"),
            Gia_trung_binh=("current_price", "mean"),
            Rating_trung_binh=("rating", "mean"),
            So_san_pham_co_rating=("rating", "count"),
            So_san_pham_co_review=("review_count", "count")
        )
        .reset_index()
    )

    # Dam bao thu muc ton tai
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    # Ghi file Excel
    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl"
    ) as writer:

        merged.to_excel(
            writer, sheet_name="Du_lieu_sach", index=False
        )

        report_df.to_excel(
            writer, sheet_name="Bao_cao_lam_sach", index=False
        )

        missing_df.to_excel(
            writer, sheet_name="Thong_ke_thieu", index=False
        )

        category_df.to_excel(
            writer, sheet_name="Thong_ke_danh_muc", index=False
        )

        source_df.to_excel(
            writer, sheet_name="Tong_quan_nguon", index=False
        )

        # Dinh dang cac sheet
        for ws in writer.book.worksheets:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions

            for cells in ws.columns:
                max_length = max(
                    len(str(cell.value))
                    if cell.value is not None else 0
                    for cell in cells
                )

                ws.column_dimensions[
                    cells[0].column_letter
                ].width = min(max(max_length + 2, 12), 45)

        # Dinh dang cot gia tien, rating va discount
        ws = writer.book["Du_lieu_sach"]

        header_map = {
            cell.value: cell.column
            for cell in ws[1]
        }

        for col in ["current_price", "original_price"]:
            if col in header_map:
                for row in range(2, ws.max_row + 1):
                    ws.cell(
                        row, header_map[col]
                    ).number_format = '#,##0'

        for col in ["discount_percent", "rating"]:
            if col in header_map:
                for row in range(2, ws.max_row + 1):
                    ws.cell(
                        row, header_map[col]
                    ).number_format = '0.0'


# ==============================================================
# 11. CHUONG TRINH CHINH
# ==============================================================

def main():
    print("=" * 65)
    print("CHUONG TRINH LAM SACH VA GOP DU LIEU MY PHAM")
    print("=" * 65)

    print(f"Thu muc du lieu: {DATASET_DIR}")
    print(f"File Guardian: {GUARDIAN_FILE}")
    print(f"File Hasaki:   {HASAKI_FILE}")
    print(f"File ket qua:  {OUTPUT_FILE}")

    # Kiem tra duong dan
    if not DATASET_DIR.exists():
        raise FileNotFoundError(
            f"\nKhong tim thay thu muc dataset:\n{DATASET_DIR}\n"
            "Hay kiem tra cau truc thu muc BIG DATA."
        )

    if not GUARDIAN_FILE.exists():
        raise FileNotFoundError(
            f"\nKhong tim thay file Guardian:\n{GUARDIAN_FILE}"
        )

    if not HASAKI_FILE.exists():
        raise FileNotFoundError(
            f"\nKhong tim thay file Hasaki:\n{HASAKI_FILE}"
        )

    # Lam sach Guardian
    guardian, guardian_report = clean_source(
        GUARDIAN_FILE, "Guardian"
    )

    # Lam sach Hasaki
    hasaki, hasaki_report = clean_source(
        HASAKI_FILE, "Hasaki"
    )

    # Gop hai nguon
    # Khong xoa san pham trung giua hai website
    merged = pd.concat(
        [guardian, hasaki],
        ignore_index=True
    )

    # Xuat Excel
    export_excel(
        merged,
        [guardian_report, hasaki_report]
    )

    # Bao cao ket qua
    print("\n" + "=" * 65)
    print("HOAN TAT LAM SACH VA GOP DU LIEU")
    print("=" * 65)
    print(f"Guardian sau lam sach: {len(guardian):,} dong")
    print(f"Hasaki sau lam sach:   {len(hasaki):,} dong")
    print(f"Tong so ban ghi:       {len(merged):,} dong")
    print(f"\nFile Excel da luu tai:\n{OUTPUT_FILE}")
    print("=" * 65)


if __name__ == "__main__":
    main()
