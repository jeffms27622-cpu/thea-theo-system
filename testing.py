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
    initial_sidebar_state="collapsed"  # ← Sidebar collapsed by default on mobile
)

# =========================================================
# MOBILE-FIRST CSS
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700&display=swap');

/* ── RESET & BASE ── */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    -webkit-tap-highlight-color: transparent;
    -webkit-text-size-adjust: 100%;
}
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

/* ── APP BACKGROUND ── */
.stApp {
    background: linear-gradient(135deg, #f0f4f8 0%, #e8edf5 50%, #f5f0e8 100%);
    min-height: 100vh;
}

/* ── MOBILE: Hilangkan padding berlebih di main container ── */
.block-container {
    padding: 0.5rem 0.75rem 2rem 0.75rem !important;
    max-width: 100% !important;
}

/* Desktop: padding lebih lega */
@media (min-width: 768px) {
    .block-container {
        padding: 1rem 2rem 2rem 2rem !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
    }
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #002855 0%, #003d7a 40%, #001f42 100%) !important;
    border-right: 3px solid #B8860B;
    min-width: 260px !important;
    max-width: 80vw !important;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not([data-baseweb]),
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div.stMarkdown,
[data-testid="stSidebar"] .stCaption {
    color: #e8edf5 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #f0c040 !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 1.1rem !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label {
    color: #B8860B !important;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-size: 0.75rem;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(184,134,11,0.4) !important;
    color: white !important;
    border-radius: 8px;
}
[data-testid="stSidebar"] .stExpander {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(184,134,11,0.3) !important;
    border-radius: 10px;
}

/* ── HEADER ── */
.top-header {
    background: linear-gradient(135deg, #002855 0%, #004080 60%, #002855 100%);
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 16px;
    border-bottom: 4px solid #B8860B;
    box-shadow: 0 8px 32px rgba(0,40,85,0.3);
    position: relative;
    overflow: hidden;
}
.top-header::before {
    content: '';
    position: absolute;
    top: -50%; right: -10%;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(184,134,11,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.top-header-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: white;
    margin: 0;
    line-height: 1.2;
}
.top-header-subtitle {
    font-size: 0.7rem;
    color: #B8860B;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 600;
    margin-top: 3px;
}
.top-header-badge {
    display: inline-block;
    background: rgba(184,134,11,0.2);
    border: 1px solid #B8860B;
    color: #f0c040;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    margin-top: 8px;
}

/* Desktop header: lebih besar */
@media (min-width: 768px) {
    .top-header {
        padding: 28px 36px;
        border-radius: 16px;
        margin-bottom: 28px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .top-header-title { font-size: 1.85rem; }
    .top-header-subtitle { font-size: 0.8rem; }
    .top-header-badge {
        display: block;
        margin-top: 0;
        padding: 6px 16px;
        font-size: 0.8rem;
    }
}

/* ── SECTION TITLE ── */
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    color: #002855;
    font-weight: 700;
    border-left: 4px solid #B8860B;
    padding-left: 10px;
    margin: 16px 0 12px 0;
}
@media (min-width: 768px) {
    .section-title { font-size: 1.3rem; margin: 20px 0 14px 0; }
}

/* ── INPUTS — ukuran touch-friendly ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    color: #1e1e1e !important;
    border-radius: 10px !important;
    border: 1.5px solid #c8d6e5 !important;
    background: white !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 1rem !important;          /* ← lebih besar di mobile */
    padding: 12px 14px !important;       /* ← lebih tinggi supaya mudah tap */
    transition: border-color 0.2s, box-shadow 0.2s !important;
    min-height: 48px !important;         /* ← touch target minimum */
    -webkit-appearance: none;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #002855 !important;
    box-shadow: 0 0 0 3px rgba(0,40,85,0.1) !important;
    outline: none !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    border-radius: 10px !important;
    border: 1.5px solid #c8d6e5 !important;
    background: white !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: #1e1e1e !important;
    min-height: 48px !important;
}
[data-testid="stMultiSelect"] > div > div {
    border-radius: 10px !important;
    border: 1.5px solid #c8d6e5 !important;
    background: white !important;
    color: #1e1e1e !important;
    min-height: 48px !important;
}
[data-testid="stSelectbox"] span,
[data-testid="stMultiSelect"] span { color: #1e1e1e !important; }

/* Dropdown option */
[data-baseweb="select"] [data-baseweb="option"],
[data-baseweb="popover"] li,
ul[role="listbox"] li {
    color: #1e1e1e !important;
    background: white !important;
    padding: 12px 16px !important;      /* ← touch-friendly */
    font-size: 0.95rem !important;
}

/* Label */
section.main .stTextInput label,
section.main .stSelectbox label,
section.main .stNumberInput label,
section.main .stMultiSelect label,
section.main .stCheckbox label {
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: #002855 !important;
}

/* ── BUTTONS — touch-friendly minimum 48px ── */
.stButton > button {
    min-height: 48px !important;
    font-size: 0.88rem !important;
    padding: 12px 20px !important;
    border-radius: 10px !important;
    width: 100% !important;             /* ← full width di mobile */
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
    -webkit-tap-highlight-color: transparent;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #002855 0%, #004080 100%) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(0,40,85,0.3) !important;
    border-bottom: 3px solid #B8860B !important;
}
.stButton > button[kind="primary"]:active {
    transform: scale(0.97) !important;
    box-shadow: 0 2px 8px rgba(0,40,85,0.3) !important;
}
.stButton > button:not([kind="primary"]) {
    background: white !important;
    color: #002855 !important;
    border: 1.5px solid #002855 !important;
}
.stButton > button:not([kind="primary"]):active {
    background: #f0f4f8 !important;
    border-color: #B8860B !important;
    color: #B8860B !important;
}

/* Desktop: tombol tidak harus full width */
@media (min-width: 768px) {
    .stButton > button { width: auto !important; }
    .stButton > button:hover:not([kind="primary"]) {
        background: #f0f4f8 !important;
        border-color: #B8860B !important;
        color: #B8860B !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(0,40,85,0.4) !important;
        background: linear-gradient(135deg, #003366 0%, #0050a0 100%) !important;
    }
}

/* Download button */
.stDownloadButton > button {
    min-height: 48px !important;
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}
@media (min-width: 768px) {
    .stDownloadButton > button { width: auto !important; }
}

/* ── METRIC CARDS ── */
[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #e0e8f0 !important;
    border-radius: 14px !important;
    padding: 14px 16px !important;
    box-shadow: 0 2px 12px rgba(0,40,85,0.07) !important;
    border-top: 3px solid #B8860B !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #5a7a9a !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 800 !important;
    color: #002855 !important;
    font-size: 1.3rem !important;       /* ← lebih kecil di mobile supaya muat */
}
@media (min-width: 768px) {
    [data-testid="stMetricValue"] { font-size: 1.75rem !important; }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,40,85,0.12) !important;
    }
}

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, #f8fafd 0%, #f0f5fc 100%) !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    color: #002855 !important;
    font-size: 0.9rem !important;
    border: 1.5px solid #dce8f0 !important;
    padding: 14px 16px !important;
    transition: background 0.2s !important;
    min-height: 48px !important;
}
.streamlit-expanderHeader:hover {
    background: linear-gradient(135deg, #edf3fb 0%, #e4eef8 100%) !important;
    border-color: #B8860B !important;
}

/* ── TEKS MAIN AREA ── */
section.main p,
section.main span,
section.main div.stMarkdown,
section.main .stMarkdown p,
section.main .stMarkdown strong,
section.main [data-testid="stMarkdownContainer"] p,
section.main [data-testid="stMarkdownContainer"] strong,
section.main [data-testid="stCaptionContainer"],
section.main small,
section.main .stCaption { color: #1e1e1e !important; }

section.main [data-testid="stCaptionContainer"] p,
section.main .stCaption p { color: #5a7a9a !important; }

section.main [data-testid="stVerticalBlockBorderWrapper"] p,
section.main [data-testid="stVerticalBlockBorderWrapper"] strong,
section.main [data-testid="stVerticalBlockBorderWrapper"] span,
section.main [data-testid="stVerticalBlockBorderWrapper"] div { color: #1e1e1e !important; }

section.main [data-testid="stMarkdownContainer"] * { color: inherit; }

section.main [data-testid="stExpander"] p,
section.main [data-testid="stExpander"] span,
section.main [data-testid="stExpander"] strong,
section.main [data-testid="stExpander"] li { color: #1e1e1e !important; }

/* ── DIVIDER ── */
hr {
    border: none !important;
    border-top: 2px solid transparent !important;
    background: linear-gradient(90deg, transparent, #B8860B, transparent) !important;
    height: 2px !important;
    margin: 16px 0 !important;
}

/* ── TOAST ── */
[data-testid="stToast"] {
    background: #002855 !important;
    color: white !important;
    border-left: 4px solid #B8860B !important;
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #c8d6e5 !important;
    border-radius: 12px !important;
    background: #f8fafd !important;
    transition: border-color 0.2s !important;
    padding: 16px !important;
}

/* ── PRICE BOX ── */
.price-info-box {
    background: linear-gradient(135deg, #002855, #004080);
    color: white;
    border-radius: 12px;
    padding: 14px 18px;
    font-weight: 700;
    font-size: 0.95rem;
    border-left: 4px solid #B8860B;
    box-shadow: 0 4px 16px rgba(0,40,85,0.25);
    margin: 8px 0;
}
.price-info-box span { color: #f0c040; font-size: 1.1rem; }

/* ── FEATURE CARDS ── */
.feature-card {
    background: white;
    border-radius: 14px;
    padding: 18px 14px;
    border: 1px solid #e0e8f0;
    border-top: 3px solid #B8860B;
    box-shadow: 0 4px 16px rgba(0,40,85,0.08);
    text-align: center;
    transition: transform 0.25s, box-shadow 0.25s;
    margin-bottom: 12px;
}
.feature-card .icon { font-size: 2rem; margin-bottom: 8px; }
.feature-card h4 { color: #002855; font-weight: 700; font-size: 0.95rem; margin-bottom: 4px; }
.feature-card p { color: #7a9ab8; font-size: 0.78rem; line-height: 1.5; margin: 0; }

@media (min-width: 768px) {
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 28px rgba(0,40,85,0.16);
    }
    .feature-card { padding: 24px 20px; }
}

/* ── DATAFRAME / TABLE ── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
    font-size: 0.82rem !important;
}

/* ── KOLOM: stack di mobile, side by side di desktop ── */
/* Streamlit columns secara otomatis stack di layar sempit,
   tapi kita bisa kurangi gap-nya di mobile */
[data-testid="column"] {
    padding: 0 4px !important;
}
@media (min-width: 768px) {
    [data-testid="column"] { padding: 0 8px !important; }
}

/* ── NUMBER INPUT — tombol +/- lebih besar ── */
.stNumberInput button {
    min-width: 40px !important;
    min-height: 40px !important;
}

/* ── CHECKBOX ── */
.stCheckbox > label {
    min-height: 40px !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    cursor: pointer !important;
}
.stCheckbox > label > div:first-child {
    width: 20px !important;
    height: 20px !important;
    min-width: 20px !important;
}

/* ── SCROLLBAR halus di mobile ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,40,85,0.2); border-radius: 4px; }

/* ── BOTTOM SAFE AREA (iPhone notch) ── */
@supports (padding-bottom: env(safe-area-inset-bottom)) {
    .stApp {
        padding-bottom: env(safe-area-inset-bottom);
    }
}

/* ── ALERT / INFO BOX ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.88rem !important;
    padding: 12px 16px !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helper renderers ──
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

@st.cache_data(ttl=600)
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


# =========================================================
# PDF GENERATOR (tidak berubah dari versi asli)
# =========================================================
class PenawaranPDF(FPDF):
    def header(self):
        self.set_fill_color(*COLOR_NAVY); self.rect(0, 0, 210, 55, 'F')
        self.set_fill_color(255, 255, 255); self.rect(10, 0, 50, 55, 'F')
        self.set_fill_color(*COLOR_GOLD); self.rect(60, 0, 2, 55, 'F'); self.rect(64, 0, 0.5, 55, 'F')
        if os.path.exists("logo.png"): self.image("logo.png", 15, 12, 40)
        self.set_y(12); self.set_x(72)
        self.set_font('Arial', 'B', 20); self.set_text_color(255, 255, 255); self.cell(0, 8, COMPANY_NAME, ln=1)
        self.set_x(72); self.set_font('Arial', 'B', 10); self.set_text_color(184, 134, 11); self.cell(0, 6, "  ".join(SLOGAN.upper()), ln=1)
        self.set_fill_color(255, 255, 255); self.rect(72, 28, 120, 0.2, 'F')
        self.set_y(32); self.set_x(72)
        self.set_font('Arial', '', 8); self.set_text_color(220, 220, 220); self.cell(0, 4, ADDR, ln=1)
        self.set_x(72); self.cell(0, 4, f"Office: {OFFICE_PHONE}  |  WA: {MARKETING_WA}", ln=1)
        self.set_x(72); self.cell(0, 4, f"Email: {MARKETING_EMAIL}", ln=1)
        self.set_y(65)

    def footer(self):
        self.set_y(-25); self.set_fill_color(*COLOR_NAVY); self.rect(0, 272, 210, 25, 'F')
        self.set_fill_color(*COLOR_GOLD); self.rect(0, 292, 210, 5, 'F')
        self.set_y(-18); self.set_font('Arial', 'B', 9); self.set_text_color(255, 255, 255)
        self.cell(0, 5, "THANK YOU FOR YOUR BUSINESS", 0, 1, 'C')
        self.set_font('Arial', '', 7); self.set_text_color(184, 134, 11)
        self.cell(0, 4, f"Page {self.page_no()} | Generated by TTS System", 0, 0, 'C')

def draw_table_header(pdf):
    pdf.set_font('Arial', 'B', 9); pdf.set_text_color(255, 255, 255); pdf.set_fill_color(*COLOR_NAVY)
    pdf.cell(10, 10, 'NO', 0, 0, 'C', True); pdf.cell(90, 10, 'DESCRIPTION', 0, 0, 'L', True)
    pdf.cell(20, 10, 'QTY', 0, 0, 'C', True); pdf.cell(20, 10, 'UNIT', 0, 0, 'C', True)
    pdf.cell(25, 10, 'PRICE', 0, 0, 'R', True); pdf.cell(25, 10, 'TOTAL', 0, 1, 'R', True)

def generate_pdf(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    pdf = PenawaranPDF(); pdf.set_margins(10, 70, 10); pdf.set_auto_page_break(auto=True, margin=30); pdf.add_page()
    pdf.set_y(70); pdf.set_font('Arial', 'B', 24); pdf.set_text_color(*COLOR_NAVY); pdf.cell(0, 10, "QUOTATION", ln=1, align='R')
    pdf.set_font('Arial', '', 9); pdf.set_text_color(120, 120, 120); pdf.cell(0, 5, f"Reference: {no_surat}", ln=1, align='R')
    waktu_skrg = datetime.utcnow() + timedelta(hours=7)
    pdf.cell(0, 5, f"Date: {waktu_skrg.strftime('%d %B %Y')}", ln=1, align='R')
    pdf.set_y(70); pdf.set_font('Arial', 'B', 9); pdf.set_text_color(*COLOR_GOLD); pdf.cell(0, 5, "PREPARED FOR:", ln=1)
    pdf.set_font('Arial', 'B', 13); pdf.set_text_color(*COLOR_TEXT); pdf.cell(0, 7, str(nama_cust).upper(), ln=1)
    pdf.set_font('Arial', '', 10); pdf.cell(0, 5, f"Attention: {pic}", ln=1); pdf.ln(10)
    draw_table_header(pdf)
    pdf.set_font('Arial', '', 9); pdf.set_text_color(*COLOR_TEXT)
    fill = False
    for i, row in df_order.iterrows():
        if pdf.get_y() > 240:
            pdf.add_page(); draw_table_header(pdf); pdf.set_font('Arial', '', 9); pdf.set_text_color(*COLOR_TEXT)
        pdf.set_fill_color(248, 249, 252) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(10, 8, str(i+1), 0, 0, 'C', True); pdf.cell(90, 8, f" {row['Nama Barang']}", 0, 0, 'L', True)
        pdf.cell(20, 8, str(int(row['Qty'])), 0, 0, 'C', True); pdf.cell(20, 8, str(row['Satuan']), 0, 0, 'C', True)
        pdf.cell(25, 8, f"{row['Harga']:,.0f} ", 0, 0, 'R', True); pdf.cell(25, 8, f"{row['Total_Row']:,.0f} ", 0, 1, 'R', True)
        pdf.set_draw_color(184, 134, 11); pdf.set_line_width(0.1); pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        fill = not fill
    if pdf.get_y() > 220: pdf.add_page()
    pdf.ln(5); pdf.set_x(130); pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 8, "Sub Total", 0, 0, 'L'); pdf.cell(25, 8, f" {subtotal:,.0f}", 0, 1, 'R')
    pdf.set_x(130); pdf.cell(45, 8, "VAT (PPN 11%)", 0, 0, 'L'); pdf.cell(25, 8, f" {ppn:,.0f}", 0, 1, 'R')
    pdf.set_x(130); pdf.set_fill_color(*COLOR_NAVY); pdf.set_text_color(255, 255, 255)
    pdf.cell(70, 10, f" TOTAL IDR {grand_total:,.0f} ", 0, 1, 'R', True)
    pdf.ln(10); pdf.set_font('Arial', 'B', 9); pdf.set_text_color(*COLOR_NAVY); pdf.cell(0, 5, "TERMS & CONDITIONS:", ln=1)
    pdf.set_font('Arial', '', 8); pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, "Notes & Payment Terms:\n1. Prices are subject to change without notice.\n2. Validity: 7 Days from date of quotation.\n3. Delivery: Within 1 working day after PO confirmation.\n4. Payments must be transferred ONLY to the following account:\n   Bank Name     : Bank Mandiri\n   Account No.   : 1550010174996\n   Account Name  : PT THEA THEO STATIONARY")
    pdf.ln(10); pdf.set_font('Arial', '', 10); pdf.set_text_color(*COLOR_TEXT)
    pdf.cell(130, 5, "", 0, 0); pdf.cell(60, 5, "Yours Faithfully,", 0, 1, 'C')
    pdf.ln(15)
    pdf.set_font('Arial', 'B', 10); pdf.set_text_color(*COLOR_NAVY)
    pdf.cell(130, 5, "", 0, 0); pdf.cell(60, 5, MARKETING_NAME.upper(), 0, 1, 'C')
    pdf.set_font('Arial', '', 9); pdf.set_text_color(100, 100, 100)
    pdf.cell(130, 5, "", 0, 0); pdf.cell(60, 5, "Sales Consultant", 0, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# CATATAN PENGGUNAAN (untuk referensi kolom di halaman app)
# =========================================================
# Untuk layout yang mobile-friendly, gunakan pola ini di halaman-halaman kamu:
#
# JANGAN:
#   col1, col2, col3 = st.columns(3)  ← terlalu sempit di HP
#
# LAKUKAN:
#   col1, col2 = st.columns([1,1])    ← maks 2 kolom untuk form
#   # atau
#   col1, col2 = st.columns([2,1])    ← konten + aksi
#
# Untuk TABEL RINGKASAN (3+ kolom), pakai st.columns([1,1,1]) tapi
# pastikan kontennya pendek (angka/label singkat).
#
# Gunakan st.expander() untuk menyembunyikan section panjang di mobile.
# =========================================================
