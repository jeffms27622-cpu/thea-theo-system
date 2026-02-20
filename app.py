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
# 1. KONFIGURASI SALES (GANTI NAMA INI UNTUK SETIAP LINK)
# =========================================================
SALES_OWNER = "Asin"  # Ganti jadi "Alex", "Topan", atau "Artini" saat deploy link baru
# =========================================================

COMPANY_NAME = "PT. THEA THEO STATIONARY"
SLOGAN = "Supplier Alat Tulis Kantor & Sekolah"
ADDR = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
CONTACT = "Ph: 021-55780659, WA: 08158199775 | email: alattulis.tts@gmail.com"
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
PAJAK_FOLDER_ID = '19i_mLcu4VtV85NLwZY67zZTGwxBgdG1z' 

st.set_page_config(page_title=f"{COMPANY_NAME} - {SALES_OWNER}", layout="wide")

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
    except Exception as e:
        st.error(f"Drive Error: {e}")
        return None

def download_drive_file(file_id):
    service = build('drive', 'v3', credentials=get_creds())
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
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
        # CEK APAKAH FILE logo.png ADA
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 25) # Ukuran logo 25mm
            self.set_x(38) # Geser teks agar tidak tertutup logo
        
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 51, 102)
        self.cell(80, 7, COMPANY_NAME, ln=0)
        
        self.set_font('Arial', '', 8)
        self.set_text_color(0, 0, 0)
        self.cell(0, 5, ADDR, ln=1, align='R')
        
        if os.path.exists("logo.png"): self.set_x(38)
        self.set_font('Arial', 'I', 9)
        self.cell(80, 5, SLOGAN, ln=0)
        
        self.set_font('Arial', '', 8)
        self.cell(0, 5, CONTACT, ln=1, align='R')
        self.line(10, 32, 200, 32) # Garis pembatas header
        self.ln(15)

def generate_pdf(no_surat, nama_cust, pic, sales_name, df_order, subtotal, ppn, grand_total):
    pdf = PenawaranPDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 10)
    waktu_jkt = datetime.utcnow() + timedelta(hours=7)
    tgl_skrg = waktu_jkt.strftime('%d %B %Y')
    
    pdf.cell(95, 6, f"No: {no_surat}", ln=0)
    pdf.cell(95, 6, f"Tangerang, {tgl_skrg}", ln=1, align='R')
    pdf.cell(0, 6, "Hal: Surat Penawaran Harga", ln=1)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "Kepada Yth,", ln=1)
    pdf.cell(0, 6, str(nama_cust), ln=1)
    pdf.cell(0, 6, f"Up. {pic}", ln=1)
    pdf.ln(5)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(10, 10, 'No', 1, 0, 'C', True)
    pdf.cell(85, 10, 'Nama Barang', 1, 0, 'C', True)
    pdf.cell(20, 10, 'Qty', 1, 0, 'C', True)
    pdf.cell(20, 10, 'Satuan', 1, 0, 'C', True)
    pdf.cell(25, 10, 'Harga', 1, 0, 'C', True)
    pdf.cell(30, 10, 'Total', 1, 1, 'C', True)

    pdf.set_font('Arial', '', 9)
    for i, row in df_order.iterrows():
        pdf.cell(10, 8, str(i+1), 1, 0, 'C')
        pdf.cell(85, 8, str(row['Nama Barang']), 1)
        pdf.cell(20, 8, str(int(row['Qty'])), 1, 0, 'C')
        pdf.cell(20, 8, str(row['Satuan']), 1, 0, 'C')
        pdf.cell(25, 8, f"{row['Harga']:,.0f}", 1, 0, 'R')
        pdf.cell(30, 8, f"{row['Total_Row']:,.0f}", 1, 1, 'R')

    pdf.ln(2); pdf.set_font('Arial', 'B', 10)
    pdf.cell(160, 8, "Sub Total", 0, 0, 'R')
    pdf.cell(30, 8, f"{subtotal:,.0f}", 1, 1, 'R')
    pdf.cell(160, 8, "PPN 11%", 0, 0, 'R')
    pdf.cell(30, 8, f"{ppn:,.0f}", 1, 1, 'R')
    pdf.cell(160, 8, "GRAND TOTAL", 0, 0, 'R')
    pdf.set_fill_color(255, 255, 0)
    pdf.cell(30, 8, f"{grand_total:,.0f}", 1, 1, 'R', True)
    
    pdf.ln(10); pdf.set_font('Arial', 'I', 8); pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "Dokumen ini diterbitkan secara otomatis oleh sistem PT. THEA THEO STATIONARY.\nSah dan valid tanpa tanda tangan basah.")
    
    pdf.set_text_color(0, 0, 0); pdf.ln(5); pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "Hormat Kami,", ln=1); pdf.ln(15); pdf.cell(0, 6, f"{sales_name}", ln=1)
    pdf.set_font('Arial', '', 9); pdf.cell(0, 5, "Sales Consultant", ln=1)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. LOGIKA MENU UTAMA ---
st.sidebar.title(f"Portal {SALES_OWNER}")
menu = st.sidebar.selectbox("Pilih Menu:", ["🏠 Home", "📝 Portal Customer", "👨‍💻 Admin Dashboard"])

if 'cart' not in st.session_state:
    st.session_state.cart = []

if menu == "🏠 Home":
    st.title(f"Selamat Datang di {COMPANY_NAME}")
    st.subheader(f"Sales Consultant: {SALES_OWNER}")
    st.write("Sistem Penawaran Otomatis & Portal Faktur Mandiri v4.7.1")

elif menu == "📝 Portal Customer":
    tab_order, tab_pajak = st.tabs(["🛒 Buat Penawaran Baru", "📄 Ambil Faktur Pajak"])

    with tab_order:
        st.subheader(f"Form Pengajuan Penawaran (Sales: {SALES_OWNER})")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            nama_toko = col1.text_input("🏢 Nama Perusahaan / Toko")
            up_nama = col2.text_input("👤 Nama Penerima (UP)")
            wa_nomor = col1.text_input("📞 Nomor WhatsApp")
            picks = st.multiselect("📦 Pilih Barang:", options=df_barang['Nama Barang'].tolist())
            if st.button("Tambahkan ke Keranjang"):
                for p in picks:
                    if p not in st.session_state.cart: st.session_state.cart.append(p)
                st.rerun()

        if st.session_state.cart:
            list_pesanan = []
            for item in st.session_state.cart:
                row_b = df_barang[df_barang['Nama Barang'] == item].iloc[0]
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 1.5, 1, 0.5])
                    c1.write(f"**{item}**")
                    c2.write(f"Harga: Rp {row_b['Harga']:,.0f} / {row_b['Satuan']}")
                    qty = c3.number_input(f"Jumlah", min_value=1, value=1, key=f"q_c_{item}")
                    if c4.button("❌", key=f"del_c_{item}"):
                        st.session_state.cart.remove(item); st.rerun()
                    list_pesanan.append({"Nama Barang": str(item), "Qty": int(qty), "Harga": float(row_b['Harga']), "Satuan": str(row_b['Satuan']), "Total_Row": float(qty * row_b['Harga'])})

            if st.button(f"🚀 Kirim Pengajuan ke {SALES_OWNER}", use_container_width=True):
                sheet = connect_gsheet()
                if sheet and nama_toko:
                    wkt = datetime.utcnow() + timedelta(hours=7)
                    # Menambahkan kolom G untuk nama Sales
                    sheet.append_row([wkt.strftime("%Y-%m-%d %H:%M"), nama_toko, up_nama, wa_nomor, str(list_pesanan), "Pending", SALES_OWNER])
                    st.success(f"Terkirim ke {SALES_OWNER}! Terima kasih."); st.session_state.cart = []

    with tab_pajak:
        st.subheader("Unduh Faktur Pajak Mandiri")
        with st.container(border=True):
            in_inv = st.text_input("Nomor Invoice:")
            in_nama = st.text_input("Nama Perusahaan:")
            if st.button("🔍 Cari Faktur"):
                file_match = search_pajak_file(in_inv, in_nama)
                if file_match:
                    pdf_data = download_drive_file(file_match['id'])
                    st.download_button(label="📥 Download PDF", data=pdf_data, file_name=file_match['name'], mime="application/pdf")
                else: st.error("❌ Data tidak ditemukan.")

elif menu == "👨‍💻 Admin Dashboard":
    st.title(f"Dashboard Admin - {SALES_OWNER}")
    pwd = st.sidebar.text_input("Password:", type="password")
    if pwd == ADMIN_PASSWORD:
        sheet = connect_gsheet()
        if sheet:
            try:
                all_vals = sheet.get_all_values()
                if len(all_vals) > 1:
                    # Menangani kolom G (Sales)
                    df_gs = pd.DataFrame(all_vals[1:], columns=all_vals[0])
                    # FILTER: Admin hanya melihat pesanan yang sesuai dengan SALES_OWNER link ini
                    pending = df_gs[(df_gs['Status'] == 'Pending') & (df_gs['Sales'] == SALES_OWNER)]
                    
                    if not pending.empty:
                        for idx, row in pending.iterrows():
                            real_row_idx = idx + 2
                            with st.expander(f"🛠️ MANAGE: {row['Customer']}"):
                                items_list = ast.literal_eval(str(row['Pesanan']))
                                edited_items = []
                                for i, r in enumerate(items_list):
                                    with st.container(border=True):
                                        ca, cb, cc, cd = st.columns([3, 1, 1.5, 0.5])
                                        ca.write(f"**{r['Nama Barang']}**")
                                        nq = cb.number_input(f"Qty", value=int(r['Qty']), key=f"q_a_{idx}_{i}")
                                        nh = cc.number_input(f"Harga Nego", value=float(r['Harga']), key=f"h_a_{idx}_{i}")
                                        if not cd.checkbox("Hapus", key=f"d_a_{idx}_{i}"):
                                            edited_items.append({"Nama Barang": r['Nama Barang'], "Qty": nq, "Harga": nh, "Satuan": r['Satuan'], "Total_Row": nq * nh})
                                
                                st.divider()
                                final_df = pd.DataFrame(edited_items)
                                if not final_df.empty:
                                    subt = final_df['Total_Row'].sum()
                                    tax = subt * 0.11
                                    gtot = subt + tax
                                    c1, c2 = st.columns(2)
                                    no_s = c1.text_input("No Surat:", value=f"..../S-TTS/II/{datetime.now().year}", key=f"no_a_{idx}")
                                    c2.metric("Total Baru", f"Rp {gtot:,.0f}")
                                    
                                    pdf_b = generate_pdf(no_s, row['Customer'], row['UP'], SALES_OWNER, final_df, subt, tax, gtot)
                                    st.download_button("📩 Download PDF Penawaran", data=pdf_b, file_name=f"TTS_{row['Customer']}.pdf", key=f"dl_a_{idx}")
                                    if st.button("✅ Selesai & Arsipkan", key=f"fin_a_{idx}"):
                                        sheet.update_cell(real_row_idx, 6, "Processed"); st.rerun()
                    else: st.info(f"Belum ada antrean untuk {SALES_OWNER}.")
            except Exception as e: st.error(f"Error: {e}")


