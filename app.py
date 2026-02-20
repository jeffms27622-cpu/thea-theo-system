import streamlit as st
import pandas as pd
import ast
from datetime import datetime
from fpdf import FPDF
import os
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import re

# --- 1. KONFIGURASI IDENTITAS & SECRETS ---
COMPANY_NAME = "PT. THEA THEO STATIONARY"
SLOGAN = "Supplier Alat Tulis Kantor & Sekolah Terlengkap"
ADDR = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
CONTACT = "Ph: 021-55780659, WA: 08158199775 | email: alattulis.tts@gmail.com"

# Keamanan Secrets
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
PAJAK_FOLDER_ID = '19i_mLcu4VtV85NLwZY67zZTGwxBgdG1z' 

st.set_page_config(page_title=COMPANY_NAME, layout="wide", page_icon="📝")

# --- 2. CSS CUSTOM (MEMPERCANTIK TANPA MERUSAK FITUR) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #e1e8f0; border-radius: 5px 5px 0 0; padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #004a99 !important; color: white !important; }
    .card {
        background-color: white; padding: 15px; border-radius: 10px;
        border-left: 5px solid #004a99; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNGSI INTI ---
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
        clean_inv = re.sub(r'[^A-Z0-9]', '', inv_keyword.upper())
        clean_name = re.sub(r'[^A-Z0-9]', '', name_keyword.upper())
        query = f"'{PAJAK_FOLDER_ID}' in parents and mimeType = 'application/pdf' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)", pageSize=1000).execute()
        files = results.get('files', [])
        for f in files:
            fname = re.sub(r'[^A-Z0-9]', '', f['name'].upper())
            if clean_inv in fname and clean_name in fname: return f 
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

# --- 4. PDF ENGINE ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14); self.set_text_color(0, 74, 153)
        self.cell(0, 8, COMPANY_NAME, ln=True)
        self.set_font('Arial', '', 8); self.set_text_color(0, 0, 0)
        self.cell(0, 4, f"{SLOGAN} | {ADDR}", ln=True)
        self.cell(0, 4, CONTACT, ln=True); self.line(10, 30, 200, 30); self.ln(10)

def generate_pdf(no_s, cust, pic, df_o, subt, tax, gtot):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 10)
    pdf.cell(100, 6, f"No: {no_s}"); pdf.cell(90, 6, f"Tgl: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='R')
    pdf.ln(5); pdf.set_font('Arial', 'B', 10); pdf.cell(0, 6, f"Kepada Yth: {cust} (UP: {pic})", ln=True); pdf.ln(5)
    pdf.set_fill_color(230, 230, 230); pdf.set_font('Arial', 'B', 9)
    pdf.cell(10, 8, 'No', 1, 0, 'C', 1); pdf.cell(90, 8, 'Nama Barang', 1, 0, 'C', 1)
    pdf.cell(20, 8, 'Qty', 1, 0, 'C', 1); pdf.cell(30, 8, 'Harga', 1, 0, 'C', 1); pdf.cell(40, 8, 'Total', 1, 1, 'C', 1)
    pdf.set_font('Arial', '', 9)
    for i, r in df_o.iterrows():
        pdf.cell(10, 8, str(i+1), 1, 0, 'C'); pdf.cell(90, 8, str(r['Nama Barang']), 1)
        pdf.cell(20, 8, f"{int(r['Qty'])} {r['Satuan']}", 1, 0, 'C')
        pdf.cell(30, 8, f"{r['Harga']:,.0f}", 1, 0, 'R'); pdf.cell(40, 8, f"{r['Total_Row']:,.0f}", 1, 1, 'R')
    pdf.ln(5); pdf.set_font('Arial', 'B', 9)
    pdf.cell(150, 7, "Subtotal", 0, 0, 'R'); pdf.cell(40, 7, f"{subt:,.0f}", 1, 1, 'R')
    pdf.cell(150, 7, "PPN 11%", 0, 0, 'R'); pdf.cell(40, 7, f"{tax:,.0f}", 1, 1, 'R')
    pdf.cell(150, 7, "GRAND TOTAL", 0, 0, 'R'); pdf.cell(40, 7, f"{gtot:,.0f}", 1, 1, 'R')
    return pdf.output(dest='S').encode('latin-1')

# --- 5. INTERFACE ---
st.markdown(f"<h1 style='text-align: center; color: #004a99;'>{COMPANY_NAME}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #666;'>{SLOGAN}</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 Penawaran Mandiri", "📥 Ambil Faktur Pajak", "🔒 Admin Dashboard"])

with tab1:
    if 'cart' not in st.session_state: st.session_state.cart = []
    
    with st.container(border=True):
        st.write("### 🛒 Tambah Barang ke List")
        c_sel, c_btn = st.columns([3, 1])
        item_pilih = c_sel.selectbox("Cari Produk:", ["-- Pilih --"] + df_barang['Nama Barang'].tolist())
        if c_btn.button("➕ Tambahkan"):
            if item_pilih != "-- Pilih --" and item_pilih not in st.session_state.cart:
                st.session_state.cart.append(item_pilih); st.rerun()

    if st.session_state.cart:
        st.write("### 📋 Daftar Pesanan Bapak")
        final_list = []
        for item in st.session_state.cart:
            with st.markdown(f'<div class="card">', unsafe_allow_html=True):
                col1, col2, col3 = st.columns([3, 1, 0.5])
                col1.write(f"**{item}**")
                qty = col2.number_input("Qty", min_value=1, value=1, key=f"u_q_{item}")
                if col3.button("🗑️", key=f"u_d_{item}"):
                    st.session_state.cart.remove(item); st.rerun()
                
                b_row = df_barang[df_barang['Nama Barang'] == item].iloc[0]
                final_list.append({
                    "Nama Barang": item, "Qty": int(qty), 
                    "Harga": int(b_row['Harga']), "Satuan": str(b_row['Satuan'])
                })
            st.markdown('</div>', unsafe_allow_html=True)

        with st.form("kirim_order"):
            c_name = st.text_input("Nama Toko/Perusahaan")
            c_up = st.text_input("Nama UP")
            c_wa = st.text_input("Nomor WhatsApp")
            if st.form_submit_button("🚀 Kirim Pengajuan Penawaran"):
                sh = connect_gsheet()
                if sh and c_name and c_wa:
                    sh.append_row([datetime.now().strftime("%Y-%m-%d"), c_name, c_up, c_wa, str(final_list), "Pending"])
                    st.balloons(); st.success("Terkirim! Admin akan segera menghubungi Bapak."); st.session_state.cart = []
                else: st.error("Lengkapi Nama & WhatsApp.")

with tab2:
    st.subheader("🔍 Cari Faktur Pajak")
    inv_in = st.text_input("Nomor Invoice (Angka saja):")
    pt_in = st.text_input("Nama PT/Toko (Sesuai Faktur):")
    if st.button("Cari & Download PDF"):
        res = search_pajak_file(inv_in, pt_in)
        if res:
            st.success(f"Ditemukan: {res['name']}")
            st.download_button("📥 Download Sekarang", data=download_drive_file(res['id']), file_name=res['name'])
        else: st.error("Data tidak ditemukan.")

with tab3:
    st.subheader("🔒 Admin Nego Harga")
    pw = st.text_input("Password Admin", type="password")
    if pw == ADMIN_PASSWORD:
        sh = connect_gsheet()
        if sh:
            vals = sh.get_all_values()
            if len(vals) > 1:
                df_gs = pd.DataFrame(vals[1:], columns=vals[0])
                pending = df_gs[df_gs['Status'] == 'Pending']
                for idx, row in pending.iterrows():
                    with st.expander(f"Order: {row['Customer']} ({row['Tanggal']})"):
                        try: items_adm = ast.literal_eval(row['Pesanan'])
                        except: st.error("Data Rusak."); continue
                        
                        upd_adm = []
                        for i, itm in enumerate(items_adm):
                            col1, col2, col3, col4 = st.columns([3, 1, 1, 0.5])
                            col1.write(itm['Nama Barang'])
                            nq = col2.number_input("Qty", value=int(itm['Qty']), key=f"aq_{idx}_{i}")
                            nh = col3.number_input("Harga", value=float(itm['Harga']), key=f"ah_{idx}_{i}")
                            if not col4.checkbox("Hapus", key=f"ax_{idx}_{i}"):
                                upd_adm.append({"Nama Barang": itm['Nama Barang'], "Qty": nq, "Harga": nh, "Satuan": itm['Satuan'], "Total_Row": nq * nh})
                        
                        if st.button("💾 Update Harga & Cetak PDF", key=f"btn_{idx}"):
                            df_f = pd.DataFrame(upd_adm)
                            sub = df_f['Total_Row'].sum(); ppn = sub * 0.11; gt = sub + ppn
                            pdf_b = generate_pdf("OFFER-TTS", row['Customer'], row['UP'], df_f, sub, ppn, gt)
                            st.download_button("📥 Download PDF Hasil Nego", data=pdf_b, file_name=f"TTS_{row['Customer']}.pdf", key=f"dl_{idx}")
                            sh.update_cell(idx+2, 5, str(upd_adm))
                        
                        if st.button("✅ Selesai (Arsipkan)", key=f"fin_{idx}"):
                            sh.update_cell(idx+2, 6, "Processed"); st.rerun()
            else: st.info("Antrean kosong.")
