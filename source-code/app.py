import os, re, hashlib, hmac, secrets
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

# --------------------------- CONFIG ---------------------------
st.set_page_config(page_title='Cosmetic Analytics System', page_icon='💄', layout='wide', initial_sidebar_state='expanded')
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR.parent / 'dataset'
NAVY, BLUE, HASAKI, GUARDIAN = '#14213D', '#315B96', '#10B981', '#F97316'
BG, PANEL, TEXT, MUTED, BORDER = '#F4F6FA', '#FFFFFF', '#151923', '#687386', '#E3E8F0'
ROLES = {'ADMIN': 'ADMIN', 'NGUOI_XEM': 'NGƯỜI XEM'}

st.markdown(f'''<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], [data-testid="stApp"] {{font-family:'Be Vietnam Pro',sans-serif;color:{TEXT};}}
.stApp {{background:{BG}; color:{TEXT};}}
[data-testid="stHeader"] {{background:rgba(244,246,250,.92);}}
[data-testid="stSidebar"] {{background:#fff;border-right:1px solid {BORDER};}}
[data-testid="stSidebar"] * {{color:{TEXT};}}
.block-container {{max-width:1600px;padding-top:1.8rem;padding-bottom:2.5rem;}}
h1 {{font-size:2.15rem!important;font-weight:800!important;color:{TEXT}!important;}}
h2 {{font-size:1.45rem!important;font-weight:750!important;color:{TEXT}!important;}}
h3 {{font-size:1.12rem!important;font-weight:700!important;color:{TEXT}!important;}}
p, label, .stMarkdown {{color:{TEXT};}}
[data-testid="stMetric"] {{background:{PANEL};border:1px solid {BORDER};border-radius:18px;padding:18px 20px;box-shadow:0 4px 18px rgba(20,33,61,.04);min-height:116px;}}
[data-testid="stMetricLabel"] p {{font-size:14px!important;color:{MUTED}!important;font-weight:600;}}
[data-testid="stMetricValue"] {{font-size:27px!important;color:{NAVY}!important;font-weight:800;}}
.stButton>button,.stDownloadButton>button {{border-radius:12px;border:1px solid {BORDER};font-weight:700;min-height:44px;}}
.stButton>button[kind="primary"] {{background:{NAVY};color:white;border-color:{NAVY};}}
.stTextInput input,.stNumberInput input,.stSelectbox div[data-baseweb="select"],.stTextArea textarea {{border-radius:12px!important;}}
[data-testid="stForm"] {{background:white;border:1px solid {BORDER};border-radius:18px;padding:22px;}}
[data-testid="stDataFrame"] {{border:1px solid {BORDER};border-radius:14px;overflow:hidden;}}
.hero {{background:linear-gradient(110deg,#fff 0%,#edf3fc 100%);border:1px solid {BORDER};border-radius:22px;padding:26px 30px;margin-bottom:20px;}}
.hero-kicker {{font-size:12px;letter-spacing:2px;color:{BLUE};font-weight:800;}}
.hero-title {{font-size:27px;font-weight:800;color:{NAVY};margin:7px 0;}}
.hero-sub {{font-size:14px;color:{MUTED};}}
.section {{font-size:17px;font-weight:800;margin:12px 0;color:{NAVY};}}
.auth-wrap {{max-width:560px;margin:4vh auto;background:white;border:1px solid {BORDER};border-radius:24px;padding:34px;box-shadow:0 16px 50px rgba(20,33,61,.08);}}
.muted {{color:{MUTED};font-size:13px;}}
</style>''', unsafe_allow_html=True)

# --------------------------- AUTH ---------------------------
def users_collection():
    if get_database is None: raise RuntimeError('Không import được database.connection.get_database().')
    return get_database()['users']

def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 260000)
    return {'salt': salt.hex(), 'password_hash': digest.hex(), 'algorithm': 'pbkdf2_sha256'}

def verify_password(password, user):
    try:
        salt = bytes.fromhex(user['salt'])
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 260000).hex()
        return hmac.compare_digest(digest, user['password_hash'])
    except Exception: return False

def bootstrap_admin(coll):
    if coll.count_documents({}) == 0:
        st.markdown('<div class="auth-wrap">', unsafe_allow_html=True)
        st.markdown('## Khởi tạo quản trị viên đầu tiên')
        st.info('Chưa có tài khoản. Tạo ADMIN đầu tiên để bắt đầu quản trị hệ thống.')
        with st.form('bootstrap_admin'):
            username = st.text_input('Tên đăng nhập')
            email = st.text_input('Email (không bắt buộc)')
            p1 = st.text_input('Mật khẩu', type='password')
            p2 = st.text_input('Nhập lại mật khẩu', type='password')
            ok = st.form_submit_button('Tạo tài khoản ADMIN', type='primary', use_container_width=True)
        if ok:
            if len(username.strip()) < 4 or len(p1) < 8: st.error('Tên đăng nhập cần ít nhất 4 ký tự, mật khẩu ít nhất 8 ký tự.')
            elif p1 != p2: st.error('Mật khẩu nhập lại chưa khớp.')
            else:
                auth = hash_password(p1)
                coll.insert_one({'username':username.strip(),'email':email.strip(),'role':'ADMIN','active':True,**auth,'created_at':datetime.now(timezone.utc)})
                st.success('Đã tạo ADMIN. Vui lòng đăng nhập.'); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

def auth_screen():
    try: coll = users_collection()
    except Exception as e:
        st.error(f'Không kết nối được MongoDB để xác thực: {e}'); st.stop()
    bootstrap_admin(coll)
    st.markdown('<div class="auth-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="hero-kicker">COSMETIC ANALYTICS SYSTEM</div><div class="hero-title">HASAKI × GUARDIAN</div><div class="hero-sub">Nền tảng phân tích dữ liệu mỹ phẩm và hỗ trợ ra quyết định</div>', unsafe_allow_html=True)
    login_tab, reg_tab = st.tabs(['ĐĂNG NHẬP','ĐĂNG KÝ'])
    with login_tab:
        with st.form('login_form'):
            username = st.text_input('Tên đăng nhập', key='login_username')
            password = st.text_input('Mật khẩu', type='password', key='login_password')
            submit = st.form_submit_button('Đăng nhập', type='primary', use_container_width=True)
        if submit:
            user = coll.find_one({'username':username.strip()})
            if not user or not user.get('active', True) or not verify_password(password, user): st.error('Thông tin đăng nhập không chính xác hoặc tài khoản đã bị khóa.')
            else:
                st.session_state.auth_user = {'id':str(user['_id']),'username':user['username'],'role':user.get('role','NGUOI_XEM')}
                st.rerun()
    with reg_tab:
        with st.form('register_form'):
            username = st.text_input('Tên đăng nhập', key='reg_username')
            email = st.text_input('Email', key='reg_email')
            p1 = st.text_input('Mật khẩu (ít nhất 8 ký tự)', type='password', key='reg_p1')
            p2 = st.text_input('Nhập lại mật khẩu', type='password', key='reg_p2')
            submit = st.form_submit_button('Tạo tài khoản Người xem', type='primary', use_container_width=True)
        if submit:
            username = username.strip()
            if len(username)<4 or len(p1)<8: st.error('Tên đăng nhập cần ít nhất 4 ký tự và mật khẩu ít nhất 8 ký tự.')
            elif p1 != p2: st.error('Mật khẩu nhập lại chưa khớp.')
            elif coll.find_one({'username':username}): st.error('Tên đăng nhập đã tồn tại.')
            else:
                auth=hash_password(p1)
                coll.insert_one({'username':username,'email':email.strip(),'role':'NGUOI_XEM','active':True,**auth,'created_at':datetime.now(timezone.utc)})
                st.success('Đăng ký thành công. Bạn có thể đăng nhập.')
    st.stop()

if 'auth_user' not in st.session_state: auth_screen()
USER = st.session_state.auth_user
IS_ADMIN = USER.get('role') == 'ADMIN'

# --------------------------- DATA ---------------------------
def normalize(df):
    aliases={'pricing_current_price':'current_price','pricing_original_price':'original_price','pricing_discount_percent':'discount_percent','ratings_rating':'rating','ratings_review_count':'review_count','ratings_has_rating':'has_rating','specifications_volume_weight':'volume_weight','specifications_volume_val':'volume_val','specifications_volume_unit':'volume_unit'}
    df=df.rename(columns=aliases)
    for c in ['source','product_id','product_name','brand','category','product_url','current_price','original_price','discount_percent','rating','review_count']:
        if c not in df: df[c]=np.nan
    for c in ['current_price','original_price','discount_percent','rating','review_count']:
        df[c]=pd.to_numeric(df[c],errors='coerce')
    for c in ['source','brand','category','product_name']:
        df[c]=df[c].astype('string').str.strip()
    df['source']=df['source'].str.lower().map({'hasaki':'Hasaki','guardian':'Guardian'}).fillna(df['source'])
    return df

@st.cache_data(ttl=300)
def load_products():
    error=''
    try:
        db=get_database(); records=list(db['products'].find({}))
        if records: return normalize(pd.json_normalize(records,sep='_')), 'MongoDB · products'
    except Exception as e: error=str(e)
    path=DATASET_DIR/'merged_data.csv'
    if path.exists():
        try:
            d=pd.read_csv(path,sep=';',encoding='utf-8-sig')
            if len(d.columns)<3: d=pd.read_csv(path,encoding='utf-8-sig')
            return normalize(d), 'CSV dự phòng · merged_data.csv'
        except Exception as e: error=str(e)
    raise RuntimeError('Không tải được products từ MongoDB và không có dataset/merged_data.csv. '+error)

@st.cache_data(ttl=300)
def load_matched():
    try:
        db=get_database(); names=db.list_collection_names()
        if 'matched_products' in names:
            rows=list(db['matched_products'].find({}))
            if rows: return pd.json_normalize(rows,sep='_'), 'MongoDB · matched_products'
    except Exception: pass
    path=DATASET_DIR/'matched_products.csv'
    if path.exists():
        try:
            d=pd.read_csv(path,sep=';',encoding='utf-8-sig')
            if len(d.columns)<3: d=pd.read_csv(path,encoding='utf-8-sig')
            return d,'CSV · matched_products.csv'
        except Exception: pass
    return pd.DataFrame(), 'Chưa có dữ liệu ghép SKU'

try: df_all, source_label = load_products()
except Exception as e: st.error(str(e)); st.stop()
if df_all.empty: st.warning('Collection products chưa có dữ liệu.'); st.stop()

# Power BI-compatible calculated columns
def price_segment(v):
    if pd.isna(v): return 'Không xác định'
    if v < 100000: return 'Dưới 100K'
    if v < 300000: return '100K–300K'
    if v < 600000: return '300K–600K'
    return 'Trên 600K'

df_all['PhanKhucGia']=df_all.current_price.apply(price_segment)
df_all['TrangThaiKhuyenMai']=np.where(df_all.discount_percent.fillna(0)>0,'Có khuyến mãi','Không khuyến mãi')
df_all['Nhóm giảm giá']=pd.cut(df_all.discount_percent,[-np.inf,0,10,20,30,np.inf],labels=['Không giảm','0–10%','10–20%','20–30%','>30%'],right=True).astype('string')

# --------------------------- HELPERS ---------------------------
def header(title, subtitle):
    st.markdown(f'<div class="hero"><div class="hero-kicker">COSMETIC ANALYTICS SYSTEM</div><div class="hero-title">{title}</div><div class="hero-sub">{subtitle}</div></div>',unsafe_allow_html=True)
def section(title): st.markdown(f'<div class="section">{title}</div>',unsafe_allow_html=True)
def money(x): return '—' if pd.isna(x) else f'{x:,.0f} đ'
def pct(x): return '—' if pd.isna(x) else f'{x:.2f}%'
def style_fig(fig,height=390):
    fig.update_layout(height=height,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(family='Be Vietnam Pro',size=13,color=TEXT),margin=dict(l=35,r=25,t=50,b=45),legend=dict(orientation='h',y=1.12,x=0.02),hoverlabel=dict(font_size=13))
    fig.update_xaxes(showgrid=False,linecolor=BORDER,zerolinecolor=BORDER,title_font=dict(size=13))
    fig.update_yaxes(gridcolor='#E9EDF4',zerolinecolor=BORDER,title_font=dict(size=13))
    return fig
def chart(fig): st.plotly_chart(style_fig(fig),use_container_width=True)
def kpis(items):
    cols=st.columns(len(items))
    for c,(label,value) in zip(cols,items): c.metric(label,value)
def apply_filters(data, include_brand=False, include_category=True, include_segment=False):
    out=data.copy()
    with st.sidebar:
        if include_brand:
            opts=sorted(out.brand.dropna().astype(str).unique())
            chosen=st.multiselect('Thương hiệu',opts,default=opts,key='filter_brand')
            if chosen: out=out[out.brand.astype(str).isin(chosen)]
        if include_category:
            opts=sorted(out.category.dropna().astype(str).unique())
            chosen=st.multiselect('Danh mục',opts,default=opts,key='filter_cat')
            if chosen: out=out[out.category.astype(str).isin(chosen)]
        if include_segment:
            opts=['Dưới 100K','100K–300K','300K–600K','Trên 600K']
            chosen=st.multiselect('Phân khúc giá',opts,default=opts,key='filter_seg')
            if chosen: out=out[out.PhanKhucGia.isin(chosen)]
    return out

# --------------------------- SIDEBAR ---------------------------
with st.sidebar:
    st.markdown('## 💄 COSMETIC ANALYTICS')
    st.caption('HASAKI × GUARDIAN')
    st.divider()
    st.markdown(f'**{USER["username"]}**')
    st.caption('Quản trị viên' if IS_ADMIN else 'Người xem')
    if st.button('Đăng xuất',use_container_width=True):
        st.session_state.pop('auth_user',None); st.rerun()
    st.divider()
    pages=['Tổng quan','So sánh','Đối chiếu','Khuyến mãi','Machine Learning','Tra cứu sản phẩm']
    if IS_ADMIN: pages += ['Quản lý sản phẩm','Quản lý tài khoản']
    page=st.radio('ĐIỀU HƯỚNG',pages,label_visibility='collapsed')
    st.divider(); st.caption('KẾT NỐI DỮ LIỆU'); st.caption(source_label)

# --------------------------- PAGE 1 ---------------------------
if page=='Tổng quan':
    header('TỔNG QUAN THỊ TRƯỜNG MỸ PHẨM: HASAKI VS GUARDIAN','Quy mô dữ liệu, mặt bằng giá và cơ cấu phân khúc giá của hai chuỗi bán lẻ.')
    df=apply_filters(df_all,include_category=True,include_segment=True)
    med=df.current_price.median(); avg=df.current_price.mean(); avg_disc=df.discount_percent.mean()
    kpis([('TỔNG SỐ SẢN PHẨM',f'{len(df):,}'),('GIÁ TRUNG VỊ (VNĐ)',money(med)),('GIÁ TRUNG BÌNH (VNĐ)',money(avg)),('TỶ LỆ GIẢM GIÁ TB',pct(avg_disc))])
    left,right=st.columns(2)
    with left:
        section('SỐ LƯỢNG SẢN PHẨM THEO CHUỖI')
        d=df.groupby('source',dropna=False).size().reset_index(name='Tổng số sản phẩm')
        fig=px.bar(d,x='source',y='Tổng số sản phẩm',color='source',text='Tổng số sản phẩm',color_discrete_map={'Hasaki':HASAKI,'Guardian':GUARDIAN},labels={'source':'source','Tổng số sản phẩm':'Tổng số sản phẩm'})
        fig.update_layout(showlegend=False); chart(fig)
    with right:
        section('SO SÁNH GIÁ TRUNG VỊ GIỮA HAI CHUỖI (VNĐ)')
        d=df.groupby('source',as_index=False).current_price.median().rename(columns={'current_price':'Gia_Trung_Vi'})
        fig=px.bar(d,x='source',y='Gia_Trung_Vi',color='source',text_auto='.3s',color_discrete_map={'Hasaki':HASAKI,'Guardian':GUARDIAN},labels={'source':'source','Gia_Trung_Vi':'Gia_Trung_Vi'})
        fig.update_layout(showlegend=False); chart(fig)
    section('CƠ CẤU PHÂN KHÚC GIÁ')
    d=df.groupby(['PhanKhucGia','source'],observed=False).size().reset_index(name='Tổng số sản phẩm')
    fig=px.bar(d,x='PhanKhucGia',y='Tổng số sản phẩm',color='source',barmode='group',text='Tổng số sản phẩm',color_discrete_map={'Hasaki':HASAKI,'Guardian':GUARDIAN},labels={'PhanKhucGia':'PhanKhucGia','Tổng số sản phẩm':'Tổng số sản phẩm'})
    chart(fig)

# --------------------------- PAGE 2 ---------------------------
elif page=='So sánh':
    header('SO SÁNH GIÁ THEO DANH MỤC','So sánh giá trung vị, tỷ lệ giảm giá và tỷ trọng sản phẩm theo danh mục.')
    df=apply_filters(df_all,include_category=True,include_segment=True)
    kpis([('GIÁ TRUNG BÌNH THỊ TRƯỜNG',money(df.current_price.mean())),('TỶ LỆ GIẢM GIÁ TRUNG BÌNH',pct(df.discount_percent.mean()))])
    section('GIÁ TRUNG VỊ THEO DANH MỤC')
    d=df.groupby(['category','source']).current_price.median().reset_index(name='Gia_Trung_Vi')
    fig=px.bar(d,x='category',y='Gia_Trung_Vi',color='source',barmode='group',text_auto='.3s',color_discrete_map={'Hasaki':HASAKI,'Guardian':GUARDIAN},labels={'category':'category','Gia_Trung_Vi':'Gia_Trung_Vi','source':'source'}); chart(fig)
    left,right=st.columns(2)
    with left:
        section('TỶ LỆ GIẢM GIÁ THEO DANH MỤC')
        d=df.groupby(['category','source']).discount_percent.mean().reset_index(name='Tyle_GiamGia_TB')
        fig=px.bar(d,x='category',y='Tyle_GiamGia_TB',color='source',barmode='group',text_auto='.2f',color_discrete_map={'Hasaki':HASAKI,'Guardian':GUARDIAN},labels={'category':'category','Tyle_GiamGia_TB':'Tyle_GiamGia_TB','source':'source'}); chart(fig)
    with right:
        section('TỶ TRỌNG SỐ LƯỢNG SẢN PHẨM')
        d=df.groupby(['category','source']).product_id.count().reset_index(name='product_id')
        fig=px.bar(d,x='category',y='product_id',color='source',barmode='relative',color_discrete_map={'Hasaki':HASAKI,'Guardian':GUARDIAN},labels={'category':'category','product_id':'product_id','source':'source'})
        fig.update_layout(barnorm='percent')
        chart(fig)
# --------------------------- PAGE 3 ---------------------------
elif page=='Đối chiếu':
    header('ĐỐI CHIẾU GIÁ SẢN PHẨM GIỮA HASAKI VÀ GUARDIAN','Đối chiếu các SKU đã ghép cặp. Cần có dữ liệu matched_products để tái tạo đầy đủ các biểu đồ Power BI.')
    matched,matched_source=load_matched()
    st.caption(f'Nguồn dữ liệu đối chiếu: {matched_source}')
    if matched.empty:
        st.warning('Chưa tìm thấy collection matched_products hoặc dataset/matched_products.csv. Trang này chưa thể tái tạo các KPI và biểu đồ ghép SKU một cách đáng tin cậy.')
        st.info('Có thể nhập matched_products.csv vào MongoDB với tên collection matched_products; ứng dụng sẽ tự ưu tiên collection này khi tải lại.')
    else:
        st.metric('SỐ DÒNG DỮ LIỆU GHÉP',f'{len(matched):,}')
        st.dataframe(matched.head(500),use_container_width=True,hide_index=True)
        # Detect typical wide-format column names from export
        cols={c.lower().strip():c for c in matched.columns}
        def find_col(*names):
            for n in names:
                if n.lower() in cols:return cols[n.lower()]
            return None
        hcol=find_col('gia_hasaki','current_price_hasaki','hasaki_price','price_hasaki')
        gcol=find_col('gia_guardian','current_price_guardian','guardian_price','price_guardian')
        catcol=find_col('category','category_hasaki','danh_muc')
        namecol=find_col('product_name_hasaki','product_name','ten_san_pham')
        if hcol and gcol:
            matched[hcol]=pd.to_numeric(matched[hcol],errors='coerce'); matched[gcol]=pd.to_numeric(matched[gcol],errors='coerce')
            matched['chenh_lech_gia']=matched[gcol]-matched[hcol]
            matched['ben_re_hon']=np.select([matched[hcol]<matched[gcol],matched[hcol]>matched[gcol]],['Hasaki','Guardian'],default='Bằng giá')
            cheaper=matched.ben_re_hon.value_counts()
            kpis([('HASAKI RẺ HƠN',f'{cheaper.get("Hasaki",0):,}'),('GUARDIAN RẺ HƠN',f'{cheaper.get("Guardian",0):,}'),('SẢN PHẨM BẰNG GIÁ',f'{cheaper.get("Bằng giá",0):,}')])
            if catcol:
                section('SO SÁNH GIÁ TRUNG BÌNH THEO DANH MỤC SẢN PHẨM')
                d=matched.groupby(catcol)[[hcol,gcol]].mean().reset_index().melt(id_vars=catcol,var_name='Chuỗi',value_name='Giá trung bình')
                chart(px.bar(d,x='Giá trung bình',y=catcol,color='Chuỗi',barmode='group',orientation='h',labels={catcol:'category','Giá trung bình':'Giá trung bình','Chuỗi':'Chuỗi'}))
            section('CƠ CẤU SKU THEO TRẠNG THÁI GIÁ')
            if catcol:
                d=matched.groupby([catcol,'ben_re_hon']).size().reset_index(name='product_name_hasaki')
                chart(px.bar(d,x='product_name_hasaki',y=catcol,color='ben_re_hon',orientation='h',barmode='stack',labels={catcol:'category','product_name_hasaki':'product_name_hasaki','ben_re_hon':'ben_re_hon'}))
            if namecol:
                section('TOP 10 SẢN PHẨM CÓ CHÊNH LỆCH GIÁ LỚN NHẤT GIỮA HASAKI VÀ GUARDIAN')
                d=matched.nlargest(10,'chenh_lech_gia')
                chart(px.bar(d,x='chenh_lech_gia',y=namecol,orientation='h',labels={'chenh_lech_gia':'chenh_lech_gia',namecol:'product_name_hasaki'}))
        else:
            st.warning('File ghép chưa có cột giá Hasaki/Guardian theo định dạng nhận diện được. Cần đối chiếu tên cột thực tế trước khi dựng KPI và biểu đồ.')
        st.download_button('Xuất dữ liệu đối chiếu CSV',matched.to_csv(index=False).encode('utf-8-sig'),'matched_products_export.csv','text/csv')

# --------------------------- PAGE 4 ---------------------------
elif page=='Khuyến mãi':
    header('KHUYẾN MÃI VÀ CẠNH TRANH THƯƠNG HIỆU','Phân tích mức giảm giá, tỷ lệ sản phẩm khuyến mãi và giá gốc so với giá sau giảm.')
    with st.sidebar:
        srcs=sorted(df_all.source.dropna().unique().tolist()); ss=st.multiselect('Chuỗi bán lẻ',srcs,default=srcs,key='promo_src')
        cats=sorted(df_all.category.dropna().unique().tolist()); cc=st.multiselect('Danh mục',cats,default=cats,key='promo_cat')
        dis=st.multiselect('Nhóm giảm giá',['Không giảm','0–10%','10–20%','20–30%','>30%'],default=['Không giảm','0–10%','10–20%','20–30%','>30%'],key='promo_dis')
    df=df_all[df_all.source.isin(ss)&df_all.category.isin(cc)&df_all['Nhóm giảm giá'].isin(dis)].copy()
    promo=df[df.discount_percent.fillna(0)>0]
    kpis([('TỔNG SỐ SẢN PHẨM',f'{len(df):,}'),('TỶ LỆ SẢN PHẨM GIẢM GIÁ',pct(100*len(promo)/len(df) if len(df) else np.nan)),('GIẢM GIÁ TRUNG BÌNH',pct(promo.discount_percent.mean())),('GIẢM GIÁ TRUNG VỊ',pct(promo.discount_percent.median()))])
    left,right=st.columns(2)
    with left:
        section('MỨC GIẢM GIÁ TRUNG BÌNH THEO DANH MỤC')
        d=df.groupby(['category','source']).discount_percent.mean().reset_index(name='Giảm giá trung bình')
        chart(px.bar(d,x='Giảm giá trung bình',y='category',color='source',barmode='group',orientation='h',color_discrete_map={'Hasaki':HASAKI,'Guardian':GUARDIAN},labels={'category':'category','Giảm giá trung bình':'Giảm giá trung bình','source':'source'}))
    with right:
        section('TOP 10 THƯƠNG HIỆU CÓ NHIỀU SẢN PHẨM KHUYẾN MÃI NHẤT')
        d=promo.groupby('brand').size().nlargest(10).sort_values().reset_index(name='product_id')
        chart(px.bar(d,x='product_id',y='brand',orientation='h',labels={'product_id':'product_id','brand':'brand'}))
    left,right=st.columns(2)
    with left:
        section('TỶ LỆ SẢN PHẨM CÓ KHUYẾN MÃI THEO CHUỖI')
        d=df.groupby(['source','TrangThaiKhuyenMai']).size().reset_index(name='product_id')
        fig=px.bar(d,x='product_id',y='source',color='TrangThaiKhuyenMai',orientation='h',barmode='stack',labels={'product_id':'product_id','source':'source','TrangThaiKhuyenMai':'TrangThaiKhuyenMai'})
        fig.update_layout(barnorm='percent')
        chart(fig)
    with right:
        section('SO SÁNH GIÁ GỐC VÀ GIÁ SAU GIẢM THEO DANH MỤC')
        d=df.groupby('category')[['original_price','current_price']].mean().reset_index().melt(id_vars='category',var_name='Loại giá',value_name='Giá trung bình')
        chart(px.bar(d,x='category',y='Giá trung bình',color='Loại giá',barmode='group',labels={'category':'category','Giá trung bình':'Giá trung bình','Loại giá':'Loại giá'}))

# --------------------------- ML ---------------------------
elif page=='Machine Learning':
    header('MACHINE LEARNING','Huấn luyện mô hình trực tiếp trên dữ liệu sản phẩm từ MongoDB.')
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score, mean_absolute_error, mean_squared_error, r2_score
    from sklearn.ensemble import RandomForestRegressor, IsolationForest
    from sklearn.model_selection import train_test_split
    ml=df_all[['current_price','discount_percent','review_count','rating']].copy()
    ml=ml.replace([np.inf,-np.inf],np.nan).dropna(subset=['current_price','discount_percent'])
    ml['review_count']=ml.review_count.fillna(0); ml['rating']=ml.rating.fillna(ml.rating.median())
    st.caption(f'Dữ liệu đầu vào hợp lệ: {len(ml):,} sản phẩm')
    tab1,tab2,tab3=st.tabs(['K-MEANS CLUSTERING','RANDOM FOREST REGRESSION','ISOLATION FOREST'])
    with tab1:
        section('PHÂN NHÓM SẢN PHẨM THEO ĐẶC TRƯNG')
        k=st.slider('Số cụm K',2,8,4)
        features=['current_price','discount_percent','review_count']
        X=ml[features]; scaler=StandardScaler(); Xs=scaler.fit_transform(X)
        model=KMeans(n_clusters=k,random_state=42,n_init=10); labels=model.fit_predict(Xs)
        score=silhouette_score(Xs,labels) if len(set(labels))>1 and len(ml)>k else np.nan
        kpis([('SỐ CỤM',str(k)),('SILHOUETTE SCORE',f'{score:.3f}' if pd.notna(score) else '—'),('SỐ SẢN PHẨM',f'{len(ml):,}')])
        out=ml.copy(); out['Cụm']=labels.astype(str)
        chart(px.scatter(out,x='current_price',y='discount_percent',color='Cụm',hover_data=['review_count','rating'],labels={'current_price':'current_price','discount_percent':'discount_percent'}))
        st.dataframe(out.groupby('Cụm')[features].mean().round(2),use_container_width=True)
    with tab2:
        section('DỰ ĐOÁN GIÁ SẢN PHẨM')
        feat=['discount_percent','review_count','rating']; model_df=ml.dropna(subset=feat+['current_price'])
        if len(model_df)>=20:
            X=model_df[feat]; y=model_df.current_price
            Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,random_state=42)
            rf=RandomForestRegressor(n_estimators=250,random_state=42,min_samples_leaf=2,n_jobs=-1); rf.fit(Xtr,ytr); pred=rf.predict(Xte)
            kpis([('MAE',money(mean_absolute_error(yte,pred))),('RMSE',money(mean_squared_error(yte,pred)**.5)),('R²',f'{r2_score(yte,pred):.3f}')])
            imp=pd.DataFrame({'Đặc trưng':feat,'Mức độ quan trọng':rf.feature_importances_}).sort_values('Mức độ quan trọng')
            chart(px.bar(imp,x='Mức độ quan trọng',y='Đặc trưng',orientation='h',labels={'Mức độ quan trọng':'Mức độ quan trọng','Đặc trưng':'Đặc trưng'}))
            st.caption('Đánh giá trên tập kiểm tra tách ngẫu nhiên 20%; đây là mô hình thử nghiệm, không phải giá niêm yết chính thức.')
        else: st.warning('Chưa đủ 20 bản ghi hợp lệ để huấn luyện và đánh giá mô hình.')
    with tab3:
        section('PHÁT HIỆN SẢN PHẨM CÓ GIÁ / GIẢM GIÁ BẤT THƯỜNG')
        contamination=st.slider('Tỷ lệ bất thường dự kiến',.01,.15,.05,.01)
        features=['current_price','discount_percent','review_count']; X=ml[features]
        scaler=StandardScaler(); Xs=scaler.fit_transform(X)
        iso=IsolationForest(contamination=contamination,random_state=42); pred=iso.fit_predict(Xs)
        out=df_all.loc[ml.index].copy(); out['Kết quả']=np.where(pred==-1,'Bất thường','Bình thường')
        kpis([('BẤT THƯỜNG',f'{(pred==-1).sum():,}'),('BÌNH THƯỜNG',f'{(pred==1).sum():,}'),('TỶ LỆ BẤT THƯỜNG',pct((pred==-1).mean()*100))])
        st.dataframe(out[out['Kết quả']=='Bất thường'][['source','product_name','brand','category','current_price','discount_percent','review_count','Kết quả']].head(300),use_container_width=True,hide_index=True)

# --------------------------- PRODUCT LOOKUP ---------------------------
elif page=='Tra cứu sản phẩm':
    header('TRA CỨU SẢN PHẨM','Tìm kiếm sản phẩm theo tên, thương hiệu, danh mục và nguồn bán.')
    keyword=st.text_input('Từ khóa tìm kiếm',placeholder='Nhập tên sản phẩm hoặc thương hiệu...')
    d=df_all.copy()
    if keyword:
        mask=d.product_name.fillna('').str.contains(keyword,case=False,regex=False)|d.brand.fillna('').str.contains(keyword,case=False,regex=False)
        d=d[mask]
    st.caption(f'Tìm thấy {len(d):,} sản phẩm')
    cols=['source','product_id','product_name','brand','category','current_price','original_price','discount_percent','rating','review_count']
    st.dataframe(d[[c for c in cols if c in d.columns]],use_container_width=True,hide_index=True)
    st.download_button('Xuất kết quả CSV',d.to_csv(index=False).encode('utf-8-sig'),'products_search.csv','text/csv')

# --------------------------- ADMIN PRODUCT CRUD ---------------------------
elif page=='Quản lý sản phẩm':
    if not IS_ADMIN: st.error('Bạn không có quyền truy cập.'); st.stop()
    header('QUẢN LÝ SẢN PHẨM','Thêm, chỉnh sửa và xóa bản ghi trong MongoDB · products.')
    try: coll=get_database()['products']
    except Exception as e: st.error(str(e)); st.stop()
    st.warning('Thao tác tại đây tác động trực tiếp đến dữ liệu MongoDB. Hãy kiểm tra kỹ trước khi lưu hoặc xóa.')
    with st.form('add_product'):
        st.subheader('Thêm sản phẩm')
        a,b,c=st.columns(3)
        source=a.selectbox('Nguồn',['Hasaki','Guardian']); pid=b.text_input('Product ID'); name=c.text_input('Tên sản phẩm')
        brand=a.text_input('Thương hiệu'); category=b.text_input('Danh mục')
        price=c.number_input('Giá hiện tại (VNĐ)',min_value=0,step=1000); original=a.number_input('Giá gốc (VNĐ)',min_value=0,step=1000); discount=b.number_input('Giảm giá (%)',min_value=0.0,max_value=100.0,step=.5)
        add=st.form_submit_button('Thêm vào MongoDB',type='primary')
    if add:
        if not pid.strip() or not name.strip(): st.error('Product ID và tên sản phẩm là bắt buộc.')
        elif coll.find_one({'source':source,'product_id':pid.strip()}): st.error('Product ID này đã tồn tại ở nguồn đã chọn.')
        else:
            coll.insert_one({'source':source,'product_id':pid.strip(),'product_name':name.strip(),'brand':brand.strip(),'category':category.strip(),'pricing':{'current_price':price,'original_price':original,'discount_percent':discount},'created_at':datetime.now(timezone.utc)})
            st.cache_data.clear(); st.success('Đã thêm sản phẩm.'); st.rerun()
    st.divider(); section('CẬP NHẬT / XÓA SẢN PHẨM')
    key=st.text_input('Nhập Product ID cần tìm'); source_key=st.selectbox('Nguồn sản phẩm',['Hasaki','Guardian'],key='edit_source')
    record=coll.find_one({'source':source_key,'product_id':key.strip()}) if key.strip() else None
    if record:
        with st.form('edit_product'):
            newname=st.text_input('Tên sản phẩm',record.get('product_name','')); newbrand=st.text_input('Thương hiệu',record.get('brand','')); newcat=st.text_input('Danh mục',record.get('category',''))
            pricing=record.get('pricing',{}); newprice=st.number_input('Giá hiện tại',min_value=0,value=int(pricing.get('current_price') or 0)); neworig=st.number_input('Giá gốc',min_value=0,value=int(pricing.get('original_price') or 0)); newdisc=st.number_input('Giảm giá (%)',min_value=0.0,max_value=100.0,value=float(pricing.get('discount_percent') or 0))
            save=st.form_submit_button('Lưu thay đổi',type='primary')
        if save:
            coll.update_one({'_id':record['_id']},{'$set':{'product_name':newname,'brand':newbrand,'category':newcat,'pricing.current_price':newprice,'pricing.original_price':neworig,'pricing.discount_percent':newdisc}}); st.cache_data.clear(); st.success('Đã cập nhật.'); st.rerun()
        confirm=st.checkbox('Tôi xác nhận muốn xóa sản phẩm này.')
        if st.button('Xóa sản phẩm',disabled=not confirm):
            coll.delete_one({'_id':record['_id']}); st.cache_data.clear(); st.success('Đã xóa sản phẩm.'); st.rerun()
    elif key.strip(): st.info('Không tìm thấy sản phẩm theo Product ID và nguồn đã chọn.')

# --------------------------- ADMIN USERS ---------------------------
elif page=='Quản lý tài khoản':
    if not IS_ADMIN: st.error('Bạn không có quyền truy cập.'); st.stop()
    header('QUẢN LÝ TÀI KHOẢN','Quản lý trạng thái hoạt động và phân quyền ADMIN / NGƯỜI XEM.')
    coll=users_collection(); users=list(coll.find({})); admins=sum(1 for u in users if u.get('role')=='ADMIN' and u.get('active',True))
    kpis([('TỔNG TÀI KHOẢN',f'{len(users):,}'),('ADMIN ĐANG HOẠT ĐỘNG',f'{admins:,}'),('NGƯỜI XEM',f'{sum(u.get("role")=="NGUOI_XEM" for u in users):,}')])
    st.dataframe(pd.DataFrame([{'Tên đăng nhập':u.get('username'),'Email':u.get('email'),'Vai trò':ROLES.get(u.get('role'),u.get('role')),'Trạng thái':'Hoạt động' if u.get('active',True) else 'Đã khóa','Ngày tạo':u.get('created_at')} for u in users]),use_container_width=True,hide_index=True)
    st.divider(); section('CẬP NHẬT QUYỀN / TRẠNG THÁI')
    names=[u.get('username') for u in users]; selected=st.selectbox('Chọn tài khoản',names)
    target=next((u for u in users if u.get('username')==selected),None)
    if target:
        with st.form('user_update'):
            role=st.selectbox('Vai trò',['NGUOI_XEM','ADMIN'],index=0 if target.get('role')!='ADMIN' else 1)
            active=st.checkbox('Tài khoản đang hoạt động',value=target.get('active',True))
            newpass=st.text_input('Đặt lại mật khẩu (để trống nếu không đổi)',type='password')
            save=st.form_submit_button('Lưu thay đổi',type='primary')
        if save:
            active_admin_count=sum(1 for u in users if u.get('role')=='ADMIN' and u.get('active',True))
            removing_admin=target.get('role')=='ADMIN' and target.get('active',True) and (role!='ADMIN' or not active)
            if removing_admin and active_admin_count<=1: st.error('Không thể hạ quyền hoặc khóa ADMIN đang hoạt động cuối cùng.')
            elif target.get('username')==USER['username'] and (role!='ADMIN' or not active): st.error('Không thể tự hạ quyền hoặc tự khóa tài khoản đang đăng nhập.')
            else:
                update={'role':role,'active':active}
                if newpass:
                    if len(newpass)<8: st.error('Mật khẩu mới cần ít nhất 8 ký tự.'); st.stop()
                    update.update(hash_password(newpass))
                coll.update_one({'_id':target['_id']},{'$set':update}); st.success('Đã cập nhật tài khoản.'); st.rerun()

st.divider()
st.markdown(f'<div style="text-align:center;color:{MUTED};font-size:12px;padding:12px">COSMETIC ANALYTICS SYSTEM · HASAKI × GUARDIAN · BIG DATA ANALYTICS PROJECT</div>',unsafe_allow_html=True)
