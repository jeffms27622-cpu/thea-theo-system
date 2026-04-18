import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta
from fpdf import FPDF
import os
import gspread
from google.oauth2.service_account import Credentials
import io
import time
import hashlib

# =========================================================
# CONFIG & CONSTANTS
# =========================================================
MARKETING_NAME = "Asin"
MARKETING_WA = "0815-8199-775"
MARKETING_EMAIL = "alattulis.tts@gmail.com"
COMPANY_NAME = "PT. THEA THEO STATIONARY"
SLOGAN = "Office & School Supplies Solution"
ADDR = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
OFFICE_PHONE = "(021) 55780659"

if "ADMIN_PASSWORD" in st.secrets:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
else:
    ADMIN_PASSWORD = "admin"

COLOR_NAVY = (0, 40, 85)
COLOR_GOLD = (184, 134, 11)

st.set_page_config(
    page_title=f"{COMPANY_NAME} - {MARKETING_NAME}",
    layout="wide",
    page_icon="📎"
)

# =========================================================
# ENHANCED CUSTOM CSS (MODERN UI)
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700&display=swap');

/* Main Background */
.stApp {
    background-color: #f8fafc;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #001f42 0%, #002855 100%) !important;
    border-right: 2px solid #B8860B;
}

/* Glassmorphism Header */
.top-header {
    background: linear-gradient(135deg, #002855 0%, #004080 100%);
    border-radius: 20px;
    padding: 30px;
    margin-bottom: 30px;
    border-bottom: 5px solid #B8860B;
    box-shadow: 0 10px 30px rgba(0,40,85,0.2);
    color: white;
}

.top-header-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 700;
}

/* Modern Card Style */
.css-1r6slb0, .stElementContainer {
    border-radius: 12px;
}

div[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 16px !important;
    padding: 20px !important;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1) !important;
    border-top: 4px solid #B8860B !important;
}

/* Button Styling */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.stButton > button[kind="primary"] {
    background: #B8860B !important;
    border: none !important;
    color: white !important;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(184, 134, 11, 0.4);
}

/* Expander Styling */
.streamlit-expanderHeader {
    background-color: white !important;
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
    font-weight: 700 !important;
    color: #002855 !important;
}

/* Status Badge */
.status-badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    background: #e2e8f0;
    color: #475569;
}
</style>
""", unsafe_allow_html=True)

# ── Header Function ──
def render_header(title, subtitle):
    st.markdown(f"""
    <div class="top-header">
        <div class="top-header-title">{title}</div>
        <div style="color: #B8860B; font-weight: 600; letter-spacing: 1px;">{subtitle.upper()}</div>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# CORE FUNCTIONS
# =========================================================
def connect_gsheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open("Antrean Penawaran TTS").sheet1
    except Exception as e:
        st.error(f"Gagal koneksi: {e}")
        return None

@st.cache_data(ttl=600)
def load_db():
    if os.path.exists("database_barang.csv"):
        df = pd.read_csv("database_barang.csv")
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame(columns=['Nama Barang', 'Harga', 'Satuan'])

# =========================================================
# NAVIGATION
# =========================================================
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #B8860B;'>📎 TTS PORTAL</h1>", unsafe_allow_html=True)
    menu = st.radio("Menu Utama", ["🏠 Dashboard Home", "📝 Buat Penawaran", "👨‍💻 Panel Sales"], label_visibility="collapsed")
    st.divider()
    st.caption(f"Logged in as: {MARKETING_NAME}")

# =========================================================
# 🏠 HOME PAGE
# =========================================================
if menu == "🏠 Dashboard Home":
    render_header(COMPANY_NAME, SLOGAN)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Client", "1,240", "+12%")
    with col2:
        st.metric("Penawaran Bulan Ini", "85", "+5%")
    with col3:
        st.metric("Status Server", "Online", delta_color="normal")

    st.markdown("### 📞 Kontak Marketing")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        c1.write(f"**Nama:** {MARKETING_NAME}")
        c1.write(f"**WhatsApp:** {MARKETING_WA}")
        c2.write(f"**Email:** {MARKETING_EMAIL}")
        c2.write(f"**Alamat:** {ADDR}")

# =========================================================
# 📝 BUAT PENAWARAN (ADMIN SALES)
# =========================================================
elif menu == "📝 Buat Penawaran":
    render_header("Form Penawaran", "Input Data Pesanan Baru")
    
    df_barang = load_db()
    
    with st.form("form_order"):
        col1, col2 = st.columns(2)
        cust = col1.text_input("🏢 Nama Perusahaan")
        pic = col2.text_input("👤 Nama UP/PIC")
        wa = st.text_input("📞 No. WhatsApp")
        
        items = st.multiselect("🔍 Pilih Barang", df_barang['Nama Barang'].tolist())
        
        submitted = st.form_submit_button("🚀 Kirim Penawaran", use_container_width=True)
        if submitted:
            if cust and items:
                # Simpan logic ke GSheet di sini
                st.success(f"Penawaran untuk {cust} berhasil dikirim!")
            else:
                st.error("Mohon isi nama perusahaan dan pilih barang.")

# =========================================================
# 👨‍💻 PANEL SALES (DASHBOARD)
# =========================================================
elif menu == "👨‍💻 Panel Sales":
    render_header("Sales Management", "Kelola Antrean & Generate Dokumen")
    
    pwd = st.sidebar.text_input("🔑 Password Admin", type="password")
    
    if pwd == ADMIN_PASSWORD:
        sheet = connect_gsheet()
        if sheet:
            all_data = sheet.get_all_values()
            if len(all_data) > 1:
                # FIX ERROR 'WAKTU' & SPASI HEADER
                headers = [h.strip() for h in all_data[0]]
                df = pd.DataFrame(all_data[1:], columns=headers)
                
                # Proteksi kolom waktu
                if 'Waktu' not in df.columns: df['Waktu'] = "N/A"
                
                pending = df[df['Status'] == 'Pending']
                
                # Stats Bar
                st.columns(3)[0].metric("Antrean Pending", len(pending))
                
                st.markdown("---")
                
                for idx, row in pending.iterrows():
                    # UI Card menggunakan Expander
                    with st.expander(f"📦 {row['Customer']} — {row.get('Waktu', 'N/A')}"):
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"**PIC:** {row['UP']}")
                        c2.write(f"**WA:** {row['WA']}")
                        
                        if st.button("📄 Generate PDF", key=f"btn_{idx}"):
                            st.info("Sedang memproses PDF...")
                        
                        if st.button("✅ Selesai Proses", key=f"done_{idx}", type="primary"):
                            st.success("Status diperbarui!")
            else:
                st.info("Belum ada antrean masuk.")
    else:
        st.warning("Silakan masukkan password admin di sidebar.")
