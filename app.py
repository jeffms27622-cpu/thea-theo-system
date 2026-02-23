import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta
from fpdf import FPDF
import os
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import re

# =========================================================
# 1. KONFIGURASI & DATA KANTOR
# =========================================================
MARKETING_NAME  = "Asin"
COMPANY_NAME    = "PT. THEA THEO STATIONARY"
SLOGAN          = "Professional Office & School Supplies Partner"
ADDR            = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
OFFICE_PHONE    = "(021) 55780659"
WA_MARKETING    = "08158199775"
EMAIL_MARKETING = "alattulis.tts@gmail.com"
PAJAK_FOLDER_ID = "19i_mLcu4VtV85NLwZY67zZTGwxBgdG1z"
ADMIN_PASSWORD  = st.secrets["ADMIN_PASSWORD"]

# --- DEFINISI WARNA MEWAH (GOLD & NAVY) ---
CP_NAVY = (0, 40, 85)     # Deep Navy
CP_GOLD = (184, 134, 11)  # Dark Goldenrod (Emas Mewah)
CP_SOFT = (245, 247, 250) # Soft Gray Background

st.set_page_config(page_title=f"TTS - {MARKETING_NAME}", layout="wide")

# =========================================================
# 2. KONEKSI GOOGLE
# =========================================================
def get_creds():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)

def connect_gsheet():
    try:
        client = gspread.authorize(get_creds())
        return client.open("Antrean Penawaran TTS").sheet1
    except: return None

def search_pajak_file(inv_keyword, name_keyword):
    try:
        service = build('drive', 'v3', credentials=get_creds())
        query = f"'{PAJAK_FOLDER_ID}' in parents and mimeType = 'application/pdf' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)", pageSize=1000).execute()
        files = results.get('files', [])
        c_inv = re.sub(r'[^A-Z0-9]', '', inv_keyword.upper()) if inv_keyword else ""
        c_nam = re.sub(r'[^A-Z0-9]', '', name_keyword.upper()) if name_keyword else ""
        for f in files:
            fn = re.sub(r'[^A-Z0-9]', '', f['name'].upper())
            if (c_inv or c_nam) and (c_inv in fn) and (c_nam in fn): return f
        return None
    except: return None

def download_drive_file(fid):
    service = build('drive', 'v3', credentials=get_creds())
    req = service.files().get_media(fileId=fid)
    fh = io.BytesIO(); downloader = MediaIoBaseDownload(fh, req)
    done = False
    while not done: _, done = downloader.next_chunk()
    return fh.getvalue()

def load_db():
    if os.path.exists("database_barang.xlsx"):
        try:
            df = pd.read_excel("database_barang.xlsx")
            df.columns = df.columns.str.strip()
            df['Harga'] = pd.to_numeric(df['Harga'], errors='coerce').fillna(0)
            return df
        except: pass
    return pd.DataFrame(columns=['Nama Barang', 'Harga', 'Satuan'])

# =========================================================
# 3. MESIN PDF (PREMIUM MULTINATIONAL STYLE)
# =========================================================
class PremiumPDF(FPDF):
    def header(self):
        # Header Banner Navy & Gold
        self.set_fill_color(*CP_NAVY); self.rect(0, 0, 210, 35, 'F')
        self.set_fill_color(*CP_GOLD); self.rect(0, 34, 210, 1, 'F')
        
        if os.path.exists("logo.png"): self.image("logo.png", 12, 8, 25)
        
        self.set_y(8); self.set_x(42)
        self.set_font('Arial', 'B', 16); self.set_text_color(255, 255, 255)
        self.cell(0, 8, COMPANY_NAME, ln=1)
        self.set_x(42); self.set_font('Arial', 'I', 8); self.set_text_color(200, 200, 200)
        self.cell(0, 5, SLOGAN, ln=1)
        self.set_x(42); self.set_font('Arial', '', 8); self.set_text_color(255, 255, 255)
        self.cell(0, 4, f"{ADDR} | Telp: {OFFICE_PHONE}", ln=1)
        self.ln(20)

    def footer(self):
        self.set_y(-25); self.set_font('Arial', 'I', 7); self.set_text_color(150, 150, 150)
        self.line(10, 275, 200, 275)
        self.cell(0, 10, f"Proprietary & Confidential - {COMPANY_NAME}", 0, 0, 'L')
        self.cell(0, 10, f"Halaman {self.page_no()}", 0, 0, 'R')

def generate_pdf(no_s, cust, pic, df_f, subt, tax, gtot):
    pdf = PremiumPDF()
    pdf.add_page(); pdf.set_y(45)
    
    # Judul & Info Customer
    pdf.set_font('Arial', 'B', 20); pdf.set_text_color(*CP_NAVY); pdf.cell(0, 10, "QUOTATION", ln=1, align='R')
    pdf.set_font('Arial', '', 9); pdf.set_text_color(120, 120, 120); pdf.cell(0, 5, f"No: {no_s}", ln=1, align='R')
    
    pdf.set_xy(10, 45); pdf.set_fill_color(*CP_SOFT); pdf.rect(10, 45, 90, 25, 'F')
    pdf.set_xy(13, 48); pdf.set_font('Arial', 'B', 8); pdf.set_text_color(100, 100, 100); pdf.cell(0, 4, "CLIENT:", ln=1)
    pdf.set_x(13); pdf.set_font('Arial', 'B', 11); pdf.set_text_color(0, 0, 0); pdf.cell(0, 6, str(cust).upper(), ln=1)
    pdf.set_x(13); pdf.set_font('Arial', '', 9); pdf.cell(0, 5, f"UP: {pic}", ln=1)
    
    pdf.ln(15)
    # Header Tabel
    pdf.set_fill_color(*CP_NAVY); pdf.set_text_color(255, 255, 255); pdf.set_font('Arial', 'B', 9)
    pdf.cell(10, 10, 'NO', 0, 0, 'C', 1); pdf.cell(90, 10, 'DESCRIPTION', 0, 0, 'L', 1)
    pdf.cell(20, 10, 'QTY', 0, 0, 'C', 1); pdf.cell(20, 10, 'UNIT', 0, 0, 'C', 1)
    pdf.cell(25, 10, 'PRICE', 0, 0, 'R', 1); pdf.cell(25, 10, 'AMOUNT', 0, 1, 'R', 1)
    
    pdf.set_font('Arial', '', 9); pdf.set_text_color(0, 0, 0); fill = False
    for i, row in df_f.iterrows():
        pdf.set_fill_color(250, 250, 250) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(10, 8, str(i+1), 0, 0, 'C', 1); pdf.cell(90, 8, f" {row['Nama Barang']}", 0, 0, 'L', 1)
        pdf.cell(20, 8, str(int(row['Qty'])), 0, 0, 'C', 1); pdf.cell(20, 8, str(row['Satuan']), 0, 0, 'C', 1)
        pdf.cell(25, 8, f"{row['Harga']:,.0f} ", 0, 0, 'R', 1); pdf.cell(25, 8, f"{row['Total_Row']:,.0f} ", 0, 1, 'R', 1)
        fill = not fill; pdf.set_draw_color(240, 240, 240); pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    # Summary
    pdf.ln(5); y_sum = pdf.get_y()
    pdf.set_font('Arial', 'B', 8); pdf.set_text_color(*CP_GOLD); pdf.cell(0, 5, "NOTES & TERMS:", ln=1)
    pdf.set_font('Arial', '', 7); pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(100, 4, "1. Harga sudah termasuk PPN 11%.\n2. Berlaku 14 hari kerja.\n3. Pembayaran via Transfer Bank.")
    
    pdf.set_xy(130, y_sum); pdf.set_font('Arial', '', 10); pdf.set_text_color(0, 0, 0)
    pdf.cell(40, 7, "Sub Total", 0, 0, 'R'); pdf.cell(30, 7, f"Rp {subt:,.0f}", 0, 1, 'R')
    pdf.set_x(130); pdf.cell(40, 7, "VAT (11%)", 0, 0, 'R'); pdf.cell(30, 7, f"Rp {tax:,.0f}", 0, 1, 'R')
    pdf.set_x(130); pdf.set_fill_color(*CP_NAVY); pdf.set_text_color(255, 255, 255); pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, "GRAND TOTAL", 0, 0, 'R', 1); pdf.cell(30, 10, f"Rp {gtot:,.0f}", 0, 1, 'R', 1)
    
    pdf.ln(15); pdf.set_x(140); pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 10)
    pdf.cell(50, 5, "Hormat Kami,", 0, 1, 'C'); pdf.ln(12); pdf.set_x(140)
    pdf.set_font('Arial', 'B', 10); pdf.cell(50, 5, MARKETING_NAME, 0, 1, 'C')
    pdf.set_x(140); pdf.set_font('Arial', '', 8); pdf.cell(50, 5, "Sales Consultant", 0, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# 4. APLIKASI UTAMA
# =========================================================
df_barang = load_db(); sheet = connect_gsheet()
menu = st.sidebar.radio("NAVIGASI:", ["🛒 STAFF AREA", "🔐 BOSS AREA"])

if menu == "🛒 STAFF AREA":
    t1, t2 = st.tabs(["📝 Pesanan Baru", "📄 Faktur Pajak"])
    with t1:
        with st.container(border=True):
            col1, col2 = st.columns(2)
            tk = col1.text_input("Nama Toko"); up = col2.text_input("UP")
            wa = col1.text_input("WA"); pb = st.multiselect("Pilih:", df_barang['Nama Barang'].tolist())
            if st.button("➕ Tambah Ke List"):
                for b in pb:
                    if b not in st.session_state.cart: st.session_state.cart.append(b)
                st.rerun()
        if st.session_state.get('cart'):
            f_list = []
            for item in st.session_state.cart:
                d = df_barang[df_barang['Nama Barang'] == item].iloc[0]
                with st.container(border=True):
                    c_a, c_b, c_c = st.columns([3, 1, 0.5])
                    c_a.write(f"**{item}** (Rp {d['Harga']:,.0f})")
                    q = c_b.number_input("Qty", 1, key=f"sq_{item}")
                    if c_c.button("❌", key=f"sd_{item}"): st.session_state.cart.remove(item); st.rerun()
                    f_list.append({"Nama Barang": item, "Qty": q, "Harga": float(d['Harga']), "Satuan": d['Satuan'], "Total_Row": q*d['Harga']})
            if st.button("🚀 KIRIM", use_container_width=True):
                if sheet and tk:
                    wkt = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")
                    sheet.append_row([wkt, tk, up, wa, str(f_list), "Pending", MARKETING_NAME])
                    st.success("Terkirim!"); st.session_state.cart = []
    with t2:
        ci, cn = st.columns(2); inv = ci.text_input("No INV"); nm = cn.text_input("Nama PT")
        if st.button("🔍 Cari"):
            f = search_pajak_file(inv, nm)
            if f: st.download_button("📥 Download", download_drive_file(f['id']), f['name'])
            else: st.error("Nihil.")

elif menu == "🔐 BOSS AREA":
    if st.sidebar.text_input("Password:", type="password") == ADMIN_PASSWORD:
        if sheet:
            all_v = sheet.get_all_values()
            df = pd.DataFrame(all_v[1:], columns=all_v[0]) if len(all_v)>1 else pd.DataFrame()
            df = df[df['Sales'] == MARKETING_NAME]
            v_mode = st.radio("Status:", ["Antrean", "Arsip"], horizontal=True)
            df_s = df[df['Status'] == ("Pending" if "Antrean" in v_mode else "Processed")]
            for idx, row in df_s.iterrows():
                r_idx = idx + 2
                with st.expander(f"📄 {row['Customer']}"):
                    try: items = ast.literal_eval(str(row['Pesanan']))
                    except: items = []
                    add = st.multiselect("Tambah:", df_barang['Nama Barang'].tolist(), key=f"a_{idx}")
                    for a in add:
                        if not any(x['Nama Barang'] == a for x in items):
                            d = df_barang[df_barang['Nama Barang'] == a].iloc[0]
                            items.append({"Nama Barang": a, "Qty": 1, "Harga": float(d['Harga']), "Satuan": str(d['Satuan']), "Total_Row": float(d['Harga'])})
                    n_list = []
                    for i, it in enumerate(items):
                        c1, c2, c3, c4, c5 = st.columns([3, 0.7, 0.8, 1.2, 0.5])
                        c1.write(f"**{it['Nama Barang']}**")
                        nq = c2.number_input("Q", int(it['Qty']), key=f"q_{idx}_{i}")
                        ns = c3.text_input("S", it['Satuan'], key=f"s_{idx}_{i}")
                        nh = c4.number_input("Rp", float(it['Harga']), key=f"h_{idx}_{i}")
                        if not c5.checkbox("Hapus", key=f"dl_{idx}_{i}"):
                            n_list.append({"Nama Barang": it['Nama Barang'], "Qty": nq, "Harga": nh, "Satuan": ns, "Total_Row": nq*nh})
                    if st.button("💾 UPDATE", key=f"sv_{idx}"):
                        sheet.update_cell(r_idx, 5, str(n_list)); st.rerun()
                    if n_list:
                        sb = sum(x['Total_Row'] for x in n_list); tx = sb*0.11; gt = sb+tx
                        sc1, sc2 = st.columns(2)
                        sc1.metric("Total", f"Rp {gt:,.0f}")
                        nos = sc1.text_input("No Surat:", f"..../S-TTS/II/{datetime.now().year}", key=f"n_{idx}")
                        pdf_b = generate_pdf(nos, row['Customer'], row['UP'], pd.DataFrame(n_list), sb, tx, gt)
                        sc2.download_button("📩 PDF LUXURY", pdf_b, f"{row['Customer']}.pdf", key=f"p_{idx}")
                        if sc2.button("✅ SELESAI", key=f"dn_{idx}"):
                            sheet.update_cell(r_idx, 6, "Processed"); st.rerun()
