import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta
from fpdf import FPDF
import os
import gspread
from google.oauth2.service_account import Credentials
import io

# =========================================================
# 1. KONFIGURASI UTAMA
# =========================================================
MARKETING_NAME  = "Asin"
MARKETING_WA    = "08158199775"
MARKETING_EMAIL = "alattulis.tts@gmail.com"

COMPANY_NAME    = "PT. THEA THEO STATIONARY"
SLOGAN          = "Supplier Alat Tulis Kantor & Sekolah"
ADDR            = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
OFFICE_PHONE    = "(021) 55780659"

ADMIN_PASSWORD  = st.secrets["ADMIN_PASSWORD"]

st.set_page_config(page_title=f"{COMPANY_NAME}", layout="wide")

# =========================================================
# 2. KONEKSI DATA
# =========================================================
def get_creds():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)

def connect_gsheet():
    try:
        client = gspread.authorize(get_creds())
        return client.open("Antrean Penawaran TTS").sheet1
    except: return None

def load_db():
    if os.path.exists("database_barang.xlsx"):
        try:
            df = pd.read_excel("database_barang.xlsx")
            df.columns = df.columns.str.strip()
            df['Harga'] = pd.to_numeric(df['Harga'], errors='coerce').fillna(0)
            return df
        except: pass
    return pd.DataFrame(columns=['Nama Barang', 'Harga', 'Satuan'])

df_barang = load_db()

# =========================================================
# 3. PDF ENGINE (PROFESSIONAL NAVY)
# =========================================================
class PenawaranPDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"): self.image("logo.png", 10, 10, 30)
        self.set_x(45); self.set_font('Arial', 'B', 16); self.set_text_color(0, 51, 102); self.cell(0, 8, COMPANY_NAME, ln=1)
        self.set_x(45); self.set_font('Arial', '', 9); self.set_text_color(100, 100, 100); self.cell(0, 5, SLOGAN, ln=1)
        self.set_x(45); self.cell(0, 5, f"{ADDR} | Telp: {OFFICE_PHONE}", ln=1)
        self.set_y(12); self.set_font('Arial', '', 8); self.set_text_color(0, 0, 0); self.cell(0, 4, f"WA: {MARKETING_WA}", ln=1, align='R'); self.cell(0, 4, f"Email: {MARKETING_EMAIL}", ln=1, align='R')
        self.set_draw_color(0, 51, 102); self.set_line_width(0.8); self.line(10, 40, 200, 40); self.ln(22)

def generate_pdf(no_s, cust, pic, df_f, subt, tax, gtot):
    pdf = PenawaranPDF()
    pdf.add_page(); pdf.set_font('Arial', 'B', 12); pdf.cell(0, 7, "SURAT PENAWARAN HARGA", ln=1, align='C'); pdf.ln(5)
    tgl = (datetime.utcnow() + timedelta(hours=7)).strftime('%d %B %Y')
    pdf.set_font('Arial', '', 10); pdf.cell(95, 6, f"No: {no_s}", 0); pdf.cell(95, 6, f"Tanggal: {tgl}", 0, 1, 'R'); pdf.ln(5)
    pdf.set_font('Arial', 'B', 10); pdf.cell(0, 6, "Kepada Yth,", ln=1); pdf.set_font('Arial', 'B', 11); pdf.cell(0, 6, str(cust).upper(), ln=1); pdf.set_font('Arial', '', 10); pdf.cell(0, 6, f"Up. {pic}", ln=1); pdf.ln(8)
    pdf.set_fill_color(0, 51, 102); pdf.set_text_color(255, 255, 255)
    pdf.cell(10, 10, 'NO', 1, 0, 'C', True); pdf.cell(85, 10, 'NAMA BARANG', 1, 0, 'C', True); pdf.cell(20, 10, 'QTY', 1, 0, 'C', True); pdf.cell(20, 10, 'SAT', 1, 0, 'C', True); pdf.cell(25, 10, 'HARGA', 1, 0, 'C', True); pdf.cell(30, 10, 'TOTAL', 1, 1, 'C', True)
    pdf.set_font('Arial', '', 9); pdf.set_text_color(0, 0, 0); fill = False
    for i, row in df_f.iterrows():
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(10, 8, str(i+1), 1, 0, 'C', True); pdf.cell(85, 8, f" {row['Nama Barang']}", 1, 0, 'L', True); pdf.cell(20, 8, str(int(row['Qty'])), 1, 0, 'C', True); pdf.cell(20, 8, str(row['Satuan']), 1, 0, 'C', True); pdf.cell(25, 8, f"{row['Harga']:,.0f} ", 1, 0, 'R', True); pdf.cell(30, 8, f"{row['Total_Row']:,.0f} ", 1, 1, 'R', True); fill = not fill
    pdf.ln(2); pdf.set_font('Arial', 'B', 10)
    pdf.cell(160, 8, "Sub Total", 0, 0, 'R'); pdf.cell(30, 8, f" {subt:,.0f}", 1, 1, 'R')
    pdf.cell(160, 8, "PPN 11%", 0, 0, 'R'); pdf.cell(30, 8, f" {tax:,.0f}", 1, 1, 'R')
    pdf.set_fill_color(0, 51, 102); pdf.set_text_color(255, 255, 255); pdf.cell(160, 10, "GRAND TOTAL  ", 0, 0, 'R'); pdf.cell(30, 10, f" {gtot:,.0f}", 1, 1, 'R', True)
    pdf.ln(10); pdf.set_font('Arial', 'I', 8); pdf.set_text_color(100, 100, 100); pdf.multi_cell(0, 4, "* Dokumen otomatis sistem TTS. Sah tanpa tanda tangan basah."); pdf.ln(10); pdf.set_font('Arial', 'B', 11); pdf.set_text_color(0, 0, 0); pdf.cell(0, 6, "Hormat Kami,", ln=1); pdf.ln(15); pdf.cell(0, 6, MARKETING_NAME, ln=1); pdf.set_font('Arial', '', 10); pdf.cell(0, 5, "Sales Consultant", ln=1)
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# 4. MENU APLIKASI
# =========================================================
st.sidebar.title("NAVIGASI")
menu = st.sidebar.selectbox("Pilih Menu:", ["🏠 Home", "🛒 1. Input Staff", "🔐 2. Pak Asin (Edit Harga & Barang)", "📄 3. Cetak Staff"])
sheet = connect_gsheet()

if menu == "🏠 Home":
    st.title(f"Portal Penawaran {COMPANY_NAME}")
    st.info(f"Pilih menu di samping untuk mulai bekerja.")

elif menu == "🛒 1. Input Staff":
    st.header("Admin: Masukkan Pesanan Baru")
    if 'cart' not in st.session_state: st.session_state.cart = []
    with st.container(border=True):
        c1, c2 = st.columns(2)
        nama_t = c1.text_input("Nama Toko/Customer")
        up = c2.text_input("UP (Nama Penerima)")
        wa = c1.text_input("Nomor WA")
        barang = st.multiselect("Pilih Barang Awal:", options=df_barang['Nama Barang'].tolist())
        if st.button("Tambah ke List"):
            for b in barang:
                if b not in st.session_state.cart: st.session_state.cart.append(b)
            st.rerun()

    if st.session_state.cart:
        list_p = []
        for item in st.session_state.cart:
            rb = df_barang[df_barang['Nama Barang'] == item].iloc[0]
            with st.container(border=True):
                ca, cb, cc = st.columns([3, 1, 0.5])
                ca.write(f"**{item}**")
                qty = cb.number_input("Qty", min_value=1, value=1, key=f"in_{item}")
                if cc.button("❌", key=f"del_{item}"): st.session_state.cart.remove(item); st.rerun()
                list_p.append({"Nama Barang": item, "Qty": qty, "Harga": rb['Harga'], "Satuan": rb['Satuan'], "Total_Row": qty * rb['Harga']})
        
        if st.button("🚀 Kirim ke Pak Asin", use_container_width=True):
            if sheet and nama_t:
                wkt = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")
                sheet.append_row([wkt, nama_t, up, wa, str(list_p), "Pending",
