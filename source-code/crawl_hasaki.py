import os
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# 1.KHỞI TẠO TRÌNH DUYỆT CHROME 
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

# 2.CẤU HÌNH DANH MỤC & ĐẦU RA
CATEGORIES = [
    {
        "name": "Chăm sóc da",
        "url": "https://hasaki.vn/danh-muc/cham-soc-da-mat-c4.html?p=",
        "pages": 40,
    },
    {
        "name": "Trang điểm",
        "url": "https://hasaki.vn/danh-muc/trang-diem-c23.html?p=",
        "pages": 40,
    },
    {
         "name": "Chăm sóc cá nhân",
         "url": "https://hasaki.vn/danh-muc/cham-soc-ca-nhan-c2049.html?p=",
         "pages": 15,
    },
    {
        "name": "Chăm sóc tóc",
        "url": "https://hasaki.vn/danh-muc/cham-soc-toc-c96.html?p=",
        "pages": 18,
    },
]

OUTPUT_DIR = os.path.abspath("../dataset")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "hasaki_raw.csv")
os.makedirs(OUTPUT_DIR, exist_ok=True)

COLUMNS = [
    "product_id", "product_name", "brand", "category", "volume_weight",
    "current_price", "original_price", "discount_percent",
    "rating", "review_count", "source", "product_url",
]

records = []
seen_ids = set()

# 3.HÀM XỬ LÝ
def clean_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def get_rating_review(text):
    """Trả về (rating, review_count). Không có rating -> None, review_count -> 0."""
    patterns = [
        r"(?<!\d)([1-5](?:[.,]\d)?)\s*\(\s*(\d+)\s*\)",
        r"(?<!\d)([1-5](?:[.,]\d)?)\s*/\s*5\s*\(\s*(\d+)\s*(?:đánh giá|review|reviews)?\s*\)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if m:
            rating = float(m.group(1).replace(",", "."))
            review_count = int(m.group(2))
            if 1 <= rating <= 5:
                return rating, review_count
    return None, 0


def get_volume(name):
    match = re.search(r"\b\d+(?:[.,]\d+)?\s*(?:ml|kg|g|lít|lit|l|miếng|viên|que|cây)\b", name, re.I)
    return match.group(0).lower() if match else None


def save_data_safe(records_list, path):
    if not records_list:
        return
    try:
        df_temp = pd.DataFrame(records_list).drop_duplicates(subset=["product_id"])
        df_temp = df_temp[COLUMNS]
        df_temp["review_count"] = df_temp["review_count"].fillna(0).astype(int)
        df_temp.to_csv(path, sep=";", index=False, encoding="utf-8-sig")
    except Exception as e:
        print(f"  ⚠️ Lỗi khi lưu file: {e}")


def crawl_page(url, max_retries=3):
    """
    Cào một trang với cơ chế retry nếu không tìm thấy sản phẩm.
    Trả về list các dict sản phẩm.
    """
    for attempt in range(1, max_retries + 1):
        try:
            driver.get(url)
            # Chờ sản phẩm xuất hiện
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='.html']"))
                )
            except Exception:
                time.sleep(1.5)

            # Cuộn để lazy-load
            driver.execute_script("window.scrollTo(0, 1200);")
            time.sleep(0.8)
            driver.execute_script("window.scrollTo(0, 2400);")
            time.sleep(0.8)

            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='.html']")
            page_records = []

            for item in links:
                try:
                    href = item.get_attribute("href") or ""
                    text = item.text.strip()

                    p_match = re.search(r"-(\d+)\.html", href)
                    if not p_match:
                        continue
                    product_id = int(p_match.group(1))

                    if product_id in seen_ids or ("₫" not in text and "đ" not in text):
                        continue

                    raw_lines = [l.strip() for l in text.split("\n") if l.strip()]

                    # Bóc giá
                    prices = []
                    for l in raw_lines:
                        if "₫" in l or "đ" in l:
                            num = re.sub(r"[^\d]", "", l)
                            if num and 1000 < int(num) <= 50000000:
                                prices.append(int(num))
                    if not prices:
                        continue

                    current_price = min(prices)
                    original_price = max(prices)

                    # Lọc dòng rác
                    clean_lines = []
                    for l in raw_lines:
                        if "%" in l or "₫" in l or "đ" in l:
                            continue
                        if any(k in l.lower() for k in ["giao 2h", "trợ giá", "bill", "tặng", "mua", "quà"]):
                            continue
                        clean_lines.append(l)

                    if not clean_lines:
                        continue

                    product_name = max(clean_lines, key=len)
                    if len(product_name) < 5:
                        continue

                    # Brand
                    if (
                        len(clean_lines) > 1
                        and len(clean_lines[0]) < 25
                        and clean_lines[0] != product_name
                        and not any(c.isdigit() for c in clean_lines[0])
                    ):
                        brand = clean_lines[0]
                    else:
                        brand = product_name.split()[0]

                    # Các trường phái sinh
                    volume_weight = get_volume(product_name)
                    discount_percent = 0.0
                    if original_price > current_price:
                        discount_percent = round(
                            ((original_price - current_price) / original_price) * 100, 1
                        )
                    rating, review_count = get_rating_review(text)

                    page_records.append({
                        "product_id": product_id,
                        "product_name": product_name,
                        "brand": brand,
                        "category": cat["name"],  # noqa: F821 (biến toàn cục, sẽ được truyền vào)
                        "volume_weight": volume_weight,
                        "current_price": current_price,
                        "original_price": original_price,
                        "discount_percent": discount_percent,
                        "rating": rating,
                        "review_count": int(review_count),
                        "source": "Hasaki",
                        "product_url": href,
                    })
                except Exception:
                    continue

            # Nếu có sản phẩm -> trả về ngay
            if page_records:
                return page_records

            # Nếu không có sản phẩm -> thử lại
            print(f"    ⚠️ Lần {attempt}/{max_retries}: Trang trống, thử tải lại...")
            time.sleep(3)
            driver.refresh()
            time.sleep(2)

        except Exception as e:
            print(f"    ❌ Lỗi lần {attempt}: {e}")
            time.sleep(3)

    return []

# 4.TIẾN TRÌNH CÀO (đã cải tiến)
print("=== BẮT ĐẦU CÀO DỮ LIỆU HASAKI (FIXED) ===")

try:
    for cat in CATEGORIES:
        print(f"\n>> Đang quét danh mục: {cat['name']}")
        empty_streak = 0

        for page in range(1, cat["pages"] + 1):
            url = f"{cat['url']}{page}"
        
            # Gọi hàm crawl với retry
            page_records = crawl_page(url, max_retries=3)

            # Gán category cho từng bản ghi (vì crawl_page không biết cat)
            for rec in page_records:
                rec["category"] = cat["name"]

            count_page = len(page_records)

            # Thêm vào danh sách tổng
            for rec in page_records:
                if rec["product_id"] not in seen_ids:
                    records.append(rec)
                    seen_ids.add(rec["product_id"])

            print(f"Trang {page:02d}: Lấy được {count_page} sp. (Tổng tích lũy:"
        f" {len(records)})")
            save_data_safe(records, OUTPUT_FILE)

            # Xử lý logic dừng
            if count_page == 0:
                empty_streak += 1
                if empty_streak >= 3:  # Tăng lên 3 lần liên tiếp mới dừng
                    print(f"Dừng danh mục")
                    break
            else:
                empty_streak = 0

            # Nghỉ giữa các trang để tránh bị block
            time.sleep(2.5)

except KeyboardInterrupt:
    print("\n⚠️ Người dùng dừng giữa chừng.")

finally:
    try:
        driver.quit()
    except Exception:
        pass
    save_data_safe(records, OUTPUT_FILE)

    if os.path.exists(OUTPUT_FILE):
        df_final = pd.read_csv(OUTPUT_FILE, sep=";", encoding="utf-8-sig")
        print(f"\n✅ Hoàn tất Hasaki: {len(df_final)} sản phẩm -> {OUTPUT_FILE}")
