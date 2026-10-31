import os
import re
import hashlib
import hmac
import secrets
import base64
from pathlib import Path
from datetime import datetime, timezone

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

try:
    from database.connection import get_database
except Exception:
    get_database = None


# ============================================================
# 1. CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Cosmetic Analytics System",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR.parent / "dataset"
ASSET_DIR = BASE_DIR / "assets"

# Color palette: Dark Green - Orange - Yellow
NAVY = "#174D32"
BLUE = "#F4C542"
HASAKI = "#174D32"
GUARDIAN = "#F07832"

BG = "#F7F8F3"
PANEL = "#FFFFFF"
TEXT = "#26352C"
MUTED = "#718078"
BORDER = "#E2E9DF"
GOLD = "#F4C542"

ROLES = {
    "ADMIN": "ADMIN",
    "NGUOI_XEM": "NGƯỜI XEM"
}


# ============================================================
# 2. GLOBAL UI DESIGN
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], [data-testid="stApp"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 8% 0%, #edf5e9 0, transparent 30%),
        #F7F8F3;
    color: #26352C;
}

[data-testid="stHeader"] {
    background: rgba(247,248,243,.92);
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #174D32 0%,
        #103B27 100%
    );
    border-right: 1px solid #245C3D;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: rgba(255,255,255,.07);
    border-radius: 12px;
    padding: 7px 10px;
    margin: 3px 0;
}

/* LAYOUT */
.block-container {
    max-width: 1600px;
    padding-top: 1.65rem;
    padding-bottom: 2.5rem;
}

/* TYPOGRAPHY */
h1 {
    font-size: 2.35rem !important;
    font-weight: 800 !important;
    color: #174D32 !important;
    letter-spacing: -.7px;
}

h2 {
    font-size: 1.65rem !important;
    font-weight: 750 !important;
    color: #174D32 !important;
}

h3 {
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: #174D32 !important;
}

p, label, .stMarkdown {
    color: #26352C;
}

/* KPI CARDS */
[data-testid="stMetric"] {
    background: linear-gradient(
        145deg,
        #FFFFFF 0%,
        #F9FCF7 100%
    );
    border: 1px solid #E4EBE1;
    border-radius: 22px;
    padding: 20px 22px;
    box-shadow:
        0 10px 24px rgba(23,77,50,.09),
        0 3px 7px rgba(23,77,50,.05),
        inset 0 1px 0 #FFFFFF;
    min-height: 120px;
    transition: transform .2s ease, box-shadow .2s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    box-shadow:
        0 16px 30px rgba(23,77,50,.14),
        0 5px 10px rgba(23,77,50,.06);
}

[data-testid="stMetricLabel"] p {
    font-size: 14px !important;
    color: #718078 !important;
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    font-size: 30px !important;
    color: #174D32 !important;
    font-weight: 800;
}

/* BUTTONS */
.stButton > button,
.stDownloadButton > button {
    border-radius: 14px;
    border: 1px solid #DDE7DC;
    font-weight: 700;
    min-height: 44px;
    box-shadow: 0 4px 10px rgba(23,77,50,.08);
    transition: all .18s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(23,77,50,.14);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #174D32, #236B43);
    color: white;
    border-color: #174D32;
}

/* INPUTS */
.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"],
.stTextArea textarea {
    border-radius: 13px !important;
}

/* FORMS */
[data-testid="stForm"] {
    background: #FFFFFF;
    border: 1px solid #E2E9DF;
    border-radius: 22px;
    padding: 22px;
    box-shadow: 0 9px 24px rgba(23,77,50,.07);
}

/* DATA TABLE */
[data-testid="stDataFrame"] {
    border: 1px solid #E2E9DF;
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 8px 20px rgba(23,77,50,.07);
}

/* HERO HEADER */
.hero {
    background: linear-gradient(
        120deg,
        #FFFFFF 0%,
        #F0F6EC 62%,
        #FFF5E4 100%
    );
    border: 1px solid #E2EADF;
    border-radius: 26px;
    padding: 30px 34px;
    margin-bottom: 22px;
    box-shadow:
        0 12px 28px rgba(23,77,50,.09),
        0 3px 8px rgba(23,77,50,.04),
        inset 0 1px 0 #FFFFFF;
}

.hero-kicker {
    font-size: 12px;
    letter-spacing: 2px;
    color: #D76B2C;
    font-weight: 800;
}

.hero-title {
    font-size: 34px;
    font-weight: 800;
    color: #174D32;
    margin: 8px 0;
    letter-spacing: -.8px;
}

.hero-sub {
    font-size: 14px;
    color: #718078;
}

/* SECTION TITLE */
.section {
    font-size: 20px;
    font-weight: 800;
    margin: 16px 0 12px;
    color: #174D32;
}

/* LOGIN / REGISTER */

.muted {
    color: #718078;
    font-size: 13px;
}

/* CIRCULAR LOGO */
.logo-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 18px;
    margin: 12px 0 18px;
}

.logo-frame {
    width: 82px;
    height: 82px;
    border-radius: 50%;
    padding: 10px;
    background: #FFFFFF;
    border: 1px solid rgba(255,255,255,.95);
    box-shadow: 0 4px 12px rgba(0,0,0,.12);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.logo-frame:hover {
    transform: translateY(-4px) scale(1.04);
    box-shadow:
        0 15px 25px rgba(0,0,0,.22),
        0 5px 10px rgba(0,0,0,.10);
}

.logo-frame img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    border-radius: 50%;
    display: block;
}

.logo-fallback {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 800;
    background: #FFFFFF;
    color: #174D32;
}

/* CHART CONTAINER */
[data-testid="stPlotlyChart"] {
    background: #FFFFFF;
    border: 1px solid #E5ECE2;
    border-radius: 20px;
    padding: 8px;
    box-shadow: 0 8px 22px rgba(23,77,50,.06);
}

/* SIDEBAR CAPTIONS */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: rgba(255,255,255,.75);
}

/* CHECKBOX */
[data-testid="stCheckbox"] label {
    color: inherit;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. LOGO FUNCTIONS
# ============================================================

def logo_html(filename, label):
    path = ASSET_DIR / filename

    if path.exists():
        from PIL import Image
        import io

        img = Image.open(path).convert("RGBA")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

        inner = f'''
            <img src="data:image/png;base64,{encoded}"
                 alt="{label}">
        '''
    else:
        inner = f'<div class="logo-fallback">{label}</div>'

    return f'<div class="logo-frame">{inner}</div>'


def brand_logos():
    st.markdown(
        f"""
        <div class="logo-row">
            {logo_html("hasaki_logo.png", "HASAKI")}
            {logo_html("guardian_logo.png", "GUARDIAN")}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# 4. AUTHENTICATION
# ============================================================

def users_collection():
    if get_database is None:
        raise RuntimeError(
            "Không import được database.connection.get_database()."
        )

    return get_database()["users"]


def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        260000
    )

    return {
        "salt": salt.hex(),
        "password_hash": digest.hex(),
        "algorithm": "pbkdf2_sha256"
    }


def verify_password(password, user):
    try:
        salt = bytes.fromhex(user["salt"])

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            260000
        ).hex()

        return hmac.compare_digest(
            digest,
            user["password_hash"]
        )

    except Exception:
        return False


def bootstrap_admin(coll):
    if coll.count_documents({}) == 0:

        st.markdown(
            '<div class="auth-wrap">',
            unsafe_allow_html=True
        )

        st.markdown("## Khởi tạo quản trị viên đầu tiên")

        st.info(
            "Chưa có tài khoản. Tạo ADMIN đầu tiên "
            "để bắt đầu quản trị hệ thống."
        )

        with st.form("bootstrap_admin"):

            username = st.text_input("Tên đăng nhập")
            email = st.text_input("Email (không bắt buộc)")
            p1 = st.text_input("Mật khẩu", type="password")
            p2 = st.text_input("Nhập lại mật khẩu", type="password")

            ok = st.form_submit_button(
                "Tạo tài khoản ADMIN",
                type="primary",
                use_container_width=True
            )

        if ok:
            if len(username.strip()) < 4 or len(p1) < 8:
                st.error(
                    "Tên đăng nhập cần ít nhất 4 ký tự, "
                    "mật khẩu ít nhất 8 ký tự."
                )

            elif p1 != p2:
                st.error("Mật khẩu nhập lại chưa khớp.")

            else:
                auth = hash_password(p1)

                coll.insert_one({
                    "username": username.strip(),
                    "email": email.strip(),
                    "role": "ADMIN",
                    "active": True,
                    **auth,
                    "created_at": datetime.now(timezone.utc)
                })

                st.success(
                    "Đã tạo ADMIN. Vui lòng đăng nhập."
                )
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()


def auth_screen():
    try:
        coll = users_collection()

    except Exception as e:
        st.error(
            f"Không kết nối được MongoDB để xác thực: {e}"
        )
        st.stop()

    bootstrap_admin(coll)

    st.markdown(
        '<div class="auth-wrap">',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="hero-kicker">
            COSMETIC ANALYTICS SYSTEM
        </div>
        <div class="hero-title">
            HASAKI × GUARDIAN
        </div>
        <div class="hero-sub">
            Nền tảng phân tích dữ liệu mỹ phẩm
            và hỗ trợ ra quyết định
        </div>
        """,
        unsafe_allow_html=True
    )

    login_tab, reg_tab = st.tabs([
        "ĐĂNG NHẬP",
        "ĐĂNG KÝ"
    ])

    with login_tab:

        with st.form("login_form"):

            username = st.text_input(
                "Tên đăng nhập",
                key="login_username"
            )

            password = st.text_input(
                "Mật khẩu",
                type="password",
                key="login_password"
            )

            submit = st.form_submit_button(
                "Đăng nhập",
                type="primary",
                use_container_width=True
            )

        if submit:
            user = coll.find_one({
                "username": username.strip()
            })

            if (
                not user
                or not user.get("active", True)
                or not verify_password(password, user)
            ):
                st.error(
                    "Thông tin đăng nhập không chính xác "
                    "hoặc tài khoản đã bị khóa."
                )

            else:
                st.session_state.auth_user = {
                    "id": str(user["_id"]),
                    "username": user["username"],
                    "role": user.get("role", "NGUOI_XEM")
                }

                st.rerun()

    with reg_tab:

        with st.form("register_form"):

            username = st.text_input(
                "Tên đăng nhập",
                key="reg_username"
            )

            email = st.text_input(
                "Email",
                key="reg_email"
            )

            p1 = st.text_input(
                "Mật khẩu (ít nhất 8 ký tự)",
                type="password",
                key="reg_p1"
            )

            p2 = st.text_input(
                "Nhập lại mật khẩu",
                type="password",
                key="reg_p2"
            )

            submit = st.form_submit_button(
                "Tạo tài khoản Người xem",
                type="primary",
                use_container_width=True
            )

        if submit:
            username = username.strip()

            if len(username) < 4 or len(p1) < 8:
                st.error(
                    "Tên đăng nhập cần ít nhất 4 ký tự "
                    "và mật khẩu ít nhất 8 ký tự."
                )

            elif p1 != p2:
                st.error("Mật khẩu nhập lại chưa khớp.")

            elif coll.find_one({"username": username}):
                st.error("Tên đăng nhập đã tồn tại.")

            else:
                auth = hash_password(p1)

                coll.insert_one({
                    "username": username,
                    "email": email.strip(),
                    "role": "NGUOI_XEM",
                    "active": True,
                    **auth,
                    "created_at": datetime.now(timezone.utc)
                })

                st.success(
                    "Đăng ký thành công. Bạn có thể đăng nhập."
                )

    st.stop()


# Check login
if "auth_user" not in st.session_state:
    auth_screen()

USER = st.session_state.auth_user
IS_ADMIN = USER.get("role") == "ADMIN"


# ============================================================
# 5. DATA PROCESSING
# ============================================================

def normalize(df):

    aliases = {
        "pricing_current_price": "current_price",
        "pricing_original_price": "original_price",
        "pricing_discount_percent": "discount_percent",
        "ratings_rating": "rating",
        "ratings_review_count": "review_count",
        "ratings_has_rating": "has_rating",
        "specifications_volume_weight": "volume_weight",
        "specifications_volume_val": "volume_val",
        "specifications_volume_unit": "volume_unit"
    }

    df = df.rename(columns=aliases)

    required_columns = [
        "source",
        "product_id",
        "product_name",
        "brand",
        "category",
        "product_url",
        "current_price",
        "original_price",
        "discount_percent",
        "rating",
        "review_count"
    ]

    for col in required_columns:
        if col not in df.columns:
            df[col] = np.nan

    numeric_columns = [
        "current_price",
        "original_price",
        "discount_percent",
        "rating",
        "review_count"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    text_columns = [
        "source",
        "brand",
        "category",
        "product_name"
    ]

    for col in text_columns:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
        )

    df["source"] = (
        df["source"]
        .str.lower()
        .map({
            "hasaki": "Hasaki",
            "guardian": "Guardian"
        })
        .fillna(df["source"])
    )

    return df


@st.cache_data(ttl=300)
def load_products():

    error = ""

    try:
        if get_database is None:
            raise RuntimeError(
                "Không tìm thấy hàm kết nối MongoDB."
            )

        db = get_database()
        records = list(db["products"].find({}))

        if records:
            return (
                normalize(
                    pd.json_normalize(records, sep="_")
                ),
                "MongoDB · products"
            )

    except Exception as e:
        error = str(e)

    path = DATASET_DIR / "merged_data.csv"

    if path.exists():
        try:
            data = pd.read_csv(
                path,
                sep=";",
                encoding="utf-8-sig"
            )

            if len(data.columns) < 3:
                data = pd.read_csv(
                    path,
                    encoding="utf-8-sig"
                )

            return (
                normalize(data),
                "CSV dự phòng · merged_data.csv"
            )

        except Exception as e:
            error = str(e)

    raise RuntimeError(
        "Không tải được products từ MongoDB "
        "và không có dataset/merged_data.csv. "
        + error
    )


@st.cache_data(ttl=300)
def load_matched():

    try:
        db = get_database()
        names = db.list_collection_names()

        if "matched_products" in names:
            rows = list(
                db["matched_products"].find({})
            )

            if rows:
                return (
                    pd.json_normalize(rows, sep="_"),
                    "MongoDB · matched_products"
                )

    except Exception:
        pass

    path = DATASET_DIR / "matched_products.csv"

    if path.exists():
        try:
            data = pd.read_csv(
                path,
                sep=";",
                encoding="utf-8-sig"
            )

            if len(data.columns) < 3:
                data = pd.read_csv(
                    path,
                    encoding="utf-8-sig"
                )

            return data, "CSV · matched_products.csv"

        except Exception:
            pass

    return pd.DataFrame(), "Chưa có dữ liệu ghép SKU"


try:
    df_all, source_label = load_products()

except Exception as e:
    st.error(str(e))
    st.stop()

if df_all.empty:
    st.warning(
        "Collection products chưa có dữ liệu."
    )
    st.stop()


# ============================================================
# 6. CALCULATED COLUMNS
# ============================================================

def price_segment(value):

    if pd.isna(value):
        return "Không xác định"

    if value < 100000:
        return "Dưới 100K"

    if value < 300000:
        return "100K–300K"

    if value < 600000:
        return "300K–600K"

    return "Trên 600K"


df_all["PhanKhucGia"] = (
    df_all["current_price"].apply(price_segment)
)

df_all["TrangThaiKhuyenMai"] = np.where(
    df_all["discount_percent"].fillna(0) > 0,
    "Có khuyến mãi",
    "Không khuyến mãi"
)

df_all["Nhóm giảm giá"] = pd.cut(
    df_all["discount_percent"],
    [-np.inf, 0, 10, 20, 30, np.inf],
    labels=[
        "Không giảm",
        "0–10%",
        "10–20%",
        "20–30%",
        ">30%"
    ],
    right=True
).astype("string")


# ============================================================
# 7. COMMON FUNCTIONS
# ============================================================

def header(title, subtitle):

    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">
                COSMETIC ANALYTICS SYSTEM
            </div>
            <div class="hero-title">
                {title}
            </div>
            <div class="hero-sub">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def section(title):

    st.markdown(
        f'<div class="section">{title}</div>',
        unsafe_allow_html=True
    )


def money(value):

    if pd.isna(value):
        return "—"

    return f"{value:,.0f} đ"


def pct(value):

    if pd.isna(value):
        return "—"

    return f"{value:.2f}%"


def style_fig(fig, height=390):

    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(
            family="Inter",
            size=13,
            color=TEXT
        ),

        margin=dict(
            l=35,
            r=25,
            t=50,
            b=45
        ),

        legend=dict(
            orientation="h",
            y=1.12,
            x=0.02
        ),

        hoverlabel=dict(
            font_size=13
        )
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor=BORDER,
        zerolinecolor=BORDER,
        title_font=dict(size=13)
    )

    fig.update_yaxes(
        gridcolor=BORDER,
        zerolinecolor=BORDER,
        title_font=dict(size=13)
    )

    return fig


def chart(fig):
    st.plotly_chart(
        style_fig(fig),
        use_container_width=True
    )


def kpis(items):

    cols = st.columns(len(items))

    for col, (label, value) in zip(cols, items):
        col.metric(label, value)

# ============================================================
# ĐỔI TÊN CỘT HIỂN THỊ TRONG BẢNG
# ============================================================

COLUMN_LABELS = {
    # Thông tin sản phẩm
    "source": "Nguồn bán",
    "product_id": "Mã sản phẩm",
    "product_name": "Tên sản phẩm",
    "brand": "Thương hiệu",
    "category": "Danh mục",
    "product_url": "Đường dẫn sản phẩm",
    "product_name_hasaki": "Tên sản phẩm Hasaki",
    "product_name_guardian": "Tên sản phẩm Guardian",

    # Thông tin giá
    "current_price": "Giá hiện tại (VNĐ)",
    "original_price": "Giá gốc (VNĐ)",
    "discount_percent": "Giảm giá (%)",
    "hasaki_price": "Giá Hasaki (VNĐ)",
    "guardian_price": "Giá Guardian (VNĐ)",
    "current_price_hasaki": "Giá Hasaki (VNĐ)",
    "current_price_guardian": "Giá Guardian (VNĐ)",
    "price_difference": "Chênh lệch giá (VNĐ)",
    "chenh_lech_gia": "Chênh lệch giá (VNĐ)",
    "cheaper_source": "Nguồn có giá thấp hơn",
    "ben_re_hon": "Nguồn có giá thấp hơn",
    "price_hasaki": "Giá Hasaki (VNĐ)",
    "price_guardian": "Giá Guardian (VNĐ)",
    "gia_hasaki": "Giá Hasaki (VNĐ)",
    "gia_guardian": "Giá Guardian (VNĐ)",

    # Đánh giá
    "rating": "Điểm đánh giá",
    "review_count": "Số lượt đánh giá",
    "has_rating": "Có đánh giá",

    # Dung tích / khối lượng
    "volume_weight": "Dung tích / Khối lượng",
    "volume_val": "Giá trị dung tích",
    "volume_unit": "Đơn vị dung tích",

    # Đối chiếu sản phẩm
    "match_score": "Điểm tương đồng",

    # Machine Learning
    "predicted_price": "Giá dự đoán (VNĐ)",
    "price_segment": "Phân khúc giá",
    "cluster": "Nhóm sản phẩm",
    "Cụm": "Nhóm sản phẩm",
    "Kết quả": "Kết quả phân tích",

    # Các trường tổng hợp
    "Gia_Trung_Vi": "Giá trung vị (VNĐ)",
    "Tyle_GiamGia_TB": "Tỷ lệ giảm giá trung bình (%)",
    "product_count": "Số lượng sản phẩm",
    "product_name_hasaki": "Tên sản phẩm Hasaki",
    "is_outlier": "Trạng thái bất thường",

    # Tài khoản
    "username": "Tên đăng nhập",
    "email": "Email",
    "role": "Vai trò",
    "active": "Trạng thái",
    "created_at": "Ngày tạo"
}


def show_table(data, **kwargs):
    """Hiển thị bảng với tên cột tiếng Việt."""
    display_df = data.rename(columns=COLUMN_LABELS)

    st.dataframe(
        display_df,
        use_container_width=True,
        **kwargs
    )

def apply_filters(
    data,
    include_brand=False,
    include_category=True,
    include_segment=False
):

    out = data.copy()

    with st.sidebar:

        if include_brand:

            opts = sorted(
                out.brand.dropna().astype(str).unique()
            )

            chosen = st.multiselect(
                "Thương hiệu",
                opts,
                default=opts,
                key="filter_brand"
            )

            if chosen:
                out = out[
                    out.brand.astype(str).isin(chosen)
                ]

        if include_category:

            opts = sorted(
                out.category.dropna().astype(str).unique()
            )

            chosen = st.multiselect(
                "Danh mục",
                opts,
                default=opts,
                key="filter_cat"
            )

            if chosen:
                out = out[
                    out.category.astype(str).isin(chosen)
                ]

        if include_segment:

            opts = [
                "Dưới 100K",
                "100K–300K",
                "300K–600K",
                "Trên 600K"
            ]

            chosen = st.multiselect(
                "Phân khúc giá",
                opts,
                default=opts,
                key="filter_seg"
            )

            if chosen:
                out = out[
                    out.PhanKhucGia.isin(chosen)
                ]

    return out

# ============================================================
# 8. SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:

    # Tiêu đề
    st.markdown("## COSMETIC ANALYTICS")

    # Logo hai thương hiệu
    brand_logos()

    # Tên hai website
    st.markdown(
        f"""
        <div style="
            text-align: center;
            color: {MUTED};
            font-size: 13px;
            font-weight: 600;
            margin-top: 8px;
            margin-bottom: 12px;
        ">
            HASAKI × GUARDIAN
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # Thông tin tài khoản
    st.markdown(f'**{USER["username"]}**')

    st.caption(
        "Quản trị viên" if IS_ADMIN else "Người xem"
    )

    # CSS cho nút Đăng xuất
    st.markdown(
        """
        <style>
        /* Nút Đăng xuất: nền trắng, chữ đen */
        [data-testid="stSidebar"] .st-key-logout_button button {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 1px solid #D1D5DB !important;
            border-radius: 8px !important;
        }

        /* Đảm bảo chữ bên trong nút luôn màu đen */
        [data-testid="stSidebar"] .st-key-logout_button button * {
            color: #000000 !important;
            fill: #000000 !important;
        }

        /* Hiệu ứng hover */
        [data-testid="stSidebar"] .st-key-logout_button button:hover {
            background-color: #F3F4F6 !important;
            border-color: #9CA3AF !important;
        }

        [data-testid="stSidebar"] .st-key-logout_button button:hover * {
            color: #000000 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Nút Đăng xuất
    if st.button(
        "Đăng xuất",
        use_container_width=True,
        key="logout_button"
    ):
        st.session_state.pop("auth_user", None)
        st.rerun()

    st.divider()

    # Danh sách trang
    pages = [
        "Tổng quan",
        "So sánh",
        "Đối chiếu",
        "Khuyến mãi",
        "Machine Learning",
        "Tra cứu sản phẩm"
    ]

    # Chỉ quản trị viên mới có quyền truy cập
    if IS_ADMIN:
        pages += [
            "Quản lý sản phẩm",
            "Quản lý tài khoản"
        ]

    # Điều hướng
    page = st.radio(
        "ĐIỀU HƯỚNG",
        pages,
        label_visibility="collapsed"
    )

    st.divider()

    # Trạng thái kết nối dữ liệu
    st.caption("KẾT NỐI DỮ LIỆU")
    st.caption(source_label)
# ============================================================
# 9. PAGE 1 - OVERVIEW
# ============================================================

if page == "Tổng quan":

    header(
        "TỔNG QUAN THỊ TRƯỜNG MỸ PHẨM: HASAKI VS GUARDIAN",
        "Quy mô dữ liệu, mặt bằng giá và cơ cấu phân khúc giá của hai chuỗi bán lẻ."
    )

    df = apply_filters(
        df_all,
        include_category=True,
        include_segment=True
    )

    med = df.current_price.median()
    avg = df.current_price.mean()
    avg_disc = df.discount_percent.mean()

    kpis([
        ("TỔNG SỐ SẢN PHẨM", f"{len(df):,}"),
        ("GIÁ TRUNG VỊ (VNĐ)", money(med)),
        ("GIÁ TRUNG BÌNH (VNĐ)", money(avg)),
        ("TỶ LỆ GIẢM GIÁ TB", pct(avg_disc))
    ])

    left, right = st.columns(2)

    with left:

        section("SỐ LƯỢNG SẢN PHẨM THEO CHUỖI")

        d = (
            df.groupby("source", dropna=False)
            .size()
            .reset_index(name="Tổng số sản phẩm")
        )

        fig = px.bar(
            d,
            x="source",
            y="Tổng số sản phẩm",
            color="source",
            text="Tổng số sản phẩm",
            color_discrete_map={
                "Hasaki": HASAKI,
                "Guardian": GUARDIAN
            },
            labels={
                "source": "Nguồn",
                "Tổng số sản phẩm": "Tổng số sản phẩm"
            }
        )

        fig.update_layout(showlegend=False)
        chart(fig)

    with right:

        section(
            "SO SÁNH GIÁ TRUNG VỊ GIỮA HAI CHUỖI (VNĐ)"
        )

        d = (
            df.groupby("source", as_index=False)
            .current_price.median()
            .rename(
                columns={"current_price": "Gia_Trung_Vi"}
            )
        )

        fig = px.bar(
            d,
            x="source",
            y="Gia_Trung_Vi",
            color="source",
            text_auto=".3s",
            color_discrete_map={
                "Hasaki": HASAKI,
                "Guardian": GUARDIAN
            },
            labels={
                "source": "Nguồn",
                "Gia_Trung_Vi": "Giá trung vị"
            }
        )

        fig.update_layout(showlegend=False)
        chart(fig)

    section("CƠ CẤU PHÂN KHÚC GIÁ")

    d = (
        df.groupby(
            ["PhanKhucGia", "source"],
            observed=False
        )
        .size()
        .reset_index(name="Tổng số sản phẩm")
    )

    fig = px.bar(
        d,
        x="PhanKhucGia",
        y="Tổng số sản phẩm",
        color="source",
        barmode="group",
        text="Tổng số sản phẩm",
        color_discrete_map={
            "Hasaki": HASAKI,
            "Guardian": GUARDIAN
        },
        labels={
            "PhanKhucGia": "Phân khúc giá",
            "Tổng số sản phẩm": "Tổng số sản phẩm"
        }
    )

    chart(fig)


# ============================================================
# 10. PAGE 2 - COMPARISON
# ============================================================

elif page == "So sánh":

    header(
        "SO SÁNH GIÁ THEO DANH MỤC",
        "So sánh giá trung vị, tỷ lệ giảm giá và tỷ trọng sản phẩm theo danh mục."
    )

    df = apply_filters(
        df_all,
        include_category=True,
        include_segment=True
    )

    kpis([
        (
            "GIÁ TRUNG BÌNH THỊ TRƯỜNG",
            money(df.current_price.mean())
        ),
        (
            "TỶ LỆ GIẢM GIÁ TRUNG BÌNH",
            pct(df.discount_percent.mean())
        )
    ])

    section("GIÁ TRUNG VỊ THEO DANH MỤC")

    d = (
        df.groupby(["category", "source"])
        .current_price.median()
        .reset_index(name="Gia_Trung_Vi")
    )

    fig = px.bar(
        d,
        x="category",
        y="Gia_Trung_Vi",
        color="source",
        barmode="group",
        text_auto=".3s",
        color_discrete_map={
            "Hasaki": HASAKI,
            "Guardian": GUARDIAN
        },
        labels={
            "category": "Danh mục",
            "Gia_Trung_Vi": "Giá trung vị",
            "source": "Nguồn"
        }
    )

    chart(fig)

    left, right = st.columns(2)

    with left:

        section("TỶ LỆ GIẢM GIÁ THEO DANH MỤC")

        d = (
            df.groupby(["category", "source"])
            .discount_percent.mean()
            .reset_index(name="Tyle_GiamGia_TB")
        )

        fig = px.bar(
            d,
            x="category",
            y="Tyle_GiamGia_TB",
            color="source",
            barmode="group",
            text_auto=".2f",
            color_discrete_map={
                "Hasaki": HASAKI,
                "Guardian": GUARDIAN
            },
            labels={
                "category": "Danh mục",
                "Tyle_GiamGia_TB": "Tỷ lệ giảm giá trung bình",
                "source": "Nguồn"
            }
        )

        chart(fig)

    with right:

        section("TỶ TRỌNG SỐ LƯỢNG SẢN PHẨM")

        d = (
            df.groupby(["category", "source"])
            .product_id.count()
            .reset_index(name="product_id")
        )

        fig = px.bar(
            d,
            x="category",
            y="product_id",
            color="source",
            barmode="relative",
            color_discrete_map={
                "Hasaki": HASAKI,
                "Guardian": GUARDIAN
            },
            labels={
                "category": "Danh mục",
                "product_id": "Số lượng sản phẩm",
                "source": "Nguồn"
            }
        )

        fig.update_layout(barnorm="percent")
        chart(fig)


# ============================================================
# 11. PAGE 3 - MATCHED PRODUCTS
# ============================================================

elif page == "Đối chiếu":

    header(
        "ĐỐI CHIẾU GIÁ SẢN PHẨM GIỮA HASAKI VÀ GUARDIAN",
        "Đối chiếu các SKU đã ghép cặp. Cần có dữ liệu matched_products để tái tạo đầy đủ các biểu đồ Power BI."
    )

    matched, matched_source = load_matched()

    st.caption(
        f"Nguồn dữ liệu đối chiếu: {matched_source}"
    )

    if matched.empty:

        st.warning(
            "Chưa tìm thấy collection matched_products "
            "hoặc dataset/matched_products.csv. "
            "Trang này chưa thể tái tạo các KPI "
            "và biểu đồ ghép SKU một cách đáng tin cậy."
        )

        st.info(
            "Có thể nhập matched_products.csv vào MongoDB "
            "với tên collection matched_products; "
            "ứng dụng sẽ tự ưu tiên collection này khi tải lại."
        )

    else:

        st.metric(
            "SỐ DÒNG DỮ LIỆU GHÉP",
            f"{len(matched):,}"
        )

        show_table(
            matched.head(500),
            hide_index=True
        )

        cols = {
            c.lower().strip(): c
            for c in matched.columns
        }

        def find_col(*names):

            for name in names:
                if name.lower() in cols:
                    return cols[name.lower()]

            return None

        hcol = find_col(
            "Giá Hasaki",
            "current_price_hasaki",
            "hasaki_price",
            "price_hasaki"
        )

        gcol = find_col(
            "Giá Guardian",
            "current_price_guardian",
            "guardian_price",
            "price_guardian"
        )

        catcol = find_col(
            "category",
            "category_hasaki",
            "danh_muc"
        )

        namecol = find_col(
            "product_name_hasaki",
            "product_name",
            "ten_san_pham"
        )

        if hcol and gcol:

            matched[hcol] = pd.to_numeric(
                matched[hcol],
                errors="coerce"
            )

            matched[gcol] = pd.to_numeric(
                matched[gcol],
                errors="coerce"
            )

            matched["chenh_lech_gia"] = (
                matched[gcol] - matched[hcol]
            )

            matched["ben_re_hon"] = np.select(
                [
                    matched[hcol] < matched[gcol],
                    matched[hcol] > matched[gcol]
                ],
                [
                    "Hasaki",
                    "Guardian"
                ],
                default="Bằng giá"
            )

            cheaper = matched.ben_re_hon.value_counts()

            kpis([
                (
                    "HASAKI RẺ HƠN",
                    f'{cheaper.get("Hasaki", 0):,}'
                ),
                (
                    "GUARDIAN RẺ HƠN",
                    f'{cheaper.get("Guardian", 0):,}'
                ),
                (
                    "SẢN PHẨM BẰNG GIÁ",
                    f'{cheaper.get("Bằng giá", 0):,}'
                )
            ])

            if catcol:

                section(
                    "SO SÁNH GIÁ TRUNG BÌNH THEO DANH MỤC SẢN PHẨM"
                )

                d = (
                    matched.groupby(catcol)[[hcol, gcol]]
                    .mean()
                    .reset_index()
                    .melt(
                        id_vars=catcol,
                        var_name="Chuỗi",
                        value_name="Giá trung bình"
                    )
                )

                chart(
                    px.bar(
                        d,
                        x="Giá trung bình",
                        y=catcol,
                        color="Chuỗi",
                        barmode="group",
                        orientation="h",
                        labels={
                            catcol: "Danh mục",
                            "Giá trung bình": "Giá trung bình",
                            "Chuỗi": "Chuỗi"
                        }
                    )
                )

            section("CƠ CẤU SKU THEO TRẠNG THÁI GIÁ")

            if catcol:

                d = (
                    matched.groupby(
                        [catcol, "ben_re_hon"]
                    )
                    .size()
                    .reset_index(name="product_name_hasaki")
                )

                chart(
                    px.bar(
                        d,
                        x="product_name_hasaki",
                        y=catcol,
                        color="ben_re_hon",
                        orientation="h",
                        barmode="stack",
                        labels={
                            catcol: "Danh mục",
                            "product_name_hasaki": "Số lượng sản phẩm",
                            "ben_re_hon": "So sánh giá"
                        }
                    )
                )

            if namecol:

                section(
                    "TOP 10 SẢN PHẨM CÓ CHÊNH LỆCH GIÁ LỚN NHẤT GIỮA HASAKI VÀ GUARDIAN"
                )

                d = matched.nlargest(
                    10,
                    "chenh_lech_gia"
                )

                chart(
                    px.bar(
                        d,
                        x="chenh_lech_gia",
                        y=namecol,
                        orientation="h",
                        labels={
                            "chenh_lech_gia": "Chênh lệch giá",
                            namecol: "Tên sản phẩm"
                        }
                    )
                )

        else:
            
            st.download_button(
            "Xuất dữ liệu đối chiếu CSV",
            matched.to_csv(index=False).encode("utf-8-sig"),
            "matched_products_export.csv",
            "text/csv"
        )


# ============================================================
# 12. PAGE 4 - PROMOTIONS
# ============================================================

elif page == "Khuyến mãi":

    header(
        "KHUYẾN MÃI VÀ CẠNH TRANH THƯƠNG HIỆU",
        "Phân tích mức giảm giá, tỷ lệ sản phẩm khuyến mãi và giá gốc so với giá sau giảm."
    )

    with st.sidebar:

        srcs = sorted(
            df_all.source.dropna().unique().tolist()
        )

        ss = st.multiselect(
            "Chuỗi bán lẻ",
            srcs,
            default=srcs,
            key="promo_src"
        )

        cats = sorted(
            df_all.category.dropna().unique().tolist()
        )

        cc = st.multiselect(
            "Danh mục",
            cats,
            default=cats,
            key="promo_cat"
        )

        dis = st.multiselect(
            "Nhóm giảm giá",
            [
                "Không giảm",
                "0–10%",
                "10–20%",
                "20–30%",
                ">30%"
            ],
            default=[
                "Không giảm",
                "0–10%",
                "10–20%",
                "20–30%",
                ">30%"
            ],
            key="promo_dis"
        )

    df = df_all[
        df_all.source.isin(ss)
        & df_all.category.isin(cc)
        & df_all["Nhóm giảm giá"].isin(dis)
    ].copy()

    promo = df[
        df.discount_percent.fillna(0) > 0
    ]

    kpis([
        ("TỔNG SỐ SẢN PHẨM", f"{len(df):,}"),
        (
            "TỶ LỆ SẢN PHẨM GIẢM GIÁ",
            pct(
                100 * len(promo) / len(df)
                if len(df)
                else np.nan
            )
        ),
        (
            "GIẢM GIÁ TRUNG BÌNH",
            pct(promo.discount_percent.mean())
        ),
        (
            "GIẢM GIÁ TRUNG VỊ",
            pct(promo.discount_percent.median())
        )
    ])

    left, right = st.columns(2)

    with left:

        section(
            "MỨC GIẢM GIÁ TRUNG BÌNH THEO DANH MỤC"
        )

        d = (
            df.groupby(["category", "source"])
            .discount_percent.mean()
            .reset_index(name="Giảm giá trung bình")
        )

        chart(
            px.bar(
                d,
                x="Giảm giá trung bình",
                y="category",
                color="source",
                barmode="group",
                orientation="h",
                color_discrete_map={
                    "Hasaki": HASAKI,
                    "Guardian": GUARDIAN
                },
                labels={
                    "category": "Danh mục",
                    "Giảm giá trung bình": "Giảm giá trung bình",
                    "source": "Nguồn"
                }
            )
        )

    with right:

        section(
            "TOP 10 THƯƠNG HIỆU CÓ NHIỀU SẢN PHẨM KHUYẾN MÃI NHẤT"
        )

        d = (
            promo.groupby("brand")
            .size()
            .nlargest(10)
            .sort_values()
            .reset_index(name="product_id")
        )

        chart(
            px.bar(
                d,
                x="product_id",
                y="brand",
                orientation="h",
                labels={
                    "product_id": "Số lượng sản phẩm",
                    "brand": "Thương hiệu"
                }
            )
        )

    left, right = st.columns(2)

    with left:

        section(
            "TỶ LỆ SẢN PHẨM CÓ KHUYẾN MÃI THEO CHUỖI"
        )

        d = (
            df.groupby(
                ["source", "TrangThaiKhuyenMai"]
            )
            .size()
            .reset_index(name="product_id")
        )

        fig = px.bar(
            d,
            x="product_id",
            y="source",
            color="TrangThaiKhuyenMai",
            orientation="h",
            barmode="stack",
            labels={
                "product_id": "Số lượng sản phẩm",
                "source": "Nguồn",
                "TrangThaiKhuyenMai": "Trạng thái khuyến mãi"
            }
        )

        fig.update_layout(barnorm="percent")
        chart(fig)

    with right:

        section(
            "SO SÁNH GIÁ GỐC VÀ GIÁ SAU GIẢM THEO DANH MỤC"
        )

        d = (
            df.groupby("category")[
              ["original_price", "current_price"]
            ]
            .mean()
            .reset_index()
            .melt(
                id_vars="category",
                var_name="Loại giá",
                value_name="Giá trung bình"
            )
        )

        chart(
            px.bar(
                d,
                x="category",
                y="Giá trung bình",
                color="Loại giá",
                barmode="group",
                labels={
                    "category": "Danh mục",
                    "Giá trung bình": "Giá trung bình",
                    "Loại giá": "Loại giá"
                }
            )
        )


# ============================================================
# 13. MACHINE LEARNING
# ============================================================

elif page == "Machine Learning":

    header(
        "MACHINE LEARNING",
        "Ứng dụng các mô hình học máy để phân tích dữ liệu sản phẩm mỹ phẩm."
    )

    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from sklearn.metrics import (
        silhouette_score,
        mean_absolute_error,
        mean_squared_error,
        r2_score
    )
    from sklearn.ensemble import (
        RandomForestRegressor,
        IsolationForest
    )
    from sklearn.model_selection import train_test_split

    ml = df_all[
        [
            "current_price",
            "discount_percent",
            "review_count",
            "rating"
        ]
    ].copy()

    ml = (
        ml.replace([np.inf, -np.inf], np.nan)
        .dropna(
            subset=[
                "current_price",
                "discount_percent"
            ]
        )
    )

    ml["review_count"] = (
        ml.review_count.fillna(0)
    )

    ml["rating"] = (
        ml.rating.fillna(ml.rating.median())
    )

    st.caption(
        f"Dữ liệu đầu vào hợp lệ: {len(ml):,} sản phẩm"
    )

    if len(ml) < 3:

        st.warning(
            "Chưa đủ dữ liệu hợp lệ để thực hiện Machine Learning."
        )

    else:

        tab1, tab2, tab3 = st.tabs([
            "K-MEANS CLUSTERING",
            "RANDOM FOREST REGRESSION",
            "ISOLATION FOREST"
        ])

        # K-MEANS
        with tab1:

            section(
                "PHÂN NHÓM SẢN PHẨM THEO ĐẶC TRƯNG"
            )

            k = st.slider(
                "Số cụm K",
                2,
                min(8, len(ml) - 1),
                min(4, len(ml) - 1)
            )

            features = [
                "current_price",
                "discount_percent",
                "review_count"
            ]

            X = ml[features]

            scaler = StandardScaler()
            Xs = scaler.fit_transform(X)

            model = KMeans(
                n_clusters=k,
                random_state=42,
                n_init=10
            )

            labels = model.fit_predict(Xs)

            score = (
                silhouette_score(Xs, labels)
                if len(set(labels)) > 1 and len(ml) > k
                else np.nan
            )

            kpis([
                ("SỐ CỤM", str(k)),
                (
                    "SILHOUETTE SCORE",
                    f"{score:.3f}"
                    if pd.notna(score)
                    else "—"
                ),
                ("SỐ SẢN PHẨM", f"{len(ml):,}")
            ])

            out = ml.copy()
            out["Cụm"] = labels.astype(str)

            chart(
                px.scatter(
                    out,
                    x="current_price",
                    y="discount_percent",
                    color="Cụm",
                    hover_data=[
                        "review_count",
                        "rating"
                    ],
                    labels={
                        "current_price": "Giá hiện tại",
                        "discount_percent": "Phần trăm giảm giá"
                    }
                )
            )

            show_table(
                out.groupby("Cụm")[features]
                .mean()
                .round(2),
            )

        # RANDOM FOREST
        with tab2:

            section("DỰ ĐOÁN GIÁ SẢN PHẨM")

            feat = [
                "discount_percent",
                "review_count",
                "rating"
            ]

            model_df = ml.dropna(
                subset=feat + ["current_price"]
            )

            if len(model_df) >= 20:

                X = model_df[feat]
                y = model_df.current_price

                Xtr, Xte, ytr, yte = train_test_split(
                    X,
                    y,
                    test_size=0.2,
                    random_state=42
                )

                rf = RandomForestRegressor(
                    n_estimators=250,
                    random_state=42,
                    min_samples_leaf=2,
                    n_jobs=-1
                )

                rf.fit(Xtr, ytr)
                pred = rf.predict(Xte)

                kpis([
                    (
                        "MAE",
                        money(
                            mean_absolute_error(yte, pred)
                        )
                    ),
                    (
                        "RMSE",
                        money(
                            mean_squared_error(
                                yte,
                                pred
                            ) ** 0.5
                        )
                    ),
                    (
                        "R²",
                        f"{r2_score(yte, pred):.3f}"
                    )
                ])

                imp = pd.DataFrame({
                    "Đặc trưng": feat,
                    "Mức độ quan trọng": rf.feature_importances_
                }).sort_values("Mức độ quan trọng")

                chart(
                    px.bar(
                        imp,
                        x="Mức độ quan trọng",
                        y="Đặc trưng",
                        orientation="h",
                        labels={
                            "Mức độ quan trọng": "Mức độ quan trọng",
                            "Đặc trưng": "Đặc trưng"
                        }
                    )
                )

                st.caption(
                    "Đánh giá trên tập kiểm tra tách ngẫu nhiên 20%; "
                    "đây là mô hình thử nghiệm, không phải giá niêm yết chính thức."
                )

            else:

                st.warning(
                    "Chưa đủ 20 bản ghi hợp lệ "
                    "để huấn luyện và đánh giá mô hình."
                )

        # ISOLATION FOREST
        with tab3:

            section(
                "PHÁT HIỆN SẢN PHẨM CÓ GIÁ / GIẢM GIÁ BẤT THƯỜNG"
            )

            contamination = st.slider(
                "Tỷ lệ bất thường dự kiến",
                0.01,
                0.15,
                0.05,
                0.01
            )

            features = [
                "current_price",
                "discount_percent",
                "review_count"
            ]

            X = ml[features]

            scaler = StandardScaler()
            Xs = scaler.fit_transform(X)

            iso = IsolationForest(
                contamination=contamination,
                random_state=42
            )

            pred = iso.fit_predict(Xs)

            out = df_all.loc[ml.index].copy()

            out["Kết quả"] = np.where(
                pred == -1,
                "Bất thường",
                "Bình thường"
            )

            kpis([
                (
                    "BẤT THƯỜNG",
                    f"{(pred == -1).sum():,}"
                ),
                (
                    "BÌNH THƯỜNG",
                    f"{(pred == 1).sum():,}"
                ),
                (
                    "TỶ LỆ BẤT THƯỜNG",
                    pct((pred == -1).mean() * 100)
                )
            ])

            show_table(
                out[
                    out["Kết quả"] == "Bất thường"
                ][
                    [
                        "source",
                        "product_name",
                        "brand",
                        "category",
                        "current_price",
                        "discount_percent",
                        "review_count",
                        "Kết quả"
                    ]
                ].head(300),
                hide_index=True
            )


# ============================================================
# 14. PRODUCT LOOKUP
# ============================================================

elif page == "Tra cứu sản phẩm":

    header(
        "TRA CỨU SẢN PHẨM",
        "Tìm kiếm sản phẩm theo tên, thương hiệu, danh mục và nguồn bán."
    )

    keyword = st.text_input(
        "Từ khóa tìm kiếm",
        placeholder="Nhập tên sản phẩm hoặc thương hiệu..."
    )

    d = df_all.copy()

    if keyword:

        mask = (
            d.product_name.fillna("")
            .str.contains(
                keyword,
                case=False,
                regex=False
            )
            |
            d.brand.fillna("")
            .str.contains(
                keyword,
                case=False,
                regex=False
            )
        )

        d = d[mask]

    st.caption(
        f"Tìm thấy {len(d):,} sản phẩm"
    )

    cols = [
        "source",
        "product_id",
        "product_name",
        "brand",
        "category",
        "current_price",
        "original_price",
        "discount_percent",
        "rating",
        "review_count"
    ]

    show_table(
        d[[c for c in cols if c in d.columns]],
        hide_index=True
    )

    st.download_button(
        "Xuất kết quả CSV",
        d.to_csv(index=False).encode("utf-8-sig"),
        "products_search.csv",
        "text/csv"
    )


# ============================================================
# 15. ADMIN - PRODUCT CRUD
# ============================================================

elif page == "Quản lý sản phẩm":

    if not IS_ADMIN:
        st.error("Bạn không có quyền truy cập.")
        st.stop()

    header(
        "QUẢN LÝ SẢN PHẨM",
        "Thêm, chỉnh sửa và xóa sản phẩm"
    )

    try:
        coll = get_database()["products"]

    except Exception as e:
        st.error(str(e))
        st.stop()


    # ADD PRODUCT
    with st.form("add_product"):

        st.subheader("Thêm sản phẩm")

        a, b, c = st.columns(3)

        source = a.selectbox(
            "Nguồn",
            ["Hasaki", "Guardian"]
        )

        pid = b.text_input("Product ID")
        name = c.text_input("Tên sản phẩm")

        brand = a.text_input("Thương hiệu")
        category = b.text_input("Danh mục")

        price = c.number_input(
            "Giá hiện tại (VNĐ)",
            min_value=0,
            step=1000
        )

        original = a.number_input(
            "Giá gốc (VNĐ)",
            min_value=0,
            step=1000
        )

        discount = b.number_input(
            "Giảm giá (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.5
        )

        add = st.form_submit_button(
            "Thêm vào MongoDB",
            type="primary"
        )

    if add:

        if not pid.strip() or not name.strip():

            st.error(
                "Product ID và tên sản phẩm là bắt buộc."
            )

        elif coll.find_one({
            "source": source,
            "product_id": pid.strip()
        }):

            st.error(
                "Product ID này đã tồn tại ở nguồn đã chọn."
            )

        else:

            coll.insert_one({
                "source": source,
                "product_id": pid.strip(),
                "product_name": name.strip(),
                "brand": brand.strip(),
                "category": category.strip(),
                "pricing": {
                    "current_price": price,
                    "original_price": original,
                    "discount_percent": discount
                },
                "created_at": datetime.now(timezone.utc)
            })

            st.cache_data.clear()

            st.success("Đã thêm sản phẩm.")
            st.rerun()

    st.divider()

    section("CẬP NHẬT / XÓA SẢN PHẨM")

    key = st.text_input(
        "Nhập Product ID cần tìm"
    )

    source_key = st.selectbox(
        "Nguồn sản phẩm",
        ["Hasaki", "Guardian"],
        key="edit_source"
    )

    record = (
        coll.find_one({
            "source": source_key,
            "product_id": key.strip()
        })
        if key.strip()
        else None
    )

    if record:

        with st.form("edit_product"):

            newname = st.text_input(
                "Tên sản phẩm",
                record.get("product_name", "")
            )

            newbrand = st.text_input(
                "Thương hiệu",
                record.get("brand", "")
            )

            newcat = st.text_input(
                "Danh mục",
                record.get("category", "")
            )

            pricing = record.get("pricing", {})

            newprice = st.number_input(
                "Giá hiện tại",
                min_value=0,
                value=int(
                    pricing.get("current_price") or 0
                )
            )

            neworig = st.number_input(
                "Giá gốc",
                min_value=0,
                value=int(
                    pricing.get("original_price") or 0
                )
            )

            newdisc = st.number_input(
                "Giảm giá (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(
                    pricing.get("discount_percent") or 0
                )
            )

            save = st.form_submit_button(
                "Lưu thay đổi",
                type="primary"
            )

        if save:

            coll.update_one(
                {"_id": record["_id"]},
                {
                    "$set": {
                        "product_name": newname,
                        "brand": newbrand,
                        "category": newcat,
                        "pricing.current_price": newprice,
                        "pricing.original_price": neworig,
                        "pricing.discount_percent": newdisc
                    }
                }
            )

            st.cache_data.clear()

            st.success("Đã cập nhật.")
            st.rerun()

        confirm = st.checkbox(
            "Tôi xác nhận muốn xóa sản phẩm này."
        )

        if st.button(
            "Xóa sản phẩm",
            disabled=not confirm
        ):

            coll.delete_one({
                "_id": record["_id"]
            })

            st.cache_data.clear()

            st.success("Đã xóa sản phẩm.")
            st.rerun()

    elif key.strip():

        st.info(
            "Không tìm thấy sản phẩm theo Product ID "
            "và nguồn đã chọn."
        )


# ============================================================
# 16. ADMIN - ACCOUNT MANAGEMENT
# ============================================================

elif page == "Quản lý tài khoản":

    if not IS_ADMIN:
        st.error("Bạn không có quyền truy cập.")
        st.stop()

    header(
        "QUẢN LÝ TÀI KHOẢN",
        "Quản lý trạng thái hoạt động và phân quyền ADMIN / NGƯỜI XEM."
    )

    coll = users_collection()

    users = list(coll.find({}))

    admins = sum(
        1 for u in users
        if u.get("role") == "ADMIN"
        and u.get("active", True)
    )

    kpis([
        ("TỔNG TÀI KHOẢN", f"{len(users):,}"),
        ("ADMIN ĐANG HOẠT ĐỘNG", f"{admins:,}"),
        (
            "NGƯỜI XEM",
            f"{sum(u.get('role') == 'NGUOI_XEM' for u in users):,}"
        )
    ])

    st.dataframe(
        pd.DataFrame([
            {
                "Tên đăng nhập": u.get("username"),
                "Email": u.get("email"),
                "Vai trò": ROLES.get(
                    u.get("role"),
                    u.get("role")
                ),
                "Trạng thái": (
                    "Hoạt động"
                    if u.get("active", True)
                    else "Đã khóa"
                ),
                "Ngày tạo": u.get("created_at")
            }
            for u in users
        ]),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    section("CẬP NHẬT QUYỀN / TRẠNG THÁI")

    names = [
        u.get("username")
        for u in users
    ]

    if names:

        selected = st.selectbox(
            "Chọn tài khoản",
            names
        )

        target = next(
            (
                u for u in users
                if u.get("username") == selected
            ),
            None
        )

        if target:

            with st.form("user_update"):

                role = st.selectbox(
                    "Vai trò",
                    ["NGUOI_XEM", "ADMIN"],
                    index=(
                        0
                        if target.get("role") != "ADMIN"
                        else 1
                    )
                )

                active = st.checkbox(
                    "Tài khoản đang hoạt động",
                    value=target.get("active", True)
                )

                newpass = st.text_input(
                    "Đặt lại mật khẩu (để trống nếu không đổi)",
                    type="password"
                )

                save = st.form_submit_button(
                    "Lưu thay đổi",
                    type="primary"
                )

            if save:

                active_admin_count = sum(
                    1 for u in users
                    if u.get("role") == "ADMIN"
                    and u.get("active", True)
                )

                removing_admin = (
                    target.get("role") == "ADMIN"
                    and target.get("active", True)
                    and (role != "ADMIN" or not active)
                )

                if (
                    removing_admin
                    and active_admin_count <= 1
                ):

                    st.error(
                        "Không thể hạ quyền hoặc khóa "
                        "ADMIN đang hoạt động cuối cùng."
                    )

                elif (
                    target.get("username") == USER["username"]
                    and (role != "ADMIN" or not active)
                ):

                    st.error(
                        "Không thể tự hạ quyền "
                        "hoặc tự khóa tài khoản đang đăng nhập."
                    )

                else:

                    update = {
                        "role": role,
                        "active": active
                    }

                    if newpass:

                        if len(newpass) < 8:

                            st.error(
                                "Mật khẩu mới cần ít nhất 8 ký tự."
                            )
                            st.stop()

                        update.update(
                            hash_password(newpass)
                        )

                    coll.update_one(
                        {"_id": target["_id"]},
                        {"$set": update}
                    )

                    st.success(
                        "Đã cập nhật tài khoản."
                    )

                    st.rerun()

    else:

        st.info("Chưa có tài khoản trong hệ thống.")


# ============================================================
# 17. FOOTER
# ============================================================

st.divider()

st.markdown(
    f"""
    <div style="
        text-align:center;
        color:{MUTED};
        font-size:12px;
        padding:12px;
    ">
        COSMETIC ANALYTICS SYSTEM
        · HASAKI × GUARDIAN
        · BIG DATA ANALYTICS PROJECT
    </div>
    """,
    unsafe_allow_html=True
)