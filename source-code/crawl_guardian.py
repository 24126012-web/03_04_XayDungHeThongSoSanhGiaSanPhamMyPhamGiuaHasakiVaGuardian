import os, re, time, pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 1.CẤU HÌNH 4 DANH MỤC 
CATEGORIES = [
    {
        "name": "Chăm sóc da",
        "url": "https://www.guardian.com.vn/cham-soc-da-mat.html",
        "pages": 39,
    },
    {
        "name": "Trang điểm",
        "url": "https://www.guardian.com.vn/trang-diem.html",
        "pages": 39,
    },
    {
        "name": "Chăm sóc tóc",
        "url": "https://www.guardian.com.vn/cham-soc-toc.html",
        "pages": 27,
    },
    {
        "name": "Chăm sóc cá nhân",
        "url": "https://www.guardian.com.vn/cham-soc-ca-nhan.html",
        "pages": 25,
    },
]

OUT_FILE = "../dataset/guardian_raw.csv"
os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

# Thứ tự cột 
COLUMNS_ORDER = [
    "product_id", "product_name", "brand", "category", "volume_weight",
    "current_price", "original_price", "discount_percent",
    "rating", "review_count", "source", "product_url"
]

# 2.KHỞI TẠO TRÌNH DUYỆT
options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"},
)
driver.maximize_window()

def clean(t): return re.sub(r"\s+", " ", str(t or "")).strip()

# 3.HÀM CÀO URL TỪ TRANG DANH SÁCH
def get_product_urls(base_url, page_num, category_name):
    url = f"{base_url}?p={page_num}"
    print(f"  [URL] {category_name} - Trang {page_num:02d}: {url}", end=" ")
    driver.get(url)
    time.sleep(2.5)

    # Cuộn trang để lazy-load
    driver.execute_script("window.scrollTo(0, 1000);")
    time.sleep(0.5)
    driver.execute_script("window.scrollTo(0, 2500);")
    time.sleep(1)

    urls = []
    links = driver.find_elements(By.CSS_SELECTOR, "a.product-item-link, a.product-item-photo")
    for link in links:
        href = link.get_attribute("href")
        if href and href.endswith(".html") and href not in urls:
            urls.append(href)

    print(f"→ {len(urls)} URL")
    return urls

# 4.HÀM CÀO CHI TIẾT TỪNG SẢN PHẨM
def crawl_detail(url, category_name):
    driver.get(url)
    time.sleep(2)

    record = {
        "product_id": None,
        "product_name": None,
        "brand": None,
        "category": category_name,
        "volume_weight": None,
        "current_price": None,
        "original_price": None,
        "discount_percent": 0.0,
        "rating": None,
        "review_count": 0,
        "source": "Guardian",
        "product_url": url,
    }

    try:
        # 1. Product ID
        try:
            elem = driver.find_element(By.CSS_SELECTOR, "[data-product-id]")
            record["product_id"] = int(elem.get_attribute("data-product-id"))
        except:
            try:
                input_elem = driver.find_element(By.CSS_SELECTOR, "input[name='product']")
                record["product_id"] = int(input_elem.get_attribute("value"))
            except:
                pass

        # 2. Tên sản phẩm
        try:
            record["product_name"] = clean(driver.find_element(By.CSS_SELECTOR, "h1.page-title span.base").text)
        except:
            record["product_name"] = clean(driver.title.split("|")[0])

        # 3. Brand
        try:
            record["brand"] = clean(driver.find_element(By.CSS_SELECTOR, "#logo_name_brand span.brand-name").text)
        except:
            record["brand"] = record["product_name"].split()[0] if record["product_name"] else None

        # 4. Giá & Discount
        try:
            price_elem = driver.find_element(By.CSS_SELECTOR, ".price")
            record["current_price"] = int(re.sub(r"\D", "", price_elem.text))

            try:
                old_price_elem = driver.find_element(By.CSS_SELECTOR, ".old-price .price")
                temp_old_price = int(re.sub(r"\D", "", old_price_elem.text))
                if temp_old_price > record["current_price"]:
                    record["original_price"] = temp_old_price
            except:
                pass

            if record["current_price"] and not record["original_price"]:
                page_text = driver.find_element(By.TAG_NAME, "body").text
                prices = re.findall(r"([\d,]{5,})", page_text)
                valid_prices = [int(re.sub(r"\D", "", p)) for p in prices if int(re.sub(r"\D", "", p)) > record["current_price"]]
                if valid_prices:
                    record["original_price"] = min(valid_prices)

            if record["original_price"] and record["current_price"]:
                record["discount_percent"] = round(
                    ((record["original_price"] - record["current_price"]) / record["original_price"]) * 100, 1
                )
        except:
            pass

        # 5. Rating & Review
        page_text = driver.find_element(By.TAG_NAME, "body").text
        try:
            review_link = driver.find_element(By.CSS_SELECTOR, ".reviews-actions a.action.view")
            m_review = re.search(r"(\d+)", review_link.text.strip())
            if m_review:
                record["review_count"] = int(m_review.group(1))
        except:
            pass

        if record["review_count"] > 0:
            try:
                rating_elem = driver.find_element(By.CSS_SELECTOR, ".rating-result")
                title = rating_elem.get_attribute("title") or ""
                m_rating = re.search(r"(\d+(?:[.,]\d+)?)%", title)
                if m_rating:
                    pct = float(m_rating.group(1).replace(",", "."))
                    if pct > 0:
                        record["rating"] = round((pct / 100.0) * 5.0, 1)
            except:
                pass

        # 6. Volume
        if record["product_name"]:
            m_vol = re.search(
                r"\b\d+(?:[.,]\d+)?\s*(?:ml|kg|g|lít|lit|l|miếng|viên|que|cây)\b",
                record["product_name"], re.I
            )
            if m_vol:
                record["volume_weight"] = m_vol.group(0).lower()

    except Exception as e:
        print(f"Lỗi: {e}", end=" ")

    return record

# 5. CHẠY CHÍNH
print("=" * 60)
print("CÀO GUARDIAN - DA 39 TRANG | TRANG ĐIỂM 39 | TÓC 27 | CÁ NHÂN 25")
print("=" * 60)

all_records = []
seen_ids = set()

for cat in CATEGORIES:
    print(f"\n{'='*60}")
    print(f"DANH MỤC: {cat['name']} ({cat['pages']} trang)")
    print(f"{'='*60}")

    # Bước 1: Lấy URL từ các trang
    all_urls = []
    for p in range(1, cat["pages"] + 1):
        urls = get_product_urls(cat["url"], p, cat["name"])
        all_urls.extend(urls)

    # Loại bỏ URL trùng lặp trong danh mục
    all_urls = list(dict.fromkeys(all_urls))
    print(f"📌 {cat['name']}: {len(all_urls)} URL sản phẩm duy nhất.\n")

    # Bước 2: Cào chi tiết
    for i, url in enumerate(all_urls, 1):
        print(f"  [{i}/{len(all_urls)}] {url.split('/')[-1][:40]}...", end=" ")
        record = crawl_detail(url, cat["name"])

        # Kiểm tra trùng ID
        if record["product_id"] and record["product_id"] in seen_ids:
            print(f"⚠️ Trùng ID {record['product_id']}, bỏ qua.")
            continue

        all_records.append(record)
        if record["product_id"]:
            seen_ids.add(record["product_id"])

        print(f"ID: {record['product_id']} | Giá: {record['current_price']} | Review: {record['review_count']}")

        # Lưu checkpoint mỗi 50 sản phẩm
        if len(all_records) % 50 == 0:
            df_temp = pd.DataFrame(all_records)
            for col in COLUMNS_ORDER:
                if col not in df_temp.columns:
                    df_temp[col] = None
            df_temp = df_temp[COLUMNS_ORDER]
            df_temp.to_csv(OUT_FILE, sep=";", index=False, encoding="utf-8-sig")
            print(f"💾 Đã lưu checkpoint ({len(all_records)} sản phẩm)")

driver.quit()

# Bước 3: Lưu file cuối cùng
df = pd.DataFrame(all_records)

for col in COLUMNS_ORDER:
    if col not in df.columns:
        df[col] = None

df = df[COLUMNS_ORDER]
df["product_id"] = pd.to_numeric(df["product_id"], errors='coerce').fillna(0).astype(int)
df.to_csv(OUT_FILE, sep=";", index=False, encoding="utf-8-sig")

print(f"\n{'='*60}")
print(f"✅ HOÀN TẤT: {len(df)} sản phẩm → {OUT_FILE}")
