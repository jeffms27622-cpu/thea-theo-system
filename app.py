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

# --- 1. KONFIGURASI IDENTITAS ---
COMPANY_NAME = "PT. THEA THEO STATIONARY"
SLOGAN = "Supplier Alat Tulis Kantor & Sekolah"
ADDR = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
CONTACT = "Ph: 021-55780659, WA: 08158199775 | email: alattulis.tts@gmail.com"

# SEKARANG 
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# ID FOLDER GOOGLE DRIVE BAPAK
PAJAK_FOLDER_ID = '19i_mLcu4VtV85NLwZY67zZTGwxBgdG1z' 

st.set_page_config(page_title=COMPANY_NAME, layout="wide", page_icon="📝")

# --- 2. CUSTOM CSS (Tampilan 10/10) ---
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #004a99;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px;
    }
    .stButton>button:hover {
        background-color: #003366;
        color: #ffca28;
    }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #004a99; }
    .footer { text-align: center; color: #888; font-size: 0.8em; margin-top: 50px; }
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
        clean_inv = re.sub(r'[^A-Z0-9]', '', inv_keyword.upper())
        clean_name = re.sub(r'[^A-Z0-9]', '', name_keyword.upper())
        query = f"'{PAJAK_FOLDER_ID}' in parents and mimeType = 'application/pdf' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)", pageSize=1000).execute()
        files = results.get('files', [])
        for f in files:
            fn_clean = re.sub(r'[^A-Z0-9]', '', f['name'].upper())
            if clean_inv in fn_clean and clean_name in fn_clean: return f 
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
        self.set_font('Arial', 'I', 9); self.cell(0, 5, SLOGAN, ln=1)
        self.set_font('Arial', '', 8); self.set_text_color(0, 0, 0)
        self.cell(0, 5, f"{ADDR} | {CONTACT}", ln=1); self.line(10, 28, 200, 28); self.ln(10)

def generate_pdf(no_s, cust, pic, df_o, subt, tax, gtot):
    pdf = PenawaranPDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 10)
    pdf.cell(95, 6, f"No: {no_s}", ln=0); pdf.cell(95, 6, f"Tgl: {datetime.now().strftime('%d/%m/%Y')}", ln=1, align='R')
    pdf.ln(5); pdf.set_font('Arial', 'B', 10); pdf.cell(0, 6, f"Kepada Yth: {cust} (UP: {pic})", ln=1); pdf.ln(5)
    
    pdf.set_fill_color(230, 230, 230); pdf.set_font('Arial', 'B', 9)
    pdf.cell(10, 8, 'No', 1, 0, 'C', 1); pdf.cell(90, 8, 'Nama Barang', 1, 0, 'C', 1)
    pdf.cell(20, 8, 'Qty', 1, 0, 'C', 1); pdf.cell(30, 8, 'Harga', 1, 0, 'C', 1); pdf.cell(40, 8, 'Total', 1, 1, 'C', 1)
    
    pdf.set_font('Arial', '', 9)
    for i, r in df_o.iterrows():
        pdf.cell(10, 8, str(i+1), 1, 0, 'C'); pdf.cell(90, 8, str(r['Nama Barang']), 1)
        pdf.cell(20, 8, str(int(r['Qty'])), 1, 0, 'C'); pdf.cell(30, 8, f"{r['Harga']:,.0f}", 1, 0, 'R')
        pdf.cell(40, 8, f"{r['Total_Row']:,.0f}", 1, 1, 'R')
    
    pdf.ln(5); pdf.cell(150, 7, "Subtotal", 0, 0, 'R'); pdf.cell(40, 7, f"{subt:,.0f}", 1, 1, 'R')
    pdf.cell(150, 7, "PPN 11%", 0, 0, 'R'); pdf.cell(40, 7, f"{tax:,.0f}", 1, 1, 'R')
    pdf.set_font('Arial', 'B', 10); pdf.cell(150, 7, "GRAND TOTAL", 0, 0, 'R'); pdf.cell(40, 7, f"{gtot:,.0f}", 1, 1, 'R')
    return pdf.output(dest='S').encode('latin-1')

# --- 5. NAVIGASI ---
menu = st.sidebar.selectbox("🧭 Menu Utama", ["🏠 Beranda", "📑 Portal Customer", "🔒 Admin Dashboard"])

if menu == "🏠 Beranda":
    st.markdown(f"""
        <div style="background-color:#004a99; padding:50px; border-radius:15px; text-align:center; color:white;">
            <h1>{COMPANY_NAME}</h1>
            <p style="font-size:1.2em;">{SLOGAN}</p>
        </div>
    """, unsafe_allow_html=True)
    st.write("")
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 Status Gudang", "Ready Stock")
    c2.metric("⚡ Penawaran", "Otomatis")
    c3.metric("📄 Faktur", "Direct Drive")

elif menu == "📑 Portal Customer":
    st.title("📑 Layanan Mandiri Pelanggan")
    t_pajak, t_order = st.tabs(["🔍 Download Faktur Pajak", "📝 Request Penawaran Harga"])

    with t_pajak:
        c_l, c_r = st.columns([1, 1])
        with c_l:
            st.subheader("Cari Faktur")
            i_inv = st.text_input("Nomor Invoice", placeholder="Contoh: 260200977")
            i_name = st.text_input("Nama PT / Toko", placeholder="Nama terdaftar di Pajak")
            if st.button("🔍 Cari Sekarang"):
                res = search_pajak_file(i_inv, i_name)
                if res:
                    st.balloons(); pdf = download_drive_file(res['id'])
                    st.success(f"Ditemukan: {res['name']}")
                    st.download_button("📥 Download PDF", data=pdf, file_name=res['name'])
                else: st.error("Data tidak ditemukan. Cek kembali penulisan Anda.")
        with c_r:
            st.info("### Petunjuk\n1. Masukkan angka invoice saja.\n2. Nama PT harus sesuai dengan yang terdaftar.")

    with t_order:
        st.subheader("Pilih Item Barang")
        if 'cart' not in st.session_state: st.session_state.cart = []
        
        with st.container(border=True):
            col_a, col_b = st.columns([3, 1])
            sel = col_a.selectbox("Cari Barang:", ["-- Pilih --"] + df_barang['Nama Barang'].tolist())
            if col_b.button("➕ Tambah"):
                if sel != "-- Pilih --" and sel not in st.session_state.cart:
                    st.session_state.cart.append(sel); st.rerun()

        if st.session_state.cart:
            final_req = []
            st.write("### Keranjang Anda")
            for item in st.session_state.cart:
                with st.container(border=True):
                    cl1, cl2, cl3 = st.columns([3, 1, 0.5])
                    cl1.write(f"**{item}**")
                    qty = cl2.number_input("Qty", min_value=1, key=f"q_{item}")
                    if cl3.button("🗑️", key=f"d_{item}"):
                        st.session_state.cart.remove(item); st.rerun()
                    b_data = df_barang[df_barang['Nama Barang'] == item].iloc[0]
                    final_req.append({"Nama Barang": item, "Qty": qty, "Harga": b_data['Harga'], "Satuan": b_data['Satuan']})
            
            with st.expander("Isi Data Pengiriman"):
                c_n = st.text_input("Nama Perusahaan / Toko")
                c_p = st.text_input("Nama UP (PIC)")
                c_w = st.text_input("Nomor WhatsApp")
                if st.button("🚀 Kirim Request Penawaran"):
                    sheet = connect_gsheet()
                    if sheet and c_n:
                        sheet.append_row([datetime.now().strftime("%Y-%m-%d"), c_n, c_p, c_w, str(final_req), "Pending"])
                        st.success("Terkirim! Admin akan segera memproses."); st.session_state.cart = []

elif menu == "🔒 Admin Dashboard":
    st.title("🔒 Admin Panel")
    in_pass = st.sidebar.text_input("Password:", type="password")
    if in_pass == ADMIN_PASSWORD:
        sheet = connect_gsheet()
        if sheet:
            vals = sheet.get_all_values()
            if len(vals) > 1:
                df_gs = pd.DataFrame(vals[1:], columns=vals[0])
                pnd = df_gs[df_gs['Status'] == 'Pending']
                for i, row in pnd.iterrows():
                    with st.expander(f"🛒 Order: {row['Customer']}"):
                        items = ast.literal_eval(row['Pesanan'])
                        updated = []
                        st.write("--- Edit Item ---")
                        for idx, itm in enumerate(items):
                            c1, c2, c3, c4 = st.columns([3, 1, 1, 0.5])
                            c1.write(itm['Nama Barang'])
                            nq = c2.number_input("Qty", value=int(itm['Qty']), key=f"admin_q_{i}_{idx}")
                            nh = c3.number_input("Harga", value=float(itm['Harga']), key=f"admin_h_{i}_{idx}")
                            if not c4.checkbox("Hapus", key=f"admin_del_{i}_{idx}"):
                                updated.append({"Nama Barang": itm['Nama Barang'], "Qty": nq, "Harga": nh, "Satuan": itm['Satuan'], "Total_Row": nq * nh})
                        
                        st.write("--- Tambah Barang ---")
                        add_b = st.multiselect("Tambah barang lain:", df_barang['Nama Barang'].tolist(), key=f"add_b_{i}")
                        for ab in add_b:
                            rb = df_barang[df_barang['Nama Barang'] == ab].iloc[0]
                            aq = st.number_input(f"Qty {ab}", min_value=1, key=f"aq_{i}_{ab}")
                            updated.append({"Nama Barang": ab, "Qty": aq, "Harga": rb['Harga'], "Satuan": rb['Satuan'], "Total_Row": aq * rb['Harga']})

                        if st.button("💾 Simpan & Update", key=f"save_{i}"):
                            sheet.update_cell(i+2, 5, str(updated)); st.rerun()

                        if updated:
                            df_f = pd.DataFrame(updated)
                            sub = df_f['Total_Row'].sum(); ppn = sub * 0.11; gt = sub + ppn
                            nos = st.text_input("No Surat:", value=".../S-TTS/II/2026", key=f"nos_{i}")
                            pdf_gen = generate_pdf(nos, row['Customer'], row['UP'], df_f, sub, ppn, gt)
                            st.download_button("📩 Download PDF Penawaran", data=pdf_gen, file_name=f"Penawaran_{row['Customer']}.pdf", key=f"dl_{i}")
                            if st.button("✅ Tandai Selesai", key=f"fin_{i}"):
                                sheet.update_cell(i+2, 6, "Processed"); st.rerun()
            else: st.info("Tidak ada antrean pending.")
    else: st.warning("Masukkan password admin yang benar di sidebar.")

st.markdown('<div class="footer">© 2026 PT. THEA THEO STATIONARY - Internal System v5.0</div>', unsafe_allow_html=True)
