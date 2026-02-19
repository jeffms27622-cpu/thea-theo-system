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

# --- 1. KONFIGURASI UTAMA ---
COMPANY_NAME = "PT. THEA THEO STATIONARY"
SLOGAN = "Solusi Kebutuhan Kantor & Sekolah Terlengkap"
ADDR = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
CONTACT = "Ph: 021-55780659, WA: 08158199775 | email: alattulis.tts@gmail.com"

# Password & Folder ID (Menggunakan Secrets Langsung)
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
PAJAK_FOLDER_ID = '19i_mLcu4VtV85NLwZY67zZTGwxBgdG1z' 

st.set_page_config(page_title=COMPANY_NAME, layout="wide", page_icon="📝")

# --- 2. CSS CUSTOM (UI 10/10) ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #004a99; color: white; font-weight: bold; }
    .stButton>button:hover { background-color: #003366; color: #ffca28; }
    .item-card { background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.02); }
    [data-testid="stMetricValue"] { color: #004a99; font-size: 28px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNGSI KONEKSI ---
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
        q_inv = re.sub(r'[^A-Z0-9]', '', inv_keyword.upper())
        q_name = re.sub(r'[^A-Z0-9]', '', name_keyword.upper())
        query = f"'{PAJAK_FOLDER_ID}' in parents and mimeType = 'application/pdf' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)", pageSize=1000).execute()
        files = results.get('files', [])
        for f in files:
            fname = re.sub(r'[^A-Z0-9]', '', f['name'].upper())
            if q_inv in fname and q_name in fname: return f 
        return None
    except: return None

def download_drive_file(file_id):
    service = build('drive', 'v3', credentials=get_creds())
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO(); downloader = MediaIoBaseDownload(fh, request)
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
class PenawaranPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15); self.set_text_color(0, 74, 153)
        self.cell(0, 7, COMPANY_NAME, ln=1)
        self.set_font('Arial', '', 8); self.set_text_color(0, 0, 0)
        self.cell(0, 5, f"{ADDR} | {CONTACT}", ln=1); self.line(10, 25, 200, 25); self.ln(10)

def generate_pdf(no_s, cust, pic, df_o, gtot):
    pdf = PenawaranPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 10); pdf.cell(0, 6, f"Penawaran Harga No: {no_s}", ln=1)
    pdf.set_font('Arial', '', 10); pdf.cell(0, 6, f"Kepada Yth: {cust} (UP: {pic})", ln=1); pdf.ln(5)
    pdf.set_fill_color(230, 230, 230); pdf.cell(10, 8, 'No', 1, 0, 'C', 1); pdf.cell(90, 8, 'Nama Barang', 1, 0, 'C', 1); pdf.cell(20, 8, 'Qty', 1, 0, 'C', 1); pdf.cell(30, 8, 'Harga', 1, 0, 'C', 1); pdf.cell(40, 8, 'Total', 1, 1, 'C', 1)
    for i, r in df_o.iterrows():
        pdf.cell(10, 8, str(i+1), 1, 0, 'C'); pdf.cell(90, 8, str(r['Nama Barang']), 1); pdf.cell(20, 8, f"{int(r['Qty'])} {r.get('Satuan','Pcs')}", 1, 0, 'C'); pdf.cell(30, 8, f"{r['Harga']:,.0f}", 1, 0, 'R'); pdf.cell(40, 8, f"{r['Total_Row']:,.0f}", 1, 1, 'R')
    pdf.ln(5); pdf.set_font('Arial', 'B', 10); pdf.cell(150, 7, "TOTAL (Inc. PPN 11%)", 0, 0, 'R'); pdf.cell(40, 7, f"Rp {gtot:,.0f}", 1, 1, 'R')
    return pdf.output(dest='S').encode('latin-1')

# --- 5. LOGIKA MENU ---
if 'cart' not in st.session_state: st.session_state.cart = []

menu = st.sidebar.selectbox("🧭 Navigasi", ["🏠 Beranda", "🛒 Penawaran Mandiri", "📄 Ambil Faktur", "🔒 Admin"])

if menu == "🏠 Beranda":
    st.markdown(f"<div style='background-color:#004a99; padding:40px; border-radius:15px; text-align:center; color:white;'><h1>{COMPANY_NAME}</h1><p>{SLOGAN}</p></div>", unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    c1.metric("📦 Status", "Ready Stock")
    c2.metric("⚡ Sistem", "Otomatis")

elif menu == "🛒 Penawaran Mandiri":
    st.title("🛒 Katalog & Penawaran Mandiri")
    with st.container(border=True):
        st.write("### 1. Cari & Tambah Barang")
        c_sel, c_btn = st.columns([3, 1])
        pilihan = c_sel.selectbox("Pilih Produk:", ["-- Pilih --"] + df_barang['Nama Barang'].tolist())
        if c_btn.button("➕ Tambah"):
            if pilihan != "-- Pilih --" and pilihan not in st.session_state.cart:
                st.session_state.cart.append(pilihan); st.rerun()

    if st.session_state.cart:
        st.write("### 2. Isi Jumlah Pesanan")
        final_list = []; total_est = 0
        for item in st.session_state.cart:
            db_row = df_barang[df_barang['Nama Barang'] == item].iloc[0]
            with st.markdown('<div class="item-card">', unsafe_allow_html=True):
                col_n, col_p, col_q, col_d = st.columns([3, 1.5, 1, 0.5])
                col_n.write(f"**{item}**")
                col_p.write(f"Rp {db_row['Harga']:,.0f} / {db_row['Satuan']}")
                qty = col_q.number_input("Qty", min_value=1, key=f"q_{item}")
                if col_d.button("🗑️", key=f"d_{item}"):
                    st.session_state.cart.remove(item); st.rerun()
                t_row = qty * db_row['Harga']
                total_est += t_row
                final_list.append({"Nama Barang": item, "Qty": qty, "Harga": db_row['Harga'], "Satuan": db_row['Satuan'], "Total_Row": t_row})
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.metric("Total Sementara", f"Rp {total_est:,.0f}")
        with st.expander("🚀 3. Kirim Data"):
            c_nama = st.text_input("Nama Perusahaan / Toko")
            c_up = st.text_input("Nama UP (PIC)")
            c_wa = st.text_input("Nomor WA")
            if st.button("Kirim Sekarang"):
                if c_nama and c_wa:
                    sh = connect_gsheet()
                    if sh:
                        sh.append_row([datetime.now().strftime("%Y-%m-%d"), c_nama, c_up, c_wa, str(final_list), "Pending"])
                        st.balloons(); st.success("Terkirim! Tunggu WA dari kami."); st.session_state.cart = []; st.rerun()

elif menu == "📄 Ambil Faktur":
    st.title("📄 Ambil Faktur Pajak")
    inv = st.text_input("No. Invoice:")
    name = st.text_input("Nama PT:")
    if st.button("Cari & Unduh"):
        res = search_pajak_file(inv, name)
        if res:
            st.success(f"Ditemukan: {res['name']}")
            st.download_button("📥 Download PDF", data=download_drive_file(res['id']), file_name=res['name'])
        else: st.error("Data tidak ditemukan.")

elif menu == "🔒 Admin":
    st.title("🔒 Admin Panel")
    pwd = st.sidebar.text_input("Password Admin", type="password")
    if pwd == ADMIN_PASSWORD:
        sh = connect_gsheet()
        if sh:
            vals = sh.get_all_values()
            if len(vals) > 1:
                df_gs = pd.DataFrame(vals[1:], columns=vals[0])
                pending = df_gs[df_gs['Status'] == 'Pending']
                for idx, row in pending.iterrows():
                    try: items_adm = ast.literal_eval(row['Pesanan'])
                    except: st.error(f"Data baris {idx+2} rusak."); continue
                    
                    with st.expander(f"📦 Order: {row['Customer']}"):
                        upd = []
                        for i, itm in enumerate(items_adm):
                            c1, c2, c3, c4 = st.columns([3, 1, 1, 0.5])
                            c1.write(itm['Nama Barang'])
                            nq = c2.number_input("Qty", value=int(itm['Qty']), key=f"aq_{idx}_{i}")
                            nh = c3.number_input("Harga", value=float(itm['Harga']), key=f"ah_{idx}_{i}")
                            if not c4.checkbox("Hapus", key=f"ax_{idx}_{i}"):
                                upd.append({"Nama Barang": itm['Nama Barang'], "Qty": nq, "Harga": nh, "Satuan": itm.get('Satuan','Pcs'), "Total_Row": nq * nh})
                        
                        st.divider()
                        if st.button("💾 Update & Buat PDF", key=f"u_{idx}"):
                            df_f = pd.DataFrame(upd); sub = df_f['Total_Row'].sum(); gt = sub * 1.11
                            pdf = generate_pdf("S-TTS/2026", row['Customer'], row['UP'], df_f, gt)
                            st.download_button("📥 Download Penawaran", data=pdf, file_name=f"TTS_{row['Customer']}.pdf", key=f"dl_{idx}")
                            sh.update_cell(idx+2, 5, str(upd))
                        if st.button("✅ Arsipkan (Selesai)", key=f"f_{idx}"):
                            sh.update_cell(idx+2, 6, "Processed"); st.rerun()
            else: st.info("Antrean kosong.")
    else: st.warning("Masukkan Password di Sidebar.")
