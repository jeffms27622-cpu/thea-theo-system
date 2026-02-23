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
# 1. KONFIGURASI UTAMA
# =========================================================
MARKETING_NAME  = "Asin"
MARKETING_WA    = "08158199775"
MARKETING_EMAIL = "alattulis.tts@gmail.com"

# --- DATA KANTOR ---
COMPANY_NAME    = "PT. THEA THEO STATIONARY"
SLOGAN          = "Supplier Alat Tulis Kantor & Sekolah"
ADDR            = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
OFFICE_PHONE    = "(021) 55780659" # <--- Tambahan Nomor Telepon Kantor

PAJAK_FOLDER_ID = "19i_mLcu4VtV85NLwZY67zZTGwxBgdG1z"
ADMIN_PASSWORD  = st.secrets["ADMIN_PASSWORD"]

st.set_page_config(page_title=f"{COMPANY_NAME} - {MARKETING_NAME}", layout="wide")

# =========================================================
# 2. KONEKSI GOOGLE SERVICES
# =========================================================
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

# =========================================================
# 3. DATABASE & PDF ENGINE (PROFESSIONAL VERSION)
# =========================================================
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

class LuxuryPDF(FPDF):
    def header(self):
        # 1. Top Banner (Deep Navy)
        self.set_fill_color(*COLOR_PRIMARY)
        self.rect(0, 0, 210, 40, 'F')
        
        # 2. Gold Accent Line
        self.set_fill_color(*COLOR_ACCENT)
        self.rect(0, 39, 210, 1.5, 'F') # Garis emas tipis di bawah navy
        
        # 3. Logo & Info
        if os.path.exists("logo.png"): 
            self.image("logo.png", 10, 5, 30)
            self.set_x(45)
        else:
            self.set_x(10)
            
        # Nama PT (Putih)
        self.set_y(10)
        self.set_x(45)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 18)
        self.cell(0, 8, COMPANY_NAME, ln=1)
        
        # Slogan (Emas Pucat)
        self.set_x(45)
        self.set_text_color(240, 230, 140) 
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, SLOGAN, ln=1)
        
        # Kontak (Putih)
        self.set_x(45)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', '', 8)
        self.cell(0, 4, f"{ADDR}", ln=1)
        self.set_x(45)
        self.cell(0, 4, f"P: {OFFICE_PHONE} | WA: {WA_MARKETING} | E: {EMAIL_MARKETING}", ln=1)
        self.ln(20)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', '', 8)
        self.set_text_color(128, 128, 128)
        # Garis tipis footer
        self.set_draw_color(200, 200, 200)
        self.line(10, 275, 200, 275)
        self.ln(2)
        self.cell(0, 4, f"{COMPANY_NAME} - Automated Document System", 0, 1, 'L')
        self.cell(0, 4, f"Page {self.page_no()}", 0, 0, 'R')

def generate_pdf(no_s, cust, pic, df_f, subt, tax, gtot):
    pdf = LuxuryPDF()
    pdf.set_auto_page_break(auto=True, margin=35)
    pdf.add_page()
    
    # --- JUDUL BESAR ---
    pdf.set_y(50)
    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.cell(0, 10, "PENAWARAN HARGA", ln=1, align='R')
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "QUOTATION", ln=1, align='R')
    
    # --- INFO KIRI (DATA CUSTOMER - KOTAK ABU) ---
    pdf.set_xy(10, 50)
    pdf.set_fill_color(*COLOR_BG_GRAY)
    pdf.rect(10, 50, 95, 30, 'F')
    
    pdf.set_xy(15, 55)
    pdf.set_font('Arial', 'B', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 4, "KEPADA YTH (BILL TO):", ln=1)
    
    pdf.set_x(15)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, str(cust).upper(), ln=1)
    
    pdf.set_x(15)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f"UP: {pic}", ln=1)
    
    # --- INFO KANAN (DETAIL SURAT) ---
    pdf.set_xy(120, 65)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(30, 6, "Nomor Surat", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f": {no_s}", 0, 1)
    
    pdf.set_x(120)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(30, 6, "Tanggal", 0, 0)
    pdf.set_font('Arial', '', 10)
    tgl = (datetime.utcnow() + timedelta(hours=7)).strftime('%d %B %Y')
    pdf.cell(0, 6, f": {tgl}", 0, 1)
    
    pdf.ln(20)
    
    # --- TABEL BARANG ---
    # Header Tabel
    pdf.set_fill_color(*COLOR_PRIMARY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_line_width(0.1)
    
    h = 10
    pdf.cell(10, h, '#', 0, 0, 'C', True)
    pdf.cell(85, h, 'DESKRIPSI BARANG', 0, 0, 'L', True)
    pdf.cell(20, h, 'QTY', 0, 0, 'C', True)
    pdf.cell(20, h, 'SAT', 0, 0, 'C', True)
    pdf.cell(25, h, 'HARGA', 0, 0, 'R', True)
    pdf.cell(30, h, 'TOTAL', 0, 1, 'R', True)
    
    # Isi Tabel
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(0, 0, 0)
    fill = False
    
    for i, row in df_f.iterrows():
        # Zebra Striping Halus
        if fill: pdf.set_fill_color(240, 248, 255) # AliceBlue
        else: pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(10, 9, str(i+1), 0, 0, 'C', True)
        pdf.cell(85, 9, f" {row['Nama Barang']}", 0, 0, 'L', True)
        pdf.cell(20, 9, str(int(row['Qty'])), 0, 0, 'C', True)
        pdf.cell(20, 9, str(row['Satuan']), 0, 0, 'C', True)
        pdf.cell(25, 9, f"{row['Harga']:,.0f} ", 0, 0, 'R', True)
        pdf.cell(30, 9, f"{row['Total_Row']:,.0f} ", 0, 1, 'R', True)
        
        # Garis tipis bawah per baris
        pdf.set_draw_color(230, 230, 230)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        fill = not fill

    pdf.ln(5)

    # --- TOTAL & NOTES ---
    y_start = pdf.get_y()
    
    # Kolom Kiri: Notes & Terms
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.cell(100, 5, "SYARAT & KETENTUAN:", ln=1)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(90, 4, "1. Harga sudah termasuk PPN 11%.\n2. Pembayaran maks 14 hari setelah invoice.\n3. Barang tidak dapat diretur kecuali cacat.\n4. Penawaran berlaku 14 hari.")
    
    # Kolom Kanan: Angka Total
    pdf.set_xy(110, y_start)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 8, "Sub Total", 0, 0, 'R')
    pdf.cell(40, 8, f"Rp {subt:,.0f}", 0, 1, 'R')
    
    pdf.set_x(110)
    pdf.cell(50, 8, "PPN (11%)", 0, 0, 'R')
    pdf.cell(40, 8, f"Rp {tax:,.0f}", 0, 1, 'R')
    
    # Grand Total (Kotak Navy)
    pdf.set_x(110)
    pdf.set_fill_color(*COLOR_PRIMARY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(50, 10, "GRAND TOTAL", 0, 0, 'R', True)
    pdf.cell(40, 10, f"Rp {gtot:,.0f}", 0, 1, 'R', True)
    
    # --- TANDA TANGAN ---
    pdf.ln(15)
    pdf.set_x(140)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(50, 5, "Hormat Kami,", 0, 1, 'C')
    pdf.ln(15)
    
    pdf.set_x(140)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(50, 5, MARKETING_NAME, 0, 1, 'C')
    pdf.set_x(140)
    pdf.set_font('Arial', '', 9)
    pdf.cell(50, 5, "Sales Consultant", 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# 4. UI UTAMA (SIDEBAR & MENU)
# =========================================================
st.sidebar.title(f"Portal {MARKETING_NAME}")
menu = st.sidebar.selectbox("Pilih Menu:", ["🏠 Home", "📝 Portal Customer", "👨‍💻 Admin Dashboard"])

if 'cart' not in st.session_state: st.session_state.cart = []

if menu == "🏠 Home":
    st.title(f"Selamat Datang di {COMPANY_NAME}")
    st.info(f"Marketing Aktif: {MARKETING_NAME}")

elif menu == "📝 Portal Customer":
    tab_order, tab_pajak = st.tabs(["🛒 Buat Penawaran Baru", "📄 Ambil Faktur Pajak"])
    with tab_order:
        st.subheader("Form Pengajuan Penawaran")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            nama_toko = col1.text_input("🏢 Nama Perusahaan / Toko")
            up_nama = col2.text_input("👤 Nama Penerima (UP)")
            wa_nomor = col1.text_input("📞 Nomor WhatsApp Pembeli")
            picks = st.multiselect("📦 Pilih Barang:", options=df_barang['Nama Barang'].tolist())
            if st.button("Tambahkan ke Keranjang"):
                for p in picks:
                    if p not in st.session_state.cart: st.session_state.cart.append(p)
                st.rerun()

        if st.session_state.cart:
            st.markdown("### 📋 Daftar Pesanan")
            list_pesanan = []
            for item in st.session_state.cart:
                row_b = df_barang[df_barang['Nama Barang'] == item].iloc[0]
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 1.5, 1, 0.5])
                    c1.markdown(f"**{item}**")
                    c2.markdown(f"Rp {row_b['Harga']:,.0f} / {row_b['Satuan']}")
                    qty = c3.number_input(f"Jumlah", min_value=1, value=1, key=f"q_c_{item}")
                    if c4.button("❌", key=f"del_c_{item}"):
                        st.session_state.cart.remove(item); st.rerun()
                    
                    list_pesanan.append({"Nama Barang": str(item), "Qty": int(qty), "Harga": float(row_b['Harga']), "Satuan": str(row_b['Satuan']), "Total_Row": float(qty * row_b['Harga'])})

            if st.button(f"🚀 Kirim Pengajuan ke {MARKETING_NAME}", use_container_width=True):
                sheet = connect_gsheet()
                if sheet and nama_toko:
                    wkt = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")
                    sheet.append_row([wkt, nama_toko, up_nama, wa_nomor, str(list_pesanan), "Pending", MARKETING_NAME])
                    st.success("Terkirim! Terima kasih."); st.session_state.cart = []

elif menu == "👨‍💻 Admin Dashboard":
    st.title(f"Admin Dashboard - {MARKETING_NAME}")
    pwd = st.sidebar.text_input("Password:", type="password")
    if pwd == ADMIN_PASSWORD:
        sheet = connect_gsheet()
        if sheet:
            try:
                all_vals = sheet.get_all_values()
                if len(all_vals) > 1:
                    df_gs = pd.DataFrame(all_vals[1:], columns=all_vals[0])
                    pending = df_gs[(df_gs['Status'] == 'Pending') & (df_gs['Sales'] == MARKETING_NAME)]
                    
                    if not pending.empty:
                        for idx, row in pending.iterrows():
                            real_row_idx = df_gs.index[idx] + 2 
                            
                            with st.expander(f"🛠️ KELOLA: {row['Customer']}", expanded=True):
                                items_list = ast.literal_eval(str(row['Pesanan']))
                                edited_items = []
                                
                                st.write("### 1. Edit Barang & Harga")
                                for i, r in enumerate(items_list):
                                    with st.container(border=True):
                                        ca, cb, cc, cd, ce = st.columns([3, 0.8, 1.2, 1.5, 0.5])
                                        ca.markdown(f"**{r['Nama Barang']}**")
                                        nq = cb.number_input("Qty", value=int(r['Qty']), key=f"q_a_{idx}_{i}")
                                        
                                        opsi_satuan = ["Pcs", "Roll", "Dus", "Pack", "Rim", "Box", "Lusin", "Unit", "Set", "Lembar", "Botol"]
                                        satuan_awal = r.get('Satuan', 'Pcs')
                                        if satuan_awal not in opsi_satuan: opsi_satuan.insert(0, satuan_awal)
                                        
                                        ns = cc.selectbox("Satuan", options=opsi_satuan, index=opsi_satuan.index(satuan_awal), key=f"s_a_{idx}_{i}")
                                        nh = cd.number_input("Harga/Unit", value=float(r['Harga']), key=f"h_a_{idx}_{i}")
                                        
                                        if not ce.checkbox("Hapus", key=f"d_a_{idx}_{i}"):
                                            edited_items.append({"Nama Barang": r['Nama Barang'], "Qty": nq, "Harga": nh, "Satuan": ns, "Total_Row": nq * nh})
                                
                                st.divider()
                                st.write("### 2. Tambah Barang Baru")
                                new_items = st.multiselect("Cari Barang Tambahan:", options=df_barang['Nama Barang'].tolist(), key=f"add_a_{idx}")
                                for p in new_items:
                                    rb = df_barang[df_barang['Nama Barang'] == p].iloc[0]
                                    edited_items.append({"Nama Barang": p, "Qty": 1, "Harga": float(rb['Harga']), "Satuan": str(rb['Satuan']), "Total_Row": float(1 * rb['Harga'])})

                                if st.button("💾 Simpan Perubahan ke GSheet", key=f"s_a_{idx}"):
                                    sheet.update_cell(real_row_idx, 5, str(edited_items))
                                    st.success("Data diupdate!"); st.rerun()

                                st.divider()
                                final_df = pd.DataFrame(edited_items)
                                if not final_df.empty:
                                    subt = final_df['Total_Row'].sum()
                                    tax = subt * 0.11
                                    gtot = subt + tax
                                    
                                    c1, c2 = st.columns(2)
                                    no_s = c1.text_input("No Surat:", value=f"..../S-TTS/II/{datetime.now().year}", key=f"no_a_{idx}")
                                    c2.metric("Total Baru (Inc. PPN)", f"Rp {gtot:,.0f}")
                                    
                                    pdf_b = generate_pdf(no_s, row['Customer'], row['UP'], final_df, subt, tax, gtot)
                                    st.download_button("📩 Download PDF Penawaran", data=pdf_b, file_name=f"TTS_{row['Customer']}.pdf", key=f"dl_a_{idx}")
                                    
                                    if st.button("✅ Selesai & Hapus dari Antrean", key=f"fin_a_{idx}"):
                                        sheet.update_cell(real_row_idx, 6, "Processed")
                                        st.success("Processed!"); st.rerun()
                    else: st.info(f"Antrean {MARKETING_NAME} kosong.")
            except Exception as e: st.error(f"Error detail: {e}")


