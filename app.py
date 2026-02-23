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
SLOGAN          = "Premium Office & School Supplies Solution"
ADDR            = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
OFFICE_PHONE    = "(021) 55780659"

PAJAK_FOLDER_ID = "19i_mLcu4VtV85NLwZY67zZTGwxBgdG1z"
ADMIN_PASSWORD  = st.secrets["ADMIN_PASSWORD"]

# Warna Tema Luxury
COLOR_NAVY = (0, 40, 85)
COLOR_GOLD = (184, 134, 11)
COLOR_TEXT = (40, 40, 40)

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
# 3. DATABASE & PDF ENGINE (EXECUTIVE LUXURY VERSION)
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

class PenawaranPDF(FPDF):
    def header(self):
        # Background Ornamen Atas (Navy Bar)
        self.set_fill_color(*COLOR_NAVY)
        self.rect(0, 0, 210, 40, 'F')
        
        # Logo
        if os.path.exists("logo.png"):
            self.image("logo.png", 12, 10, 25)
            self.set_x(45)
        
        # Header Info (Putih)
        self.set_y(10)
        self.set_x(45)
        self.set_font('Arial', 'B', 18)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, COMPANY_NAME, ln=1)
        
        self.set_x(45)
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, SLOGAN, ln=1)
        
        self.set_x(45)
        self.set_font('Arial', '', 8)
        self.cell(0, 4, f"{ADDR}", ln=1)
        self.set_x(45)
        self.cell(0, 4, f"Telp: {OFFICE_PHONE} | Email: {MARKETING_EMAIL}", ln=1)
        
        # Garis Emas di bawah Header
        self.set_fill_color(*COLOR_GOLD)
        self.rect(0, 40, 210, 2, 'F')
        self.ln(30)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()} | {COMPANY_NAME} Official Quotation", 0, 0, 'C')

def generate_pdf(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    pdf = PenawaranPDF()
    pdf.set_auto_page_break(auto=True, margin=35)
    pdf.add_page()
    
    # Judul Surat
    pdf.set_y(50)
    pdf.set_font('Arial', 'B', 22)
    pdf.set_text_color(*COLOR_NAVY)
    pdf.cell(0, 10, "QUOTATION", ln=1, align='R')
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Ref No: {no_surat}", ln=1, align='R')
    pdf.cell(0, 5, f"Date: {(datetime.utcnow() + timedelta(hours=7)).strftime('%d %B %Y')}", ln=1, align='R')
    pdf.ln(10)

    # Info Client (Box Modern)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, 75, 95, 30, 'F')
    pdf.set_xy(13, 78)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(*COLOR_GOLD)
    pdf.cell(0, 5, "PREPARED FOR:", ln=1)
    
    pdf.set_x(13)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.cell(0, 7, str(nama_cust).upper(), ln=1)
    
    pdf.set_x(13)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, f"Attn: {pic}", ln=1)
    
    pdf.set_y(115)
    
    # Header Tabel Luxury
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(*COLOR_NAVY)
    
    h = 10
    pdf.cell(10, h, 'NO', 0, 0, 'C', True)
    pdf.cell(90, h, 'DESCRIPTION', 0, 0, 'L', True)
    pdf.cell(20, h, 'QTY', 0, 0, 'C', True)
    pdf.cell(20, h, 'UNIT', 0, 0, 'C', True)
    pdf.cell(25, h, 'PRICE', 0, 0, 'C', True)
    pdf.cell(25, h, 'TOTAL', 0, 1, 'C', True)

    # Isi Tabel Zebra
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(*COLOR_TEXT)
    fill = False
    for i, row in df_order.iterrows():
        pdf.set_fill_color(248, 249, 250) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(10, 8, str(i+1), 0, 0, 'C', True)
        pdf.cell(90, 8, f" {row['Nama Barang']}", 0, 0, 'L', True)
        pdf.cell(20, 8, str(int(row['Qty'])), 0, 0, 'C', True)
        pdf.cell(20, 8, str(row['Satuan']), 0, 0, 'C', True)
        pdf.cell(25, 8, f"{row['Harga']:,.0f} ", 0, 0, 'R', True)
        pdf.cell(25, 8, f"{row['Total_Row']:,.0f} ", 0, 1, 'R', True)
        fill = not fill

    # Kalkulasi Akhir
    pdf.ln(5)
    pdf.set_x(135)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, "Sub Total", 0, 0, 'L'); pdf.cell(25, 8, f" {subtotal:,.0f}", 0, 1, 'R')
    pdf.set_x(135)
    pdf.cell(40, 8, "VAT (PPN 11%)", 0, 0, 'L'); pdf.cell(25, 8, f" {ppn:,.0f}", 0, 1, 'R')
    
    # Grand Total Bar
    pdf.set_x(130)
    pdf.set_fill_color(*COLOR_GOLD)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(65, 10, f" TOTAL : IDR {grand_total:,.0f} ", 0, 1, 'R', True)

    # Terms & Conditions Area
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(*COLOR_NAVY)
    pdf.cell(0, 5, "TERMS & CONDITIONS:", ln=1)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "1. Prices are subject to change with notice.\n2. Validity: 14 Days from the date of quotation.\n3. Delivery: Within 3 working days after PO confirmation.\n4. Payment: T/T or Bank Transfer.")

    # Signature Area
    pdf.ln(10)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.cell(130, 5, "", 0, 0)
    pdf.cell(60, 5, "Authorized Signature,", 0, 1, 'C')
    
    pdf.ln(15)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(*COLOR_NAVY)
    pdf.cell(130, 5, "", 0, 0)
    pdf.cell(60, 5, MARKETING_NAME.upper(), 0, 1, 'C')
    
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(130, 5, "", 0, 0)
    pdf.cell(60, 5, "Sales Consultant", 0, 1, 'C')
    
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
                                    st.download_button("📩 Download PDF Penawaran Luxury", data=pdf_b, file_name=f"TTS_{row['Customer']}.pdf", key=f"dl_a_{idx}")
                                    
                                    if st.button("✅ Selesai & Hapus dari Antrean", key=f"fin_a_{idx}"):
                                        sheet.update_cell(real_row_idx, 6, "Processed")
                                        st.success("Processed!"); st.rerun()
                    else: st.info(f"Antrean {MARKETING_NAME} kosong.")
            except Exception as e: st.error(f"Error detail: {e}")
