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
    page_icon="📎"
)

# =========================================================
# CUSTOM CSS — FIXED: teks putih + sidebar scope
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Playfair+Display:wght@700&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

.stApp {
    background: linear-gradient(135deg, #f0f4f8 0%, #e8edf5 50%, #f5f0e8 100%);
    min-height: 100vh;
}

/* ── SIDEBAR ── hanya target elemen di dalam sidebar, TIDAK pakai wildcard * */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #002855 0%, #003d7a 40%, #001f42 100%) !important;
    border-right: 3px solid #B8860B;
}

/* Teks umum sidebar (label, caption, p) */
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

/* ── MAIN AREA — semua teks gelap, tidak terkena override sidebar ── */

/* Semua teks paragraf & markdown di main area (bukan sidebar) */
section.main p,
section.main span,
section.main div.stMarkdown,
section.main .stMarkdown p,
section.main .stMarkdown strong,
section.main [data-testid="stMarkdownContainer"] p,
section.main [data-testid="stMarkdownContainer"] strong,
section.main [data-testid="stCaptionContainer"],
section.main small,
section.main .stCaption {
    color: #1e1e1e !important;
}

/* Caption / subtext khusus */
section.main [data-testid="stCaptionContainer"] p,
section.main .stCaption p {
    color: #5a7a9a !important;
}

/* Input fields */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    color: #1e1e1e !important;
    border-radius: 10px !important;
    border: 1.5px solid #c8d6e5 !important;
    background: white !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 10px 14px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #002855 !important;
    box-shadow: 0 0 0 3px rgba(0,40,85,0.1) !important;
}

/* Selectbox main area */
[data-testid="stSelectbox"] > div > div {
    border-radius: 10px !important;
    border: 1.5px solid #c8d6e5 !important;
    background: white !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: #1e1e1e !important;
}
[data-testid="stMultiSelect"] > div > div {
    border-radius: 10px !important;
    border: 1.5px solid #c8d6e5 !important;
    background: white !important;
    color: #1e1e1e !important;
}

/* Teks di dalam selectbox yang terpilih */
[data-testid="stSelectbox"] span,
[data-testid="stMultiSelect"] span {
    color: #1e1e1e !important;
}

/* Dropdown options (listbox) */
[data-baseweb="select"] [data-baseweb="option"],
[data-baseweb="popover"] li,
ul[role="listbox"] li {
    color: #1e1e1e !important;
    background: white !important;
}

/* Label utama di main area */
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

/* Container border teks */
section.main [data-testid="stVerticalBlockBorderWrapper"] p,
section.main [data-testid="stVerticalBlockBorderWrapper"] strong,
section.main [data-testid="stVerticalBlockBorderWrapper"] span,
section.main [data-testid="stVerticalBlockBorderWrapper"] div {
    color: #1e1e1e !important;
}

/* Override khusus: pastikan semua span HTML inline juga gelap di main area */
section.main [data-testid="stMarkdownContainer"] * {
    color: inherit;
}

/* Paksa semua teks di expander content juga gelap */
section.main [data-testid="stExpander"] p,
section.main [data-testid="stExpander"] span,
section.main [data-testid="stExpander"] strong,
section.main [data-testid="stExpander"] li {
    color: #1e1e1e !important;
}

/* ── HEADER ── */
.top-header {
    background: linear-gradient(135deg, #002855 0%, #004080 60%, #002855 100%);
    border-radius: 16px; padding: 28px 36px; margin-bottom: 28px;
    border-bottom: 4px solid #B8860B; display: flex; align-items: center;
    justify-content: space-between;
    box-shadow: 0 8px 32px rgba(0,40,85,0.3); position: relative; overflow: hidden;
}
.top-header::before {
    content: ''; position: absolute; top: -50%; right: -10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(184,134,11,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.top-header-title {
    font-family: 'Playfair Display', serif; font-size: 1.85rem;
    font-weight: 700; color: white; margin: 0; line-height: 1.2;
}
.top-header-subtitle {
    font-size: 0.8rem; color: #B8860B; letter-spacing: 0.12em;
    text-transform: uppercase; font-weight: 600; margin-top: 4px;
}
.top-header-badge {
    background: rgba(184,134,11,0.2); border: 1px solid #B8860B;
    color: #f0c040; padding: 6px 16px; border-radius: 20px;
    font-size: 0.8rem; font-weight: 600; letter-spacing: 0.06em;
}

.section-title {
    font-family: 'Playfair Display', serif; font-size: 1.3rem;
    color: #002855; font-weight: 700; border-left: 4px solid #B8860B;
    padding-left: 12px; margin: 20px 0 14px 0;
}

/* ── BUTTONS ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #002855 0%, #004080 100%) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 700 !important;
    font-size: 0.85rem !important; letter-spacing: 0.08em !important;
    padding: 12px 24px !important; transition: all 0.2s ease !important;
    text-transform: uppercase !important; box-shadow: 0 4px 14px rgba(0,40,85,0.3) !important;
    border-bottom: 3px solid #B8860B !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(0,40,85,0.4) !important;
    background: linear-gradient(135deg, #003366 0%, #0050a0 100%) !important;
}
.stButton > button:not([kind="primary"]) {
    background: white !important; color: #002855 !important;
    border: 1.5px solid #002855 !important; border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important; font-size: 0.82rem !important;
    letter-spacing: 0.04em !important; transition: all 0.2s ease !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: #f0f4f8 !important; border-color: #B8860B !important;
    color: #B8860B !important; transform: translateY(-1px) !important;
}

.stDownloadButton > button {
    border-radius: 10px !important; font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important; font-size: 0.82rem !important;
    letter-spacing: 0.06em !important; text-transform: uppercase !important;
    transition: all 0.2s ease !important;
}

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, #f8fafd 0%, #f0f5fc 100%) !important;
    border-radius: 12px !important; font-weight: 700 !important;
    color: #002855 !important; font-size: 0.92rem !important;
    border: 1.5px solid #dce8f0 !important; padding: 14px 18px !important;
    transition: background 0.2s !important;
}
.streamlit-expanderHeader:hover {
    background: linear-gradient(135deg, #edf3fb 0%, #e4eef8 100%) !important;
    border-color: #B8860B !important;
}

/* ── METRIC ── */
[data-testid="stMetric"] {
    background: white !important; border: 1px solid #e0e8f0 !important;
    border-radius: 14px !important; padding: 16px 20px !important;
    box-shadow: 0 2px 12px rgba(0,40,85,0.07) !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
    border-top: 3px solid #B8860B !important;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0,40,85,0.12) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important; font-weight: 600 !important;
    letter-spacing: 0.08em !important; text-transform: uppercase !important;
    color: #5a7a9a !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 800 !important; color: #002855 !important;
}

hr {
    border: none !important; border-top: 2px solid transparent !important;
    background: linear-gradient(90deg, transparent, #B8860B, transparent) !important;
    height: 2px !important; margin: 20px 0 !important;
}

[data-testid="stToast"] {
    background: #002855 !important; color: white !important;
    border-left: 4px solid #B8860B !important; border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 600 !important;
}

[data-testid="stFileUploader"] {
    border: 2px dashed #c8d6e5 !important; border-radius: 12px !important;
    background: #f8fafd !important; transition: border-color 0.2s !important;
}

.price-info-box {
    background: linear-gradient(135deg, #002855, #004080); color: white;
    border-radius: 12px; padding: 14px 20px; font-weight: 700; font-size: 1rem;
    border-left: 4px solid #B8860B; box-shadow: 0 4px 16px rgba(0,40,85,0.25);
}
.price-info-box span { color: #f0c040; font-size: 1.15rem; }

.feature-card {
    background: white; border-radius: 16px; padding: 24px 20px;
    border: 1px solid #e0e8f0; border-top: 3px solid #B8860B;
    box-shadow: 0 4px 16px rgba(0,40,85,0.08); text-align: center;
    transition: transform 0.25s, box-shadow 0.25s;
}
.feature-card:hover { transform: translateY(-4px); box-shadow: 0 10px 28px rgba(0,40,85,0.16); }
.feature-card .icon { font-size: 2.2rem; margin-bottom: 10px; }
.feature-card h4 { color: #002855; font-weight: 700; font-size: 1rem; margin-bottom: 6px; }
.feature-card p { color: #7a9ab8; font-size: 0.82rem; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)


# ── Helper renderers ──
def render_header(title, subtitle="", right_badge=""):
    right_html = f'<div class="top-header-badge">{right_badge}</div>' if right_badge else ""
    st.markdown(f"""
    <div class="top-header">
        <div>
            <div class="top-header-title">{title}</div>
            <div class="top-header-subtitle">{subtitle if subtitle else SLOGAN}</div>
        </div>
        {right_html}
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
# PDF / EXCEL GENERATORS
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


def item_key(row_idx, nama_barang, suffix=""):
    h = hashlib.md5(nama_barang.encode()).hexdigest()[:8]
    return f"r{row_idx}_{h}_{suffix}" if suffix else f"r{row_idx}_{h}"

def clear_row_state(real_row_idx):
    keys_to_clear = [k for k in list(st.session_state.keys()) if k.startswith(f"r{real_row_idx}_")]
    for k in keys_to_clear:
        del st.session_state[k]


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size:2.4rem;">📎</div>
        <div style="font-family:'Playfair Display',serif; font-size:1.1rem; color:#f0c040; font-weight:700; margin-top:6px;">
            TTS Portal
        </div>
        <div style="font-size:0.72rem; color:#B8860B; letter-spacing:0.1em; text-transform:uppercase; margin-top:2px;">
            {MARKETING_NAME} · Sales Console
        </div>
    </div>
    <hr style="border-top:1px solid rgba(184,134,11,0.3); margin: 10px 0 18px 0;">
    """, unsafe_allow_html=True)

    menu = st.selectbox("Navigasi:", ["🏠 Home", "📝 Admin Sales", "👨‍💻 Sales Dashboard"], label_visibility="collapsed")

    st.markdown("""
    <hr style="border-top:1px solid rgba(184,134,11,0.2); margin: 18px 0 10px 0;">
    <div style="font-size:0.7rem; color:rgba(255,255,255,0.35); text-align:center; padding-bottom:10px;">
        PT. THEA THEO STATIONARY<br>© 2026 All Rights Reserved
    </div>
    """, unsafe_allow_html=True)


if 'cart' not in st.session_state:
    st.session_state.cart = []


# =========================================================
# HOME
# =========================================================
if menu == "🏠 Home":
    render_header(COMPANY_NAME, SLOGAN, f"📍 {ADDR.split(',')[0]}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🧑‍💼 Marketing Aktif", MARKETING_NAME)
    c2.metric("📞 WhatsApp", MARKETING_WA)
    c3.metric("📧 Email", "alattulis.tts")
    c4.metric("🏢 Kantor", OFFICE_PHONE)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class="feature-card"><div class="icon">📝</div><h4>Form Penawaran</h4><p>Buat daftar pesanan dengan mudah, cari barang, atur satuan & harga, lalu kirim langsung ke dashboard sales.</p></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="feature-card"><div class="icon">📄</div><h4>Generate Quotation</h4><p>Unduh quotation profesional format PDF atau Excel siap kirim ke pelanggan dalam hitungan detik.</p></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="feature-card"><div class="icon">📊</div><h4>Sales Dashboard</h4><p>Kelola antrean penawaran, edit item, atur urutan, dan tandai penawaran selesai dari satu tempat.</p></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info(f"💡 Gunakan menu di sidebar kiri untuk mengakses **Form Penawaran** atau **Sales Dashboard**.")


# =========================================================
# ADMIN SALES
# =========================================================
elif menu == "📝 Admin Sales":
    render_header("Form Penawaran", "Buat & kirim penawaran baru", "📋 Admin Sales")

    if "widget_id" not in st.session_state:
        st.session_state.widget_id = 0

    render_section_title("👤 Data Pelanggan")
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        nama_toko = col1.text_input("🏢 Nama Perusahaan / Toko", placeholder="PT. Contoh Maju Bersama")
        up_nama   = col2.text_input("👤 Nama Penerima (UP)",     placeholder="Bapak / Ibu ...")
        wa_nomor  = col3.text_input("📞 Nomor WhatsApp",         placeholder="08xx-xxxx-xxxx")

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
            c1, c2, c3 = st.columns([1.5, 1, 1])
            mode_c = c1.selectbox(f"Pilih Satuan (Default: {satuan_db})", ["Sesuai Database", "Lusin (12)", "Dus", "Box", "Pack", "Set"], key=f"m_c_{st.session_state.widget_id}")
            mult_c = 1; sat_final = satuan_db
            if mode_c == "Lusin (12)": mult_c = 12; sat_final = "Lusin"
            elif mode_c in ["Dus", "Box", "Pack", "Set"]:
                isi_c = c2.number_input(f"Isi per {mode_c}", min_value=1, value=10, key=f"isi_c_{st.session_state.widget_id}")
                mult_c = isi_c; sat_final = mode_c
            qty_c = c3.number_input(f"Jumlah ({sat_final})", min_value=1, value=1, key=f"qty_c_{st.session_state.widget_id}")
            h_jual_c = int(h_master * mult_c)
            st.markdown(f"""
            <div class="price-info-box">
                💰 Harga: <span>Rp {h_jual_c:,.0f}</span> / {sat_final}
                &nbsp;&nbsp;|&nbsp;&nbsp; Qty: <span>{int(qty_c)} {sat_final}</span>
                &nbsp;&nbsp;|&nbsp;&nbsp; Total: <span>Rp {int(qty_c * h_jual_c):,.0f}</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Masukkan ke Keranjang", use_container_width=True, type="primary"):
                st.session_state.cart = [x for x in st.session_state.cart if x['Nama Barang'] != pilihan_barang]
                st.session_state.cart.append({"Nama Barang": pilihan_barang, "Qty": int(qty_c), "Harga": float(h_jual_c), "Satuan": sat_final, "Total_Row": float(qty_c * h_jual_c)})
                st.session_state.widget_id += 1
                st.toast(f"✅ Ditambahkan: {pilihan_barang}"); time.sleep(0.2); st.rerun()
        else:
            st.markdown("""<div style="text-align:center; padding:20px 0; color:#7a9ab8;"><div style="font-size:2rem; margin-bottom:8px;">🔍</div><div style="font-size:0.88rem;">Ketik atau klik dropdown di atas untuk mencari barang</div></div>""", unsafe_allow_html=True)

    if st.session_state.cart:
        render_section_title(f"🛒 Keranjang Pesanan ({len(st.session_state.cart)} item)")
        total_cart = sum(x['Total_Row'] for x in st.session_state.cart)
        tax_cart   = total_cart * 0.11
        grand_cart = total_cart + tax_cart

        m1, m2, m3 = st.columns(3)
        m1.metric("📦 Jumlah Item",  f"{len(st.session_state.cart)} jenis")
        m2.metric("💵 Sub Total",     f"Rp {total_cart:,.0f}")
        m3.metric("🧾 Total + PPN",   f"Rp {grand_cart:,.0f}")
        st.markdown("<br>", unsafe_allow_html=True)

        for i, item in enumerate(st.session_state.cart):
            with st.container(border=True):
                ca, cb, cc, cd = st.columns([3, 2, 1.5, 0.4])
                ca.markdown(f"<span style='color:#002855;font-weight:700;font-size:0.95rem;'>{item['Nama Barang']}</span>", unsafe_allow_html=True)
                ca.markdown(f"<span style='color:#5a7a9a;font-size:0.80rem;'>@ Rp {item['Harga']:,.0f} / {item['Satuan']}</span>", unsafe_allow_html=True)
                cb.markdown(f"<span style='color:#002855;font-weight:600;font-size:0.92rem;'>🔢 {item['Qty']} {item['Satuan']}</span>", unsafe_allow_html=True)
                cc.markdown(f"<span style='color:#002855;font-weight:700;font-size:0.95rem;'>Rp {item['Total_Row']:,.0f}</span>", unsafe_allow_html=True)
                if cd.button("✕", key=f"del_item_{i}", help="Hapus item ini"):
                    st.session_state.cart.pop(i); st.rerun()

        st.divider()
        col_send, col_clear = st.columns([3, 1])
        with col_send:
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
        with col_clear:
            if st.button("🗑️ Kosongkan", use_container_width=True):
                st.session_state.cart = []; st.rerun()


# =========================================================
# SALES DASHBOARD
# =========================================================
elif menu == "👨‍💻 Sales Dashboard":
    render_header("Sales Dashboard", f"Kelola antrean penawaran · {MARKETING_NAME}", "🔐 Admin Only")

    pwd = st.sidebar.text_input("🔑 Password Admin:", type="password", placeholder="Masukkan password...")

    if pwd == ADMIN_PASSWORD:
        st.sidebar.success("✅ Login berhasil")

        with st.sidebar.expander("📁 Update Database (.csv)", expanded=False):
            up_f = st.file_uploader("Pilih file CSV baru:", type=["csv"], key="admin_csv_up")
            if up_f and st.button("🚀 Update Sekarang"):
                with open("database_barang.csv", "wb") as f: f.write(up_f.getbuffer())
                st.cache_data.clear(); st.success("✅ Database diperbarui!"); time.sleep(1); st.rerun()

        sheet = connect_gsheet()
        if sheet:
            try:
                all_vals = sheet.get_all_values()
                if len(all_vals) > 1:
                    # ── FIX: Normalisasi header — strip spasi & BOM ──
                    raw_headers = all_vals[0]
                    clean_headers = [h.strip().lstrip('\ufeff') for h in raw_headers]

                    # Pastikan kolom wajib ada; jika tidak, tambahkan dengan nilai kosong
                    required_cols = ["Waktu", "Customer", "UP", "WA", "Pesanan", "Status", "Sales"]
                    df_gs = pd.DataFrame(all_vals[1:], columns=clean_headers)

                    # Tambah kolom yang mungkin hilang
                    for col in required_cols:
                        if col not in df_gs.columns:
                            df_gs[col] = ""

                    # Strip nilai string di semua kolom kritis
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
                    dm1.metric("📋 Total Antrean",   total_all,     help="Semua penawaran")
                    dm2.metric("⏳ Menunggu Proses",  total_pending, help="Belum diproses")
                    dm3.metric("✅ Selesai Diproses",  total_done,   help="Sudah diproses")
                    st.markdown("<br>", unsafe_allow_html=True)

                    if not pending.empty:
                        render_section_title(f"⏳ Antrean Pending ({total_pending} penawaran)")

                        for idx, row in pending.iterrows():
                            real_row_idx = idx + 2  # +2: 1 for header row, 1 for 1-based index
                            try:
                                items_preview = ast.literal_eval(str(row['Pesanan']))
                                n_items = len(items_preview)
                            except:
                                items_preview = []; n_items = 0

                            waktu_val    = row.get('Waktu', '')
                            customer_val = row.get('Customer', '')
                            up_val       = row.get('UP', '')
                            wa_val       = row.get('WA', '')

                            exp_label = f"🏢 {customer_val}  ·  UP: {up_val}  ·  {n_items} item  ·  📅 {waktu_val}"
                            with st.expander(exp_label, expanded=True):
                                hi1, hi2, hi3 = st.columns(3)
                                hi1.info(f"🏢 **{customer_val}**")
                                hi2.info(f"👤 UP: **{up_val}**")
                                hi3.info(f"📞 WA: **{wa_val}**")
                                st.markdown("---")

                                try:
                                    items_list = ast.literal_eval(str(row['Pesanan']))
                                except:
                                    items_list = []

                                render_section_title("📝 Edit Daftar Barang")
                                st.caption("💡 Ubah angka **Pos** untuk mengatur urutan (2.5 = sisipkan antara no.2 & no.3). Centang 🗑️ untuk hapus.")

                                # ── Pass 1: Inisialisasi session_state HANYA jika belum ada ──
                                # Selalu pakai data dari GSheets (r['Harga'], r['Satuan'], r['Qty'])
                                # TIDAK pernah reset dari database master agar inputan admin sales terjaga
                                for i, r in enumerate(items_list):
                                    nama_item = r['Nama Barang']
                                    u_k       = item_key(real_row_idx, nama_item)

                                    harga_tersimpan  = float(r.get('Harga', 0))
                                    satuan_tersimpan = str(r.get('Satuan', 'Pcs')).strip()

                                    if f"h_{u_k}" not in st.session_state:
                                        st.session_state[f"h_{u_k}"] = int(harga_tersimpan)
                                    if f"s_{u_k}" not in st.session_state:
                                        st.session_state[f"s_{u_k}"] = satuan_tersimpan
                                    if f"q_{u_k}" not in st.session_state:
                                        st.session_state[f"q_{u_k}"] = int(r.get('Qty', 1))
                                    if f"p_{u_k}" not in st.session_state:
                                        st.session_state[f"p_{u_k}"] = float(i + 1)
                                    if f"m_{u_k}" not in st.session_state:
                                        st.session_state[f"m_{u_k}"] = "Pcs/Tetap"
                                    if f"isi_{u_k}" not in st.session_state:
                                        st.session_state[f"isi_{u_k}"] = 10

                                # ── Pass 2: Render widget ──
                                temp_up   = []
                                list_mode = ["Pcs/Tetap", "Lusin (12)", "Dus", "Box", "Pack", "Set", "Rim"]

                                for i, r in enumerate(items_list):
                                    nama_item     = r['Nama Barang']
                                    u_k           = item_key(real_row_idx, nama_item)

                                    # Harga master hanya untuk info referensi
                                    row_master    = df_barang[df_barang['Nama Barang'] == nama_item]
                                    harga_master  = float(row_master['Harga'].values[0]) if not row_master.empty else float(r.get('Harga', 0))
                                    satuan_master = str(row_master['Satuan'].values[0]).strip() if not row_master.empty else str(r.get('Satuan', 'Pcs'))

                                    with st.container(border=True):
                                        c1, c2, c3, c4, c5, c6 = st.columns([2.0, 1.1, 1.2, 1.3, 0.7, 0.4])
                                        c1.markdown(f"<span style='color:#002855;font-weight:700;font-size:0.95rem;'>{nama_item}</span>", unsafe_allow_html=True)
                                        c1.markdown(f"<span style='color:#5a7a9a;font-size:0.78rem;'>📋 Master DB: Rp {harga_master:,.0f} / {satuan_master}</span>", unsafe_allow_html=True)
                                        c1.markdown(f"<span style='color:#B8860B;font-size:0.78rem;font-weight:600;'>💾 Tersimpan: Rp {int(r.get('Harga',0)):,.0f} / {str(r.get('Satuan',''))}</span>", unsafe_allow_html=True)

                                        # Selectbox mode satuan — hanya untuk kalkulasi otomatis harga
                                        mode = c2.selectbox("Kalkulasi Otomatis?", list_mode, key=f"m_{u_k}")
                                        if mode in ["Dus", "Box", "Pack", "Set"]:
                                            c3.number_input(f"Isi per {mode}", min_value=1, step=1, key=f"isi_{u_k}")

                                        # Tombol apply kalkulasi otomatis
                                        if mode != "Pcs/Tetap":
                                            if mode == "Lusin (12)":
                                                harga_kalkulasi = int(harga_master * 12)
                                                sat_kalkulasi   = "Lusin"
                                            elif mode == "Rim":
                                                harga_kalkulasi = int(harga_master)
                                                sat_kalkulasi   = "Rim"
                                            else:
                                                isi_val = st.session_state.get(f"isi_{u_k}", 10)
                                                harga_kalkulasi = int(harga_master * isi_val)
                                                sat_kalkulasi   = mode
                                            if c2.button(f"▶ Apply", key=f"apply_{u_k}", help=f"Set harga ke Rp {harga_kalkulasi:,.0f} / {sat_kalkulasi}"):
                                                st.session_state[f"h_{u_k}"] = harga_kalkulasi
                                                st.session_state[f"s_{u_k}"] = sat_kalkulasi
                                                st.rerun()

                                        nq  = c2.number_input("Qty",        min_value=1, step=1,   key=f"q_{u_k}")
                                        ns  = c3.text_input  ("Unit",                              key=f"s_{u_k}")
                                        nh  = c4.number_input("Harga Jual", min_value=0, step=500, key=f"h_{u_k}", format="%d")
                                        np_ = c5.number_input("Pos", min_value=0.1, step=0.1, format="%.1f", key=f"p_{u_k}",
                                                              help="Ubah untuk mengatur urutan. 2.5 = sisipkan antara no.2 & no.3")
                                        td  = c6.checkbox("🗑️", key=f"d_{u_k}", help="Centang untuk hapus barang ini")
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
                                    save_data = [{"Nama Barang": x['Nama'], "Qty": x['Qty'], "Harga": x['Harga'], "Satuan": x['Sat'], "Total_Row": x['Qty'] * x['Harga']} for x in final]
                                    sheet.update_cell(real_row_idx, 5, str(save_data))
                                    st.cache_data.clear()
                                    clear_row_state(real_row_idx)
                                    st.success(f"✅ Tersimpan! {len(save_data)} barang — urutan sudah dirapikan.")
                                    time.sleep(0.8); st.rerun()

                                # ── Re-fetch untuk PDF/Excel ──
                                try:
                                    current_row_data = sheet.row_values(real_row_idx)
                                    current_items    = ast.literal_eval(current_row_data[4]) if len(current_row_data) > 4 else items_list
                                except:
                                    current_items = items_list

                                if current_items:
                                    f_df = pd.DataFrame(current_items)
                                    subt = f_df['Total_Row'].sum(); tax = subt * 0.11; gtot = subt + tax

                                    st.markdown("---")
                                    render_section_title("🖨️ Generate & Download Quotation")

                                    t1, t2, t3 = st.columns(3)
                                    t1.metric("Sub Total",   f"Rp {subt:,.0f}")
                                    t2.metric("PPN 11%",     f"Rp {tax:,.0f}")
                                    t3.metric("Grand Total", f"Rp {gtot:,.0f}")
                                    st.markdown("<br>", unsafe_allow_html=True)

                                    c_no, _ = st.columns([2, 2])
                                    no_s = c_no.text_input("📄 Nomor Surat:", value="/S-TTS/IV/2026", key=f"ns_print_{real_row_idx}")

                                    b1, b2 = st.columns(2)
                                    pdf_data = generate_pdf(no_s, customer_val, up_val, f_df, subt, tax, gtot)
                                    b1.download_button(label="📩 DOWNLOAD PDF", data=pdf_data, file_name=f"Quo_{customer_val}.pdf", key=f"btn_p_{real_row_idx}", use_container_width=True, type="primary")
                                    xls_data = generate_excel(no_s, customer_val, up_val, f_df, subt, tax, gtot)
                                    b2.download_button(label="📊 DOWNLOAD EXCEL", data=xls_data, file_name=f"{customer_val}.xlsx", key=f"btn_x_{real_row_idx}", use_container_width=True)

                                    st.markdown("<br>", unsafe_allow_html=True)
                                    if st.button("✅ TANDAI PENAWARAN SELESAI & HAPUS DARI ANTREAN", key=f"done_btn_{real_row_idx}", type="primary", use_container_width=True):
                                        sheet.update_cell(real_row_idx, 6, "Processed")
                                        st.success(f"✅ Penawaran {customer_val} selesai diproses.")
                                        st.rerun()
                    else:
                        st.markdown(f"""<div style="text-align:center; padding:48px 20px; color:#7a9ab8;"><div style="font-size:3rem; margin-bottom:12px;">🎉</div><div style="font-size:1.1rem; font-weight:700; color:#002855;">Antrean Bersih!</div><div style="font-size:0.85rem; margin-top:6px;">Semua penawaran sudah diproses, Pak {MARKETING_NAME}.</div></div>""", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Error Sistem: {e}")
                import traceback
                st.code(traceback.format_exc(), language="python")

    elif pwd != "":
        st.sidebar.error("❌ Password salah. Coba lagi.")
        st.warning("🔐 Masukkan password admin yang benar di sidebar kiri untuk mengakses dashboard.")
    else:
        st.markdown("""<div style="text-align:center; padding:60px 20px; color:#7a9ab8;"><div style="font-size:3.5rem; margin-bottom:16px;">🔐</div><div style="font-size:1.2rem; font-weight:700; color:#002855; margin-bottom:8px;">Area Admin</div><div style="font-size:0.88rem;">Masukkan password di sidebar kiri untuk melanjutkan.</div></div>""", unsafe_allow_html=True)
