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
COLOR_TEXT = (30, 30, 30)

st.set_page_config(
    page_title=f"{COMPANY_NAME} - {MARKETING_NAME}",
    layout="wide",
    page_icon="📎",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    -webkit-tap-highlight-color: transparent;
    -webkit-text-size-adjust: 100%;
}
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

.stApp {
    background: linear-gradient(135deg, #f0f4f8 0%, #e8edf5 50%, #f5f0e8 100%);
    min-height: 100vh;
}

.block-container {
    padding: 0.6rem 0.8rem 3rem 0.8rem !important;
    max-width: 100% !important;
}
@media (min-width: 768px) {
    .block-container {
        padding: 1.2rem 2.5rem 3rem 2.5rem !important;
        max-width: 1280px !important;
        margin: 0 auto !important;
    }
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #002855 0%, #003d7a 40%, #001f42 100%) !important;
    border-right: 3px solid #B8860B;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not([data-baseweb]),
[data-testid="stSidebar"] label { color: #e8edf5 !important; }

.topnav-container {
    background: linear-gradient(135deg, #002855 0%, #003d7a 100%);
    border-radius: 14px;
    padding: 10px;
    margin-bottom: 18px;
    border-bottom: 3px solid #B8860B;
    box-shadow: 0 6px 20px rgba(0,40,85,0.3);
}

.top-header {
    background: linear-gradient(135deg, #002855 0%, #004080 60%, #002855 100%);
    border-radius: 12px; padding: 16px 18px; margin-bottom: 16px;
    border-bottom: 4px solid #B8860B;
    box-shadow: 0 8px 32px rgba(0,40,85,0.3); position: relative; overflow: hidden;
}
.top-header-title {
    font-family: 'Playfair Display', serif; font-size: 1.25rem;
    font-weight: 700; color: white; margin: 0; line-height: 1.2;
}
.top-header-subtitle {
    font-size: 0.68rem; color: #B8860B; letter-spacing: 0.1em;
    text-transform: uppercase; font-weight: 600; margin-top: 3px;
}
.top-header-badge {
    display: inline-block; background: rgba(184,134,11,0.2);
    border: 1px solid #B8860B; color: #f0c040; padding: 4px 12px;
    border-radius: 20px; font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.06em; margin-top: 8px;
}
@media (min-width: 768px) {
    .top-header { padding: 28px 36px; border-radius: 16px; margin-bottom: 28px; }
    .top-header-title { font-size: 1.85rem; }
}

.section-title {
    font-family: 'Playfair Display', serif; font-size: 1rem;
    color: #002855; font-weight: 700; border-left: 4px solid #B8860B;
    padding-left: 10px; margin: 14px 0 10px 0;
}

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    color: #1e1e1e !important;
    border-radius: 10px !important;
    border: 1.5px solid #c8d6e5 !important;
    background: white !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 1rem !important;
    padding: 12px 14px !important;
    min-height: 48px !important;
    -webkit-appearance: none;
}
.stTextInput > div > div > input::placeholder,
.stNumberInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #9fb3c8 !important;
    opacity: 1 !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #002855 !important;
    box-shadow: 0 0 0 3px rgba(0,40,85,0.1) !important;
    outline: none !important;
}

[data-testid="stSelectbox"] > div > div {
    border-radius: 10px !important; border: 1.5px solid #c8d6e5 !important;
    background: white !important; color: #1e1e1e !important; min-height: 48px !important;
}
[data-testid="stMultiSelect"] > div > div {
    border-radius: 10px !important; border: 1.5px solid #c8d6e5 !important;
    background: white !important; color: #1e1e1e !important; min-height: 48px !important;
}
[data-testid="stSelectbox"] span,
[data-testid="stMultiSelect"] span { color: #1e1e1e !important; }

[data-testid="stSelectbox"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSelectbox"] div[role="combobox"] p,
[data-baseweb="select"] div[data-testid="stMarkdownContainer"] p {
    color: #1e1e1e !important;
}

[data-baseweb="select"] [data-baseweb="option"],
[data-baseweb="popover"] li,
ul[role="listbox"] li {
    color: #1e1e1e !important; background: white !important;
    padding: 12px 16px !important; font-size: 0.95rem !important;
}

[data-baseweb="select"] input {
    color: #1e1e1e !important;
    background: white !important;
}

section.main .stTextInput > label,
section.main .stTextInput label,
section.main .stSelectbox > label,
section.main .stSelectbox label,
section.main .stNumberInput > label,
section.main .stNumberInput label,
section.main .stMultiSelect > label,
section.main .stMultiSelect label,
section.main .stCheckbox > label,
section.main .stCheckbox label,
section.main .stTextArea > label,
section.main .stTextArea label,
div[data-testid="stForm"] label,
div[class*="stTextInput"] label,
div[class*="stSelectbox"] label,
div[class*="stNumberInput"] label,
div[class*="stMultiSelect"] label {
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: #002855 !important;
    opacity: 1 !important;
    visibility: visible !important;
}

.stButton > button {
    min-height: 48px !important; border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important; font-size: 0.85rem !important;
    letter-spacing: 0.06em !important; text-transform: uppercase !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important; -webkit-tap-highlight-color: transparent;
    width: 100% !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #002855 0%, #004080 100%) !important;
    color: white !important; border: none !important;
    box-shadow: 0 4px 14px rgba(0,40,85,0.3) !important;
    border-bottom: 3px solid #B8860B !important;
}
.stButton > button:not([kind="primary"]) {
    background: white !important; color: #002855 !important;
    border: 1.5px solid #002855 !important;
}
@media (min-width: 768px) {
    .stButton > button { width: auto !important; }
}

.stDownloadButton > button {
    min-height: 48px !important; border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important; font-size: 0.82rem !important;
    letter-spacing: 0.06em !important; text-transform: uppercase !important;
    width: 100% !important; transition: all 0.2s ease !important;
}
@media (min-width: 768px) {
    .stDownloadButton > button { width: auto !important; }
}

.streamlit-expanderHeader {
    background: linear-gradient(135deg, #f8fafd 0%, #f0f5fc 100%) !important;
    border-radius: 12px !important; font-weight: 700 !important;
    color: #002855 !important; font-size: 0.88rem !important;
    border: 1.5px solid #dce8f0 !important; padding: 14px 16px !important;
    min-height: 48px !important;
}

[data-testid="stMetric"] {
    background: white !important; border: 1px solid #e0e8f0 !important;
    border-radius: 14px !important; padding: 12px 14px !important;
    box-shadow: 0 2px 12px rgba(0,40,85,0.07) !important;
    border-top: 3px solid #B8860B !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important; font-weight: 600 !important;
    letter-spacing: 0.08em !important; text-transform: uppercase !important;
    color: #5a7a9a !important;
}
[data-testid="stMetricValue"] {
    font-weight: 800 !important; color: #002855 !important; font-size: 1.1rem !important;
}
@media (min-width: 768px) {
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
}

section.main .stMarkdown p,
section.main .stMarkdown strong,
section.main [data-testid="stMarkdownContainer"] p,
section.main [data-testid="stMarkdownContainer"] strong { color: #1e1e1e !important; }
section.main [data-testid="stCaptionContainer"] p,
section.main .stCaption p { color: #5a7a9a !important; }
section.main [data-testid="stExpander"] p,
section.main [data-testid="stExpander"] span,
section.main [data-testid="stExpander"] strong,
section.main [data-testid="stExpander"] li { color: #1e1e1e !important; }

hr {
    border: none !important;
    background: linear-gradient(90deg, transparent, #B8860B, transparent) !important;
    height: 2px !important; margin: 14px 0 !important;
}
[data-testid="stToast"] {
    background: #002855 !important; color: white !important;
    border-left: 4px solid #B8860B !important; border-radius: 10px !important;
    font-weight: 600 !important;
}
[data-testid="stAlert"] { border-radius: 10px !important; font-size: 0.88rem !important; }

.price-info-box {
    background: linear-gradient(135deg, #002855, #004080); color: white;
    border-radius: 12px; padding: 12px 16px; font-weight: 700; font-size: 0.88rem;
    border-left: 4px solid #B8860B; box-shadow: 0 4px 16px rgba(0,40,85,0.25);
    margin: 8px 0; line-height: 1.8;
}
.price-info-box span { color: #f0c040; font-size: 1rem; }

.feature-card {
    background: white; border-radius: 14px; padding: 18px 14px;
    border: 1px solid #e0e8f0; border-top: 3px solid #B8860B;
    box-shadow: 0 4px 16px rgba(0,40,85,0.08); text-align: center;
    margin-bottom: 12px;
}
.feature-card .icon { font-size: 2rem; margin-bottom: 8px; }
.feature-card h4 { color: #002855; font-weight: 700; font-size: 0.95rem; margin-bottom: 4px; }
.feature-card p { color: #7a9ab8; font-size: 0.78rem; line-height: 1.5; margin: 0; }

.pwd-box {
    background: white; border-radius: 16px; padding: 28px 24px;
    border: 1px solid #e0e8f0; border-top: 4px solid #B8860B;
    box-shadow: 0 6px 24px rgba(0,40,85,0.12);
}

[data-testid="column"] { padding: 0 4px !important; }
@media (min-width: 768px) { [data-testid="column"] { padding: 0 8px !important; } }

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-thumb { background: rgba(0,40,85,0.2); border-radius: 4px; }

@supports (padding-bottom: env(safe-area-inset-bottom)) {
    .stApp { padding-bottom: env(safe-area-inset-bottom); }
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──
def render_header(title, subtitle="", right_badge=""):
    badge_html = f'<div class="top-header-badge">{right_badge}</div>' if right_badge else ""
    st.markdown(f"""
    <div class="top-header">
        <div>
            <div class="top-header-title">{title}</div>
            <div class="top-header-subtitle">{subtitle if subtitle else SLOGAN}</div>
            {badge_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_section_title(text):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)

def get_creds():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)

def connect_gsheet():
    try:
        client = gspread.authorize(get_creds())
        sheet = client.open("Antrean Penawaran TTS").sheet1
        if not sheet.get_all_values():
            sheet.append_row(["Waktu", "Customer", "UP", "WA", "Pesanan", "Status", "Sales"])
        return sheet
    except Exception as e:
        st.error(f"Koneksi GSheets Gagal: {e}")
        return None

@st.cache_data(ttl=300)
def load_db():
    if os.path.exists("database_barang.csv"):
        try:
            df = pd.read_csv("database_barang.csv", sep=None, engine='python', on_bad_lines='skip')
            df.columns = df.columns.str.strip()
            if 'Harga' in df.columns:
                df['Harga'] = pd.to_numeric(df['Harga'], errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"Gagal membaca CSV: {e}")
    return pd.DataFrame(columns=['Nama Barang', 'Harga', 'Satuan'])

df_barang = load_db()

def item_key(row_idx, nama_barang):
    h = hashlib.md5(nama_barang.encode()).hexdigest()[:8]
    return f"r{row_idx}_{h}"

def clear_row_state(real_row_idx):
    keys_to_del = [k for k in list(st.session_state.keys()) if k.startswith(f"r{real_row_idx}_")]
    for k in keys_to_del:
        del st.session_state[k]

def read_row_fresh(sheet, row_idx):
    try:
        time.sleep(0.5)
        vals = sheet.row_values(row_idx)
        if len(vals) > 4 and vals[4].strip():
            return ast.literal_eval(vals[4])
        return []
    except Exception as e:
        return []

def save_to_gsheet_verified(sheet, row_idx, save_data):
    try:
        sheet.update_cell(row_idx, 5, str(save_data))
        time.sleep(1.5)
        verify = sheet.row_values(row_idx)
        if len(verify) > 4:
            try:
                parsed = ast.literal_eval(verify[4])
                if len(parsed) == len(save_data):
                    return True, "OK"
                else:
                    return False, f"Jumlah item tidak cocok: {len(parsed)} vs {len(save_data)}"
            except:
                return False, "Gagal parse data setelah simpan"
        return False, "Row kosong setelah simpan"
    except Exception as e:
        return False, str(e)


# =========================================================
# SESSION STATE
# =========================================================
if "active_menu" not in st.session_state:
    st.session_state.active_menu = "🏠 Home"
if "cart" not in st.session_state:
    st.session_state.cart = []
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "widget_id" not in st.session_state:
    st.session_state.widget_id = 0
if "saved_items_cache" not in st.session_state:
    st.session_state.saved_items_cache = {}


# =========================================================
# TOP NAVIGATION BAR
# =========================================================
st.markdown('<div class="topnav-container">', unsafe_allow_html=True)
nc1, nc2, nc3 = st.columns(3)
with nc1:
    if st.button("🏠 Home", key="nav_home", use_container_width=True,
                 type="primary" if st.session_state.active_menu == "🏠 Home" else "secondary"):
        st.session_state.active_menu = "🏠 Home"
        st.rerun()
with nc2:
    if st.button("📝 Admin Sales", key="nav_admin", use_container_width=True,
                 type="primary" if st.session_state.active_menu == "📝 Admin Sales" else "secondary"):
        st.session_state.active_menu = "📝 Admin Sales"
        st.rerun()
with nc3:
    if st.button("📊 Dashboard", key="nav_dash", use_container_width=True,
                 type="primary" if st.session_state.active_menu == "👨‍💻 Sales Dashboard" else "secondary"):
        st.session_state.active_menu = "👨‍💻 Sales Dashboard"
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

menu = st.session_state.active_menu


# =========================================================
# PDF GENERATOR  ← REVISI VISUAL
# =========================================================
class PenawaranPDF(FPDF):
    def __init__(self, total_pages=1):
        super().__init__()
        self.total_pages = total_pages

    def header(self):
        # Background navy penuh
        self.set_fill_color(*COLOR_NAVY)
        self.rect(0, 0, 210, 52, 'F')

        # Strip putih area logo
        self.set_fill_color(255, 255, 255)
        self.rect(10, 6, 44, 40, 'F')

        # Garis gold vertikal tebal sebagai pemisah
        self.set_fill_color(*COLOR_GOLD)
        self.rect(58, 0, 3, 52, 'F')

        # Logo jika ada
        if os.path.exists("logo.png"):
            self.image("logo.png", 13, 10, 38)

        # Nama perusahaan
        self.set_y(10); self.set_x(66)
        self.set_font('Arial', 'B', 17)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, COMPANY_NAME, ln=1)

        # Slogan gold
        self.set_x(66)
        self.set_font('Arial', 'B', 8.5)
        self.set_text_color(*COLOR_GOLD)
        self.cell(0, 5, "  ".join(SLOGAN.upper()), ln=1)

        # Garis tipis pemisah
        self.set_fill_color(255, 255, 255)
        self.rect(66, 26, 132, 0.3, 'F')

        # Detail kontak
        self.set_y(29); self.set_x(66)
        self.set_font('Arial', '', 7.5)
        self.set_text_color(210, 220, 235)
        self.cell(0, 4.5, ADDR, ln=1)
        self.set_x(66)
        self.cell(0, 4.5, f"Office: {OFFICE_PHONE}  |  WA: {MARKETING_WA}", ln=1)
        self.set_x(66)
        self.cell(0, 4.5, f"Email: {MARKETING_EMAIL}", ln=1)

        # Garis gold bawah header
        self.set_fill_color(*COLOR_GOLD)
        self.rect(0, 52, 210, 2.5, 'F')

        self.set_y(62)

    def footer(self):
        self.set_y(-18)
        # Garis gold atas footer
        self.set_fill_color(*COLOR_GOLD)
        self.rect(0, self.get_y(), 210, 1.5, 'F')

        # Background navy footer
        self.set_fill_color(*COLOR_NAVY)
        self.rect(0, self.get_y() + 1.5, 210, 17, 'F')

        self.set_y(-14)
        self.set_font('Arial', 'B', 8)
        self.set_text_color(255, 255, 255)
        self.cell(0, 5, SLOGAN.upper(), 0, 1, 'C')

        self.set_font('Arial', '', 7)
        self.set_text_color(*COLOR_GOLD)
        self.cell(0, 4,
                  f"{COMPANY_NAME}  |  {ADDR}  |  Hal. {self.page_no()} / {self.total_pages}",
                  0, 0, 'C')


def draw_table_header(pdf):
    # Background header tabel navy
    pdf.set_fill_color(*COLOR_NAVY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_draw_color(*COLOR_GOLD)
    pdf.set_line_width(0.4)

    pdf.cell(10,  10, 'NO',          border=1, align='C', fill=True)
    pdf.cell(82,  10, 'DESKRIPSI',   border=1, align='C', fill=True)
    pdf.cell(18,  10, 'QTY',         border=1, align='C', fill=True)
    pdf.cell(20,  10, 'SATUAN',      border=1, align='C', fill=True)
    pdf.cell(30,  10, 'HARGA',       border=1, align='C', fill=True)
    pdf.cell(30,  10, 'TOTAL',       border=1, align='C', fill=True)
    pdf.ln()


def generate_pdf(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    # T&C block tingginya sekitar 58mm, area total ~35mm, margin bawah 25mm
    # Gunakan 2-pass: render dulu tanpa total_pages, hitung, render ulang
    def _render(pdf):
        pdf.set_margins(10, 70, 10)
        pdf.set_auto_page_break(auto=True, margin=28)
        pdf.add_page()

        # ── Judul QUOTATION ──
        pdf.set_y(62)
        pdf.set_font('Arial', 'B', 26)
        pdf.set_text_color(*COLOR_NAVY)
        pdf.cell(0, 10, "QUOTATION", ln=1, align='R')

        pdf.set_draw_color(*COLOR_GOLD)
        pdf.set_line_width(0.8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

        waktu_skrg  = datetime.utcnow() + timedelta(hours=7)
        expiry_date = waktu_skrg + timedelta(days=7)
        pdf.set_font('Arial', '', 8.5)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"No. Surat   : {no_surat}", ln=1, align='R')
        pdf.cell(0, 5, f"Tanggal      : {waktu_skrg.strftime('%d %B %Y')}", ln=1, align='R')
        pdf.cell(0, 5, f"Berlaku s/d  : {expiry_date.strftime('%d %B %Y')}", ln=1, align='R')
        pdf.ln(4)

        # ── Info Customer ──
        pdf.set_x(10)
        pdf.set_font('Arial', 'B', 7.5)
        pdf.set_text_color(*COLOR_GOLD)
        pdf.cell(90, 5, "DITUJUKAN KEPADA:", ln=1)

        pdf.set_x(10)
        pdf.set_font('Arial', 'B', 13)
        pdf.set_text_color(*COLOR_NAVY)
        pdf.cell(90, 7, str(nama_cust).upper(), ln=1)

        pdf.set_x(10)
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(*COLOR_TEXT)
        pdf.cell(90, 5, f"U/P: {pic}", ln=1)
        pdf.ln(6)

        # ── Tabel ──
        draw_table_header(pdf)
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(*COLOR_TEXT)

        for i, row in df_order.iterrows():
            # Cek apakah baris berikutnya + area total + T&C masih muat
            # Estimasi ruang yang dibutuhkan setelah tabel: ~100mm
            if pdf.get_y() > 170:
                pdf.add_page()
                draw_table_header(pdf)
                pdf.set_font('Arial', '', 9)
                pdf.set_text_color(*COLOR_TEXT)

            if i % 2 == 0:
                pdf.set_fill_color(240, 245, 252)
            else:
                pdf.set_fill_color(255, 255, 255)

            pdf.set_draw_color(180, 195, 215)
            pdf.set_line_width(0.2)

            pdf.cell(10, 8, str(i + 1),               border=1, align='C', fill=True)
            pdf.cell(82, 8, f" {str(row['Nama Barang'])}", border=1, align='L', fill=True)
            pdf.cell(18, 8, str(int(row['Qty'])),      border=1, align='C', fill=True)
            pdf.cell(20, 8, str(row['Satuan']),        border=1, align='C', fill=True)
            pdf.cell(30, 8, f"Rp {row['Harga']:,.0f}", border=1, align='R', fill=True)
            pdf.cell(30, 8, f"Rp {row['Total_Row']:,.0f}", border=1, align='R', fill=True)
            pdf.ln()

        # ── Area Total ──
        pdf.ln(4)
        pdf.set_draw_color(*COLOR_GOLD)
        pdf.set_line_width(0.6)
        pdf.line(120, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(*COLOR_TEXT)
        pdf.set_x(120)
        pdf.cell(50, 7, "Sub Total", align='L')
        pdf.cell(30, 7, f"Rp {subtotal:,.0f}", align='R', ln=1)

        pdf.set_x(120)
        pdf.cell(50, 7, "PPN 11%", align='L')
        pdf.cell(30, 7, f"Rp {ppn:,.0f}", align='R', ln=1)

        pdf.set_draw_color(*COLOR_NAVY)
        pdf.set_line_width(0.4)
        pdf.line(120, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(1)

        pdf.set_fill_color(*COLOR_NAVY)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_x(120)
        pdf.cell(50, 10, "  GRAND TOTAL", border=0, align='L', fill=True)
        pdf.cell(30, 10, f"Rp {grand_total:,.0f}  ", border=0, align='R', fill=True, ln=1)

        pdf.set_draw_color(*COLOR_GOLD)
        pdf.set_line_width(0.8)
        pdf.line(120, pdf.get_y(), 200, pdf.get_y())

        # ── Cek ruang untuk T&C — tinggi blok T&C = 62mm ──
        TC_HEIGHT = 55
        BOTTOM_LIMIT = 297 - 28  # A4 - margin bawah = 269mm
        if pdf.get_y() + 10 + TC_HEIGHT > BOTTOM_LIMIT:
            pdf.add_page()
            pdf.set_y(68)
        else:
            pdf.ln(10)

        # ── T&C + Marketing dalam 1 blok sejajar ──
        y_tc = pdf.get_y()

        # Kotak T&C kiri
        pdf.set_fill_color(248, 250, 253)
        pdf.set_draw_color(*COLOR_NAVY)
        pdf.set_line_width(0.4)
        pdf.rect(10, y_tc, 120, TC_HEIGHT, 'DF')

        pdf.set_y(y_tc + 3)
        pdf.set_x(13)
        pdf.set_font('Arial', 'B', 9)
        pdf.set_text_color(*COLOR_NAVY)
        pdf.cell(116, 5, "SYARAT & KETENTUAN:", ln=1)

        pdf.set_draw_color(*COLOR_GOLD)
        pdf.set_line_width(0.5)
        pdf.line(13, pdf.get_y(), 127, pdf.get_y())
        pdf.ln(2)

        pdf.set_x(13)
        pdf.set_font('Arial', '', 8.5)
        pdf.set_text_color(50, 50, 50)
        terms = (
            "1. Harga dapat berubah sewaktu-waktu tanpa pemberitahuan.\n"
            "2. Penawaran berlaku 7 hari dari tanggal surat.\n"
            "3. Pengiriman 1 hari kerja setelah konfirmasi PO.\n"
            "4. Pembayaran ditransfer HANYA ke rekening berikut:\n"
            "   Bank       : Bank Mandiri\n"
            "   No. Rek    : 1550010174996\n"
            "   Atas Nama  : PT THEA THEO STATIONARY"
        )
        # Gunakan set_x sebelum multi_cell agar tidak overflow ke kanan
        pdf.set_x(13)
        pdf.multi_cell(114, 5.5, terms)

        # Info Marketing (kanan, sejajar T&C)
        # ── Blok Marketing (kanan T&C) ──
        # Layout: MARKETING label → TTD+stempel (kecil, proporsional) → nama → WA → email
        # Semua teks di x=138, TTD di x=135 agar sedikit ke kiri dari label
        y_mkt = y_tc + 3

        pdf.set_y(y_mkt)
        pdf.set_x(138)
        pdf.set_font('Arial', 'B', 8.5)
        pdf.set_text_color(*COLOR_GOLD)
        pdf.cell(60, 5, "MARKETING:", ln=1)

        # TTD height di PDF = 22mm, width proporsional
        TTD_H_MM = 42
        ttd_path = "ttd_clean.png"
        y_ttd_start = pdf.get_y() + 1

        if os.path.exists(ttd_path):
            try:
                from PIL import Image as PILImage
                import numpy as _np
                ttd_img = PILImage.open(ttd_path).convert("RGBA")
                ttd_w_px, ttd_h_px = ttd_img.size
                # Hitung lebar di PDF proporsional terhadap tinggi 22mm
                ttd_w_mm = TTD_H_MM * ttd_w_px / ttd_h_px

                if os.path.exists("logo.png"):
                    logo_img = PILImage.open("logo.png").convert("RGBA")
                    # Logo 60% lebar TTD, proporsional
                    lw = int(ttd_w_px * 0.60)
                    lh = int(logo_img.height * lw / logo_img.width)
                    logo_img = logo_img.resize((lw, lh), PILImage.LANCZOS)
                    logo_arr = _np.array(logo_img)
                    logo_arr[:,:,3] = (logo_arr[:,:,3] * 0.80).astype(_np.uint8)
                    logo_faded = PILImage.fromarray(logo_arr)
                    lx = (ttd_w_px - lw) // 2
                    ly = max(0, (ttd_h_px - lh) // 2)
                    canvas = ttd_img.copy()
                    canvas.paste(logo_faded, (lx, ly), logo_faded)
                    tmp_path = "/tmp/ttd_stamp_combined.png"
                    canvas.save(tmp_path)
                    pdf.image(tmp_path, x=137, y=y_ttd_start, h=TTD_H_MM)
                else:
                    pdf.image(ttd_path, x=137, y=y_ttd_start, h=TTD_H_MM)
            except Exception:
                pdf.image(ttd_path, x=137, y=y_ttd_start, h=TTD_H_MM)

        # Teks di bawah TTD
        pdf.set_y(y_ttd_start + TTD_H_MM + 1)
        pdf.set_x(138)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(*COLOR_NAVY)
        pdf.cell(60, 6, MARKETING_NAME.upper(), ln=1)

        pdf.set_x(138)
        pdf.set_font('Arial', '', 8.5)
        pdf.set_text_color(*COLOR_TEXT)
        pdf.cell(60, 5, f"WA    : {MARKETING_WA}", ln=1)
        pdf.set_x(138)
        pdf.cell(60, 5, f"Email : {MARKETING_EMAIL}", ln=1)

    # Pass 1: hitung jumlah halaman
    pdf1 = PenawaranPDF(total_pages=99)
    _render(pdf1)
    total_pages = pdf1.page

    # Pass 2: render final dengan total_pages yang benar
    pdf2 = PenawaranPDF(total_pages=total_pages)
    _render(pdf2)

    return pdf2.output(dest='S').encode('latin-1')


# =========================================================
# EXCEL GENERATOR
# =========================================================
def generate_excel(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook  = writer.book
        worksheet = workbook.add_worksheet('Quotation')
        fmt_navy_bg      = workbook.add_format({'bg_color': '#002855', 'font_color': 'white', 'bold': True, 'font_size': 18, 'valign': 'vcenter'})
        fmt_gold_text    = workbook.add_format({'font_color': '#B8860B', 'bold': True, 'font_size': 10})
        fmt_white_text   = workbook.add_format({'font_color': 'white', 'font_size': 9})
        fmt_header_table = workbook.add_format({'bg_color': '#002855', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_border       = workbook.add_format({'border': 1})
        fmt_money        = workbook.add_format({'border': 1, 'num_format': '#,##0'})
        fmt_total_label  = workbook.add_format({'bold': True, 'align': 'right'})
        fmt_grand_total  = workbook.add_format({'bg_color': '#002855', 'font_color': 'white', 'bold': True, 'num_format': '#,##0', 'align': 'right'})
        worksheet.set_column('A:A', 5);  worksheet.set_column('B:B', 45); worksheet.set_column('C:C', 10)
        worksheet.set_column('D:D', 10); worksheet.set_column('E:E', 15); worksheet.set_column('F:F', 18)
        for r in range(0, 5): worksheet.write_blank(r, 0, '', fmt_navy_bg)
        worksheet.merge_range('B2:F2', COMPANY_NAME, fmt_navy_bg)
        worksheet.write('B3', "  ".join(SLOGAN.upper()), fmt_gold_text)
        worksheet.write('B4', f"{ADDR} | Office: {OFFICE_PHONE}", fmt_white_text)
        worksheet.write('B5', f"WhatsApp: {MARKETING_WA} | Email: {MARKETING_EMAIL}", fmt_white_text)
        worksheet.write('B7', "PREPARED FOR:", fmt_gold_text)
        worksheet.write('B8', nama_cust.upper(), workbook.add_format({'bold': True, 'font_size': 12}))
        worksheet.write('B9', f"Attention: {pic}")
        worksheet.write('F7', "QUOTATION", workbook.add_format({'bold': True, 'font_size': 20, 'align': 'right', 'font_color': '#002855'}))
        worksheet.write('F8', f"Ref: {no_surat}", workbook.add_format({'align': 'right'}))
        worksheet.write('F9', f"Date: {(datetime.utcnow() + timedelta(hours=7)).strftime('%d %B %Y')}", workbook.add_format({'align': 'right'}))
        header_row = 11
        for col_num, data in enumerate(['NO', 'DESCRIPTION', 'QTY', 'UNIT', 'PRICE', 'TOTAL']):
            worksheet.write(header_row, col_num, data, fmt_header_table)
        row_idx = 12
        for i, row in df_order.iterrows():
            worksheet.write(row_idx, 0, i+1, fmt_border); worksheet.write(row_idx, 1, row['Nama Barang'], fmt_border)
            worksheet.write(row_idx, 2, row['Qty'], fmt_border); worksheet.write(row_idx, 3, row['Satuan'], fmt_border)
            worksheet.write(row_idx, 4, row['Harga'], fmt_money); worksheet.write(row_idx, 5, row['Total_Row'], fmt_money)
            row_idx += 1
        row_idx += 1
        worksheet.write(row_idx, 4, "Sub Total", fmt_total_label); worksheet.write(row_idx, 5, subtotal, fmt_money); row_idx += 1
        worksheet.write(row_idx, 4, "VAT (PPN 11%)", fmt_total_label); worksheet.write(row_idx, 5, ppn, fmt_money); row_idx += 1
        worksheet.write(row_idx, 4, "GRAND TOTAL", fmt_total_label); worksheet.write(row_idx, 5, grand_total, fmt_grand_total)
    return output.getvalue()


# =========================================================
# HOME
# =========================================================
if menu == "🏠 Home":
    render_header(COMPANY_NAME, SLOGAN, f"📍 {ADDR.split(',')[0]}")

    c1, c2 = st.columns(2)
    c1.metric("🧑‍💼 Marketing", MARKETING_NAME)
    c2.metric("📞 WhatsApp", MARKETING_WA)
    c3, c4 = st.columns(2)
    c3.metric("📧 Email", "alattulis.tts")
    c4.metric("🏢 Kantor", OFFICE_PHONE)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class="feature-card"><div class="icon">📝</div><h4>Form Penawaran</h4><p>Buat daftar pesanan, cari barang, atur satuan & harga, kirim ke sales.</p></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="feature-card"><div class="icon">📄</div><h4>Generate Quotation</h4><p>Unduh quotation PDF atau Excel siap kirim ke pelanggan.</p></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="feature-card"><div class="icon">📊</div><h4>Sales Dashboard</h4><p>Kelola antrean, edit item, dan tandai penawaran selesai.</p></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 Ketuk tombol navigasi di atas untuk berpindah halaman.")


# =========================================================
# ADMIN SALES
# =========================================================
elif menu == "📝 Admin Sales":
    render_header("Form Penawaran", "Buat & kirim penawaran baru", "📋 Admin Sales")

    render_section_title("👤 Data Pelanggan")
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        nama_toko = col1.text_input("🏢 Nama Perusahaan / Toko", placeholder="PT. Contoh Maju Bersama")
        up_nama   = col2.text_input("👤 Nama Penerima (UP)", placeholder="Bapak / Ibu ...")
        wa_nomor  = col3.text_input("📞 Nomor WhatsApp", placeholder="08xx-xxxx-xxxx")

    render_section_title("📦 Tambah Barang ke Keranjang")
    with st.container(border=True):
        pilihan_barang = st.selectbox(
            "🔍 Cari & Pilih Nama Barang:",
            options=[""] + df_barang['Nama Barang'].tolist(),
            key=f"pilih_brg_{st.session_state.widget_id}"
        )
        if pilihan_barang != "":
            row_m = df_barang[df_barang['Nama Barang'] == pilihan_barang].iloc[0]
            h_master = float(row_m['Harga']); satuan_db = str(row_m['Satuan']).strip()

            c1, c2 = st.columns(2)
            mode_c = c1.selectbox(f"Satuan (Default: {satuan_db})",
                                  ["Sesuai Database", "Lusin (12)", "Dus", "Box", "Pack", "Set"],
                                  key=f"m_c_{st.session_state.widget_id}")
            mult_c = 1; sat_final = satuan_db
            if mode_c == "Lusin (12)":
                mult_c = 12; sat_final = "Lusin"
            elif mode_c in ["Dus", "Box", "Pack", "Set"]:
                isi_c = st.number_input(f"Isi per {mode_c}", min_value=1, value=10,
                                        key=f"isi_c_{st.session_state.widget_id}")
                mult_c = isi_c; sat_final = mode_c

            qty_c    = c2.number_input(f"Jumlah ({sat_final})", min_value=1, value=1,
                                       key=f"qty_c_{st.session_state.widget_id}")
            h_jual_c = int(h_master * mult_c)

            st.markdown(f"""
            <div class="price-info-box">
                💰 Harga: <span>Rp {h_jual_c:,.0f}</span> / {sat_final}<br>
                🔢 Qty: <span>{int(qty_c)} {sat_final}</span> &nbsp;|&nbsp;
                💵 Total: <span>Rp {int(qty_c * h_jual_c):,.0f}</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("➕ Masukkan ke Keranjang", use_container_width=True, type="primary"):
                st.session_state.cart = [x for x in st.session_state.cart if x['Nama Barang'] != pilihan_barang]
                st.session_state.cart.append({
                    "Nama Barang": pilihan_barang, "Qty": int(qty_c),
                    "Harga": float(h_jual_c), "Satuan": sat_final,
                    "Total_Row": float(qty_c * h_jual_c)
                })
                st.session_state.widget_id += 1
                st.toast(f"✅ Ditambahkan: {pilihan_barang}"); time.sleep(0.2); st.rerun()
        else:
            st.markdown("""<div style="text-align:center; padding:20px 0; color:#7a9ab8;">
                <div style="font-size:2rem; margin-bottom:8px;">🔍</div>
                <div style="font-size:0.88rem; color:#5a7a9a;">Ketik atau klik dropdown di atas untuk mencari barang</div>
            </div>""", unsafe_allow_html=True)

    if st.session_state.cart:
        render_section_title(f"🛒 Keranjang ({len(st.session_state.cart)} item)")
        total_cart = sum(x['Total_Row'] for x in st.session_state.cart)
        tax_cart   = total_cart * 0.11
        grand_cart = total_cart + tax_cart

        m1, m2 = st.columns(2)
        m1.metric("📦 Item", f"{len(st.session_state.cart)} jenis")
        m2.metric("💵 Sub Total", f"Rp {total_cart:,.0f}")
        st.metric("🧾 Total + PPN", f"Rp {grand_cart:,.0f}")
        st.markdown("<br>", unsafe_allow_html=True)

        for i, item in enumerate(st.session_state.cart):
            with st.container(border=True):
                st.markdown(
                    f"<span style='color:#002855;font-weight:700;font-size:0.95rem;'>{item['Nama Barang']}</span><br>"
                    f"<span style='color:#5a7a9a;font-size:0.80rem;'>@ Rp {item['Harga']:,.0f} / {item['Satuan']}</span>",
                    unsafe_allow_html=True
                )
                ca, cb = st.columns([3, 1])
                ca.markdown(
                    f"<span style='color:#002855;font-weight:700;'>🔢 {item['Qty']} {item['Satuan']} &nbsp;·&nbsp; Rp {item['Total_Row']:,.0f}</span>",
                    unsafe_allow_html=True
                )
                if cb.button("✕ Hapus", key=f"del_item_{i}"):
                    st.session_state.cart.pop(i); st.rerun()

        st.divider()
        if st.button(f"🚀 KIRIM PENAWARAN KE PAK {MARKETING_NAME.upper()}", use_container_width=True, type="primary"):
            if not nama_toko:
                st.error("⚠️ Nama Toko/Perusahaan wajib diisi!")
            else:
                sheet = connect_gsheet()
                if sheet:
                    wkt = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")
                    sheet.append_row([wkt, nama_toko, up_nama, wa_nomor, str(st.session_state.cart), "Pending", MARKETING_NAME])
                    st.balloons(); st.success(f"✅ Penawaran untuk **{nama_toko}** berhasil terkirim!")
                    st.session_state.cart = []; time.sleep(1); st.rerun()

        if st.button("🗑️ Kosongkan Keranjang", use_container_width=True):
            st.session_state.cart = []; st.rerun()


# =========================================================
# SALES DASHBOARD
# =========================================================
elif menu == "👨‍💻 Sales Dashboard":
    render_header("Sales Dashboard", f"Kelola antrean · {MARKETING_NAME}", "🔐 Admin Only")

    # ── BELUM LOGIN ──
    if not st.session_state.admin_logged_in:
        st.markdown("<br>", unsafe_allow_html=True)
        _, mid_col, _ = st.columns([1, 2, 1])
        with mid_col:
            st.markdown('<div class="pwd-box">', unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align:center; margin-bottom:24px;">
                <div style="font-size:2.8rem;">🔐</div>
                <div style="font-family:'Playfair Display',serif;font-size:1.15rem;color:#002855;font-weight:700;margin-top:10px;">Login Admin</div>
                <div style="font-size:0.82rem;color:#7a9ab8;margin-top:6px;">Masukkan password untuk mengakses dashboard</div>
            </div>
            """, unsafe_allow_html=True)

            pwd_input = st.text_input(
                "🔑 Password Admin",
                type="password",
                placeholder="Masukkan password...",
                key="pwd_field_main"
            )
            if st.button("🚀 MASUK KE DASHBOARD", use_container_width=True, type="primary", key="btn_login_main"):
                if pwd_input == ADMIN_PASSWORD:
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Password salah. Coba lagi.")

            st.markdown('</div>', unsafe_allow_html=True)

    # ── SUDAH LOGIN ──
    else:
        col_inf, col_out, col_ref = st.columns([3, 1, 1])
        col_inf.success(f"✅ Login sebagai **{MARKETING_NAME}**")
        if col_out.button("🚪 Logout", use_container_width=True, key="btn_logout"):
            st.session_state.admin_logged_in = False
            st.rerun()
        if col_ref.button("🔄 Refresh", use_container_width=True, key="btn_refresh"):
            st.session_state.saved_items_cache = {}
            st.cache_data.clear()
            st.rerun()

        # ── Update Database Barang ──
        with st.expander("📁 Update Database Barang (.csv)", expanded=False):
            st.caption("Upload file CSV baru untuk mengganti database produk.")
            up_f2 = st.file_uploader("Pilih file CSV baru:", type=["csv"], key="csv_up_login")
            if up_f2:
                if st.button("🚀 Update Database Sekarang", key="btn_csv_login", type="primary"):
                    with open("database_barang.csv", "wb") as f:
                        f.write(up_f2.getbuffer())
                    st.cache_data.clear()
                    st.success("✅ Database berhasil diperbarui!")
                    time.sleep(1); st.rerun()

        sheet = connect_gsheet()
        if sheet:
            try:
                all_vals = sheet.get_all_values()
                if len(all_vals) > 1:
                    raw_headers   = all_vals[0]
                    clean_headers = [h.strip().lstrip('\ufeff') for h in raw_headers]
                    required_cols = ["Waktu", "Customer", "UP", "WA", "Pesanan", "Status", "Sales"]
                    df_gs = pd.DataFrame(all_vals[1:], columns=clean_headers)
                    for col in required_cols:
                        if col not in df_gs.columns: df_gs[col] = ""
                    for col in required_cols:
                        df_gs[col] = df_gs[col].astype(str).str.strip()

                    pending = df_gs[
                        (df_gs['Status'].str.lower() == 'pending') &
                        (df_gs['Sales'] == MARKETING_NAME)
                    ]

                    total_all     = len(df_gs[df_gs['Sales'] == MARKETING_NAME])
                    total_pending = len(pending)
                    total_done    = total_all - total_pending

                    dm1, dm2, dm3 = st.columns(3)
                    dm1.metric("📋 Total",  total_all)
                    dm2.metric("⏳ Pending", total_pending)
                    dm3.metric("✅ Selesai", total_done)
                    st.markdown("<br>", unsafe_allow_html=True)

                    if not pending.empty:
                        render_section_title(f"⏳ Antrean Pending ({total_pending})")

                        for idx, row in pending.iterrows():
                            real_row_idx = idx + 2
                            try:
                                items_preview = ast.literal_eval(str(row['Pesanan']))
                                n_items = len(items_preview)
                            except:
                                items_preview = []; n_items = 0

                            waktu_val    = row.get('Waktu', '')
                            customer_val = row.get('Customer', '')
                            up_val       = row.get('UP', '')
                            wa_val       = row.get('WA', '')

                            with st.expander(f"🏢 {customer_val} · {n_items} item · {waktu_val}", expanded=True):
                                st.info(f"🏢 **{customer_val}** &nbsp;|&nbsp; 👤 UP: **{up_val}** &nbsp;|&nbsp; 📞 **{wa_val}**")
                                st.markdown("---")

                                try:
                                    items_list = ast.literal_eval(str(row['Pesanan']))
                                except:
                                    items_list = []

                                if real_row_idx in st.session_state.saved_items_cache:
                                    items_list = st.session_state.saved_items_cache[real_row_idx]

                                render_section_title("📝 Edit Daftar Barang")
                                st.caption("💡 Ubah **Pos** untuk urutan. Centang 🗑️ untuk hapus.")

                                for i, r in enumerate(items_list):
                                    nama_item = r['Nama Barang']
                                    u_k = item_key(real_row_idx, nama_item)
                                    if f"h_{u_k}" not in st.session_state:
                                        st.session_state[f"h_{u_k}"] = int(float(r.get('Harga', 0)))
                                    if f"s_{u_k}" not in st.session_state:
                                        st.session_state[f"s_{u_k}"] = str(r.get('Satuan', 'Pcs')).strip()
                                    if f"q_{u_k}" not in st.session_state:
                                        st.session_state[f"q_{u_k}"] = int(r.get('Qty', 1))
                                    if f"p_{u_k}" not in st.session_state:
                                        st.session_state[f"p_{u_k}"] = float(i + 1)
                                    if f"m_{u_k}" not in st.session_state:
                                        st.session_state[f"m_{u_k}"] = "Pcs/Tetap"
                                    if f"isi_{u_k}" not in st.session_state:
                                        st.session_state[f"isi_{u_k}"] = 10

                                temp_up   = []
                                list_mode = ["Pcs/Tetap", "Lusin (12)", "Dus", "Box", "Pack", "Set", "Rim"]

                                for i, r in enumerate(items_list):
                                    nama_item    = r['Nama Barang']
                                    u_k          = item_key(real_row_idx, nama_item)
                                    row_master   = df_barang[df_barang['Nama Barang'] == nama_item]
                                    harga_master = float(row_master['Harga'].values[0]) if not row_master.empty else float(r.get('Harga', 0))
                                    satuan_master= str(row_master['Satuan'].values[0]).strip() if not row_master.empty else str(r.get('Satuan', 'Pcs'))

                                    with st.container(border=True):
                                        harga_tersimpan  = st.session_state.get(f"h_{u_k}", int(float(r.get('Harga', 0))))
                                        satuan_tersimpan = st.session_state.get(f"s_{u_k}", str(r.get('Satuan', '')))
                                        st.markdown(
                                            f"<span style='color:#002855;font-weight:700;font-size:0.95rem;'>{nama_item}</span><br>"
                                            f"<span style='color:#5a7a9a;font-size:0.75rem;'>📋 Master: Rp {harga_master:,.0f} / {satuan_master}</span><br>"
                                            f"<span style='color:#B8860B;font-size:0.75rem;font-weight:600;'>💾 Tersimpan: Rp {harga_tersimpan:,.0f} / {satuan_tersimpan}</span>",
                                            unsafe_allow_html=True
                                        )
                                        st.markdown("")
                                        c1, c2 = st.columns(2)
                                        mode = c1.selectbox("Kalkulasi", list_mode, key=f"m_{u_k}")
                                        nq   = c2.number_input("Qty", min_value=1, step=1, key=f"q_{u_k}")

                                        if mode in ["Dus", "Box", "Pack", "Set"]:
                                            st.number_input(f"Isi per {mode}", min_value=1, step=1, key=f"isi_{u_k}")

                                        if mode != "Pcs/Tetap":
                                            if mode == "Lusin (12)":
                                                harga_kalkulasi = int(harga_master * 12); sat_kalkulasi = "Lusin"
                                            elif mode == "Rim":
                                                harga_kalkulasi = int(harga_master); sat_kalkulasi = "Rim"
                                            else:
                                                isi_val = st.session_state.get(f"isi_{u_k}", 10)
                                                harga_kalkulasi = int(harga_master * isi_val); sat_kalkulasi = mode
                                            if st.button(f"▶ Apply {sat_kalkulasi} — Rp {harga_kalkulasi:,.0f}", key=f"apply_{u_k}", use_container_width=True):
                                                st.session_state[f"h_{u_k}"] = harga_kalkulasi
                                                st.session_state[f"s_{u_k}"] = sat_kalkulasi
                                                st.rerun()

                                        c3, c4 = st.columns(2)
                                        ns  = c3.text_input("Unit",        key=f"s_{u_k}")
                                        nh  = c4.number_input("Harga Jual", min_value=0, step=500, key=f"h_{u_k}", format="%d")
                                        c5, c6 = st.columns([2, 1])
                                        np_ = c5.number_input("Pos (urutan)", min_value=0.1, step=0.1, format="%.1f", key=f"p_{u_k}")
                                        td  = c6.checkbox("🗑️ Hapus", key=f"d_{u_k}")
                                        temp_up.append({"del": td, "pos": np_, "Nama": nama_item, "Qty": nq, "Harga": nh, "Sat": ns})

                                st.markdown("---")
                                add_b = st.multiselect(
                                    "➕ Tambah Barang Baru:",
                                    options=df_barang['Nama Barang'].tolist(),
                                    key=f"add_new_{real_row_idx}",
                                    placeholder="Pilih barang untuk ditambahkan..."
                                )

                                if st.button("💾 SIMPAN PERUBAHAN DATA", key=f"btn_save_{real_row_idx}", use_container_width=True):
                                    final = sorted([x for x in temp_up if not x['del']], key=lambda x: x['pos'])
                                    for p in add_b:
                                        rb = df_barang[df_barang['Nama Barang'] == p].iloc[0]
                                        final.append({"Nama": p, "Qty": 1, "Harga": float(rb['Harga']), "Sat": str(rb['Satuan'])})
                                    save_data = [
                                        {
                                            "Nama Barang": x['Nama'],
                                            "Qty": x['Qty'],
                                            "Harga": x['Harga'],
                                            "Satuan": x['Sat'],
                                            "Total_Row": x['Qty'] * x['Harga']
                                        }
                                        for x in final
                                    ]

                                    with st.spinner("Menyimpan ke Google Sheets..."):
                                        ok, msg = save_to_gsheet_verified(sheet, real_row_idx, save_data)

                                    if ok:
                                        st.session_state.saved_items_cache[real_row_idx] = save_data
                                        clear_row_state(real_row_idx)
                                        st.success(f"✅ Tersimpan & terverifikasi! {len(save_data)} barang.")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"⚠️ Simpan gagal: {msg}. Coba lagi.")

                                if real_row_idx in st.session_state.saved_items_cache:
                                    current_items = st.session_state.saved_items_cache[real_row_idx]
                                else:
                                    current_items = read_row_fresh(sheet, real_row_idx)
                                    if not current_items:
                                        current_items = items_list

                                if current_items:
                                    f_df = pd.DataFrame(current_items)
                                    subt = f_df['Total_Row'].sum(); tax = subt * 0.11; gtot = subt + tax

                                    st.markdown("---")
                                    render_section_title("🖨️ Download Quotation")
                                    t1, t2 = st.columns(2)
                                    t1.metric("Sub Total",   f"Rp {subt:,.0f}")
                                    t2.metric("Grand Total", f"Rp {gtot:,.0f}")
                                    st.metric("PPN 11%", f"Rp {tax:,.0f}")
                                    st.markdown("<br>", unsafe_allow_html=True)

                                    no_s = st.text_input("📄 Nomor Surat:", value="/S-TTS/V/2026", key=f"ns_print_{real_row_idx}")

                                    b1, b2 = st.columns(2)
                                    pdf_data = generate_pdf(no_s, customer_val, up_val, f_df, subt, tax, gtot)
                                    b1.download_button(
                                        label="📩 PDF", data=pdf_data,
                                        file_name=f"Quo_{customer_val}.pdf",
                                        key=f"btn_p_{real_row_idx}",
                                        use_container_width=True, type="primary"
                                    )
                                    xls_data = generate_excel(no_s, customer_val, up_val, f_df, subt, tax, gtot)
                                    b2.download_button(
                                        label="📊 Excel", data=xls_data,
                                        file_name=f"{customer_val}.xlsx",
                                        key=f"btn_x_{real_row_idx}",
                                        use_container_width=True
                                    )

                                    st.markdown("<br>", unsafe_allow_html=True)
                                    if st.button("✅ TANDAI SELESAI & HAPUS DARI ANTREAN",
                                                 key=f"done_btn_{real_row_idx}",
                                                 type="primary", use_container_width=True):
                                        sheet.update_cell(real_row_idx, 6, "Processed")
                                        if real_row_idx in st.session_state.saved_items_cache:
                                            del st.session_state.saved_items_cache[real_row_idx]
                                        st.success(f"✅ Penawaran {customer_val} selesai.")
                                        st.rerun()
                    else:
                        st.markdown(f"""<div style="text-align:center; padding:48px 20px; color:#7a9ab8;">
                            <div style="font-size:3rem; margin-bottom:12px;">🎉</div>
                            <div style="font-size:1.1rem; font-weight:700; color:#002855;">Antrean Bersih!</div>
                            <div style="font-size:0.85rem; margin-top:6px;">Semua penawaran sudah diproses, Pak {MARKETING_NAME}.</div>
                        </div>""", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Error Sistem: {e}")
                import traceback
                st.code(traceback.format_exc(), language="python")
