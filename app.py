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
# 1. KONFIGURASI PROFIL MARKETING (GANTI BAGIAN INI SAJA)
# =========================================================
# Ganti data di bawah ini sesuai siapa yang punya link:
SALES_NAME = "Asin" 
SALES_WA   = "08158199775"
SALES_EMAIL = "alattulis.tts@gmail.com"
# =========================================================

COMPANY_NAME = "PT. THEA THEO STATIONARY"
SLOGAN = "Supplier Alat Tulis Kantor & Sekolah"
ADDR = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
PAJAK_FOLDER_ID = '19i_mLcu4VtV85NLwZY67zZTGwxBgdG1z' 

st.set_page_config(page_title=f"TTS - {SALES_NAME}", layout="wide")

# --- 2. KONEKSI GOOGLE SERVICES ---
def get_creds():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)

def connect_gsheet():
    try:
        client = gspread.authorize(get_creds())
        return client.open("Antrean Penawaran TTS").sheet1
    except Exception as e:
        st.error(f"Koneksi GSheets Gagal: {e}")
        return None

# --- 3. FUNGSI PENCARIAN DRIVE ---
def search_pajak_file(inv_keyword, name_keyword):
    try:
        service = build('drive', 'v3', credentials=get_creds())
        clean_inv = re.sub(r'[^A-Z0-9]', '', inv_keyword.upper())
        clean_name = re.sub(r'[^A-Z0-9]', '', name_keyword.upper())
        query = f"'{PAJAK_FOLDER_ID}' in parents and mimeType = 'application/pdf' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)", pageSize=1000).execute()
        files = results.get('files', [])
        for f in files:
            file_name_clean = re.sub(r'[^A-Z0-9]', '', f['name'].upper())
            if clean_inv in file_name_clean and clean_name in file_name_clean:
                return f 
        return None
    except: return None

def download_drive_file(file_id):
    service = build('drive', 'v3', credentials=get_creds())
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done: _, done = downloader.next_chunk()
    return fh.getvalue()

# --- 4. DATABASE & PDF ENGINE ---
def load_db():
    if os.path.exists("database_barang.xlsx"):
        try:
            df = pd.read_excel("database_barang.xlsx")
            df.columns = df.columns.str.strip()
            if 'Harga' in df.columns:
                df['Harga'] = pd.to_numeric(df['Harga'], errors='coerce').fillna(0)
            return df
        except: pass
    return pd.DataFrame(columns=['Nama Barang', 'Harga', 'Satuan'])

df_barang = load_db()

class PenawaranPDF(FPDF):
    def header(self):
        # LOGO (Pastikan file logo.png ada di GitHub)
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 25)
            self.set_x(38)
        
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 51, 102)
        self.cell(80, 7, COMPANY_NAME, ln=0)
        
        self.set_font('Arial', '', 8)
        self.set_text_color(0, 0, 0)
        self.cell(0, 4, ADDR, ln=1, align='R')
        
        if os.path.exists("logo.png"): self.set_x(38)
        self.set_font('Arial', 'I', 9)
        self.cell(80, 5, SLOGAN, ln=0)
        
        self.set_font('Arial', '', 8)
        # KONTAK MENGIKUTI DATA MARKETING
        self.cell(0, 4, f"WA: {SALES_WA} | Email: {SALES_EMAIL}", ln=1, align='R')
        self.line(10, 30, 200, 30)
        self.ln(12)

def generate_pdf(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    pdf = PenawaranPDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 10)
    waktu_jkt = datetime.utcnow() + timedelta(hours=7)
    tgl_skrg = waktu_jkt.strftime('%d %B %Y')
    
    pdf.cell(95, 6, f"No: {no_surat}", ln=0)
    pdf.cell(95, 6, f"Tangerang, {tgl_skrg}", ln=1, align='R')
    pdf.cell(0, 6, f"Sales Consultant: {SALES_NAME}", ln=1)
    pdf.cell(0, 6, "Hal: Surat Penawaran Harga", ln=1)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "Kepada Yth,", ln=1); pdf.cell(0, 6, str(nama_cust), ln=1); pdf.cell(0, 6, f"Up. {pic}", ln=1)
    pdf.ln(5)
    
    # Tabel
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(10, 10, 'No', 1, 0, 'C', True); pdf.cell(85, 10, 'Nama Barang', 1, 0, 'C', True)
    pdf.cell(20, 10, 'Qty', 1, 0, 'C', True); pdf.cell(20, 10, 'Satuan', 1, 0, 'C', True)
    pdf.cell(25, 10, 'Harga', 1, 0, 'C', True); pdf.cell(30, 10, 'Total', 1, 1, 'C', True)

    pdf.set_font('Arial', '', 9)
    for i, row in df_order.iterrows():
        pdf.cell(10, 8, str(i+1), 1, 0, 'C'); pdf.cell(85, 8, str(row['Nama Barang']), 1)
        pdf.cell(20, 8, str(int(row['Qty'])), 1, 0, 'C'); pdf.cell(20, 8, str(row['Satuan']), 1, 0, 'C')
        pdf.cell(25, 8, f"{row['Harga']:,.0f}", 1, 0, 'R'); pdf.cell(30, 8, f"{row['Total_Row']:,.0f}", 1, 1, 'R')

    pdf.ln(2); pdf.set_font('Arial', 'B', 10)
    pdf.cell(160, 8, "Sub Total", 0, 0, 'R'); pdf.cell(30, 8, f"{subtotal:,.0f}", 1, 1, 'R')
    pdf.cell(160, 8, "PPN 11%", 0, 0, 'R'); pdf.cell(30, 8, f"{ppn:,.0f}", 1, 1, 'R')
    pdf.cell(160, 8, "GRAND TOTAL", 0, 0, 'R')
    pdf.set_fill_color(255, 255, 0); pdf.cell(30, 8, f"{grand_total:,.0f}", 1, 1, 'R', True)
    
    pdf.ln(10); pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "Hormat Kami,", ln=1); pdf.ln(15)
    pdf.cell(0, 6, f"{SALES_NAME}", ln=1) # Nama di tanda tangan
    pdf.set_font('Arial', '', 9); pdf.cell(0, 5, "Sales Consultant", ln=1)
    pdf.cell(0, 5, f"WA: {SALES_WA}", ln=1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 5. TAMPILAN ---
st.title(f"🚀 Portal {SALES_NAME} - TTS")

menu = st.sidebar.selectbox("Menu:", ["🛒 Portal Customer", "👨‍💻 Admin"])

if 'cart' not in st.session_state: st.session_state.cart = []

if menu == "🛒 Portal Customer":
    t1, t2 = st.tabs(["Buat Penawaran", "Ambil Faktur"])
    with t1:
        with st.container(border=True):
            col1, col2 = st.columns(2)
            c_name = col1.text_input("Nama Toko/PT")
            c_up = col2.text_input("Nama UP")
            c_wa = col1.text_input("WhatsApp Pembeli")
            picks = st.multiselect("Pilih Barang:", options=df_barang['Nama Barang'].tolist())
            if st.button("Tambah ke List"):
                for p in picks:
                    if p not in st.session_state.cart: st.session_state.cart.append(p)
                st.rerun()

        if st.session_state.cart:
            final_items = []
            for itm in st.session_state.cart:
                rb = df_barang[df_barang['Nama Barang'] == itm].iloc[0]
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 1.5, 1, 0.5])
                    c1.write(f"**{itm}**")
                    qty = c3.number_input(f"Qty", min_value=1, value=1, key=f"q_{itm}")
                    if c4.button("🗑️", key=f"d_{itm}"):
                        st.session_state.cart.remove(itm); st.rerun()
                    final_items.append({"Nama Barang": itm, "Qty": qty, "Harga": rb['Harga'], "Satuan": rb['Satuan'], "Total_Row": qty * rb['Harga']})
            
            if st.button(f"Kirim ke {SALES_NAME}", use_container_width=True):
                sheet = connect_gsheet()
                if sheet and c_name:
                    sheet.append_row([(datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M"), c_name, c_up, c_wa, str(final_items), "Pending", SALES_NAME])
                    st.success("Tersimpan!"); st.session_state.cart = []; st.rerun()

elif menu == "👨‍💻 Admin":
    pwd = st.sidebar.text_input("Password", type="password")
    if pwd == ADMIN_PASSWORD:
        sheet = connect_gsheet()
        if sheet:
            data = sheet.get_all_values()
            if len(data) > 1:
                df_gs = pd.DataFrame(data[1:], columns=data[0])
                # Filter agar sales hanya melihat miliknya sendiri
                pending = df_gs[(df_gs['Status'] == 'Pending') & (df_gs['Sales'] == SALES_NAME)]
                for idx, row in pending.iterrows():
                    with st.expander(f"Order: {row['Customer']}"):
                        items = ast.literal_eval(row['Pesanan'])
                        updated = []
                        for i, r in enumerate(items):
                            c1, c2, c3 = st.columns([3, 1, 1.5])
                            nq = c1.number_input(f"{r['Nama Barang']}", value=int(r['Qty']), key=f"aq_{idx}_{i}")
                            nh = c2.number_input(f"Harga", value=float(r['Harga']), key=f"ah_{idx}_{i}")
                            updated.append({"Nama Barang": r['Nama Barang'], "Qty": nq, "Harga": nh, "Satuan": r['Satuan'], "Total_Row": nq * nh})
                        
                        no_s = st.text_input("No Surat:", value=f"..../S-TTS/II/{datetime.now().year}", key=f"ns_{idx}")
                        if st.button("Cetak PDF", key=f"cp_{idx}"):
                            df_f = pd.DataFrame(updated); subt = df_f['Total_Row'].sum(); tax = subt * 0.11; gt = subt + tax
                            pdf_b = generate_pdf(no_s, row['Customer'], row['UP'], df_f, subt, tax, gt)
                            st.download_button("Download PDF", data=pdf_b, file_name=f"TTS_{row['Customer']}.pdf", key=f"dl_{idx}")
                        if st.button("Arsipkan", key=f"ar_{idx}"):
                            sheet.update_cell(idx+2, 6, "Processed"); st.rerun()
