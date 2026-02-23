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
SLOGAN          = "Partner Terpercaya Kebutuhan Kantor & Sekolah"
ADDR            = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
OFFICE_PHONE    = "(021) 55780659"

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
        clean_inv = re.sub(r'[^A-Z0-9]', '', inv_keyword.upper()) if inv_keyword else ""
        clean_name = re.sub(r'[^A-Z0-9]', '', name_keyword.upper()) if name_keyword else ""
        
        query = f"'{PAJAK_FOLDER_ID}' in parents and mimeType = 'application/pdf' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)", pageSize=1000).execute()
        files = results.get('files', [])
        
        for f in files:
            fname = re.sub(r'[^A-Z0-9]', '', f['name'].upper())
            match_inv = clean_inv in fname if clean_inv else True
            match_name = clean_name in fname if clean_name else True
            
            if match_inv and match_name:
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
# 3. DATABASE & PDF ENGINE (PROFESSIONAL LUXURY VERSION)
# =========================================================
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

class PenawaranPDF(FPDF):
    def header(self):
        # A. ORNAMEN GARIS ATAS (Header Bar)
        self.set_fill_color(0, 51, 102) # Navy Blue
        self.rect(0, 0, 210, 5, 'F') # Garis biru di paling atas kertas
        
        # B. LOGO
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 10, 30)
            self.set_x(45)
        else:
            self.set_x(10)

        # C. NAMA & ALAMAT (Lebih Rapi)
        self.set_y(12)
        self.set_x(45)
        self.set_font('Arial', 'B', 18)
        self.set_text_color(0, 51, 102)
        self.cell(0, 8, COMPANY_NAME, ln=1)
        
        self.set_x(45)
        self.set_font('Arial', 'I', 9) # Italic untuk Slogan
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, SLOGAN, ln=1)
        
        self.set_x(45)
        self.set_font('Arial', '', 9)
        self.cell(0, 5, f"{ADDR}", ln=1)
        self.set_x(45)
        self.cell(0, 5, f"Phone: {OFFICE_PHONE} | Email: {MARKETING_EMAIL}", ln=1)
        
        # D. GARIS PEMBATAS GANDA (Kesan Mahal)
        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.5)
        self.line(10, 42, 200, 42)
        self.set_line_width(0.1)
        self.line(10, 43, 200, 43)
        self.ln(20)

    def footer(self):
        # A. ORNAMEN BAWAH (Footer Bar)
        self.set_y(-25)
        self.set_fill_color(245, 245, 245) # Abu-abu sangat muda background footer
        self.rect(0, 272, 210, 25, 'F')
        
        # B. TEXT FOOTER
        self.set_y(-20)
        self.set_font('Arial', 'B', 8)
        self.set_text_color(0, 51, 102)
        self.cell(0, 4, COMPANY_NAME, 0, 1, 'C')
        
        self.set_font('Arial', '', 7)
        self.set_text_color(120, 120, 120)
        self.cell(0, 4, "Document generated automatically. Valid without wet signature.", 0, 1, 'C')
        self.cell(0, 4, f"Page {self.page_no()}", 0, 0, 'C')

def generate_pdf(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    pdf = PenawaranPDF()
    pdf.set_auto_page_break(auto=True, margin=30)
    pdf.add_page()
    
    # 1. JUDUL SURAT
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "PENAWARAN HARGA", ln=1, align='C')
    # Garis bawah judul
    pdf.set_line_width(0.2)
    width_title = pdf.get_string_width("PENAWARAN HARGA") + 10
    start_x = (210 - width_title) / 2
    pdf.line(start_x, pdf.get_y(), start_x + width_title, pdf.get_y())
    pdf.ln(5)
    
    # 2. INFO TANGGAL & NO SURAT
    pdf.set_font('Arial', '', 10)
    waktu_jkt = datetime.utcnow() + timedelta(hours=7)
    tgl_skrg = waktu_jkt.strftime('%d %B %Y')
    
    # Layout 2 Kolom (Kiri No Surat, Kanan Tanggal)
    pdf.cell(100, 6, f"Nomor   : {no_surat}", ln=0)
    pdf.cell(0, 6, f"Tanggal : {tgl_skrg}", ln=1, align='R')
    pdf.ln(5)
    
    # 3. KEPADA YTH
    pdf.set_fill_color(245, 245, 245) # Kotak abu-abu untuk area alamat
    pdf.rect(10, 65, 190, 25, 'F')
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "Kepada Yth.", ln=1)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 6, str(nama_cust).upper(), ln=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f"UP: {pic}", ln=1)
    pdf.cell(0, 6, f"Di Tempat", ln=1)
    
    pdf.ln(10)
    
    # 4. KATA PENGANTAR (Gaya Surat Bisnis Formal)
    pdf.multi_cell(0, 5, "Dengan hormat,\nBersama surat ini, kami mengajukan penawaran harga terbaik untuk kebutuhan perusahaan Bapak/Ibu sebagai berikut:")
    pdf.ln(5)
    
    # 5. HEADER TABEL (Modern & Mahal)
    pdf.set_fill_color(0, 51, 102) # Navy Blue
    pdf.set_text_color(255, 255, 255) # Putih
    pdf.set_font('Arial', 'B', 9)
    
    h = 8
    pdf.cell(10, h, 'NO', 1, 0, 'C', True)
    pdf.cell(85, h, 'NAMA BARANG', 1, 0, 'C', True)
    pdf.cell(20, h, 'QTY', 1, 0, 'C', True)
    pdf.cell(20, h, 'SAT', 1, 0, 'C', True)
    pdf.cell(25, h, 'HARGA (Rp)', 1, 0, 'C', True)
    pdf.cell(30, h, 'TOTAL (Rp)', 1, 1, 'C', True)

    # 6. ISI TABEL (Zebra Striping)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(0, 0, 0)
    
    fill = False
    for i, row in df_order.iterrows():
        # Zebra Warna
        if fill: pdf.set_fill_color(240, 248, 255) # AliceBlue (Biru Pucat)
        else: pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(10, 7, str(i+1), 'LRTB', 0, 'C', True)
        pdf.cell(85, 7, f" {row['Nama Barang']}", 'LRTB', 0, 'L', True)
        pdf.cell(20, 7, str(int(row['Qty'])), 'LRTB', 0, 'C', True)
        pdf.cell(20, 7, str(row['Satuan']), 'LRTB', 0, 'C', True)
        pdf.cell(25, 7, f"{row['Harga']:,.0f} ", 'LRTB', 0, 'R', True)
        pdf.cell(30, 7, f"{row['Total_Row']:,.0f} ", 'LRTB', 1, 'R', True)
        fill = not fill

    # 7. TOTAL SECTION (Kotak Khusus)
    pdf.ln(5)
    
    # Hitung Lebar Kotak Total
    start_x_total = 120
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(110, 8, "SUB TOTAL", 0, 0, 'R')
    pdf.cell(50, 8, f"Rp {subtotal:,.0f}", 1, 1, 'R')
    
    pdf.cell(110, 8, "PPN 11%", 0, 0, 'R')
    pdf.cell(50, 8, f"Rp {ppn:,.0f}", 1, 1, 'R')
    
    # Grand Total Biru
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(110, 10, "GRAND TOTAL  ", 0, 0, 'R')
    pdf.cell(50, 10, f"Rp {grand_total:,.0f}", 1, 1, 'R', True)

    # 8. TERMS & CONDITIONS (Penting untuk Profesional)
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 5, "SYARAT & KETENTUAN:", ln=1)
    
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 4, "1. Harga diatas sudah termasuk PPN 11%.\n2. Pembayaran maksimal 14 hari setelah invoice diterima.\n3. Barang yang sudah dibeli tidak dapat ditukar/dikembalikan kecuali cacat produksi.\n4. Harga tidak mengikat dan dapat berubah sewaktu-waktu tanpa pemberitahuan.\n5. Penawaran ini berlaku selama 14 hari kerja.")
    
    # 9. PENUTUP & TANDA TANGAN ELEKTRONIK
    pdf.ln(5)
    
    # Layout 2 Kolom TTD (Kiri Kosong, Kanan TTD)
    y_ttd = pdf.get_y()
    
    pdf.set_xy(130, y_ttd)
    pdf.set_font('Arial', '', 10)
    pdf.cell(60, 5, "Hormat Kami,", ln=1, align='C')
    pdf.set_x(130)
    pdf.cell(60, 5, COMPANY_NAME, ln=1, align='C')
    
    # Ruang Tanda Tangan (bisa tambah gambar TTD.png kalau mau)
    pdf.ln(15)
    
    pdf.set_x(130)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 51, 102) # Biru Nama
    pdf.cell(60, 5, MARKETING_NAME, ln=1, align='C')
    
    pdf.set_x(130)
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(60, 5, "Sales Consultant", ln=1, align='C')
    
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
    
    # --- TAB 1: INPUT PESANAN ---
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

    # --- TAB 2: FAKTUR PAJAK ---
    with tab_pajak:
        st.subheader("Pencarian Faktur Pajak")
        st.caption("Cari berdasarkan Nomor Invoice atau Nama Perusahaan.")
        
        col_a, col_b = st.columns(2)
        in_inv = col_a.text_input("Nomor Invoice (Contoh: INV/...)")
        in_nama = col_b.text_input("Nama Perusahaan")
        
        if st.button("🔍 Cari Faktur di Drive"):
            if not in_inv and not in_nama:
                st.warning("Mohon isi salah satu kolom pencarian.")
            else:
                with st.spinner("Sedang mencari di Google Drive..."):
                    file_match = search_pajak_file(in_inv, in_nama)
                    if file_match:
                        st.success(f"Ditemukan: {file_match['name']}")
                        pdf_data = download_drive_file(file_match['id'])
                        st.download_button("📥 Download PDF Faktur", data=pdf_data, file_name=file_match['name'], use_container_width=True)
                    else:
                        st.error("❌ File tidak ditemukan. Pastikan nama/nomor benar.")

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
                                # Load Data dengan Safety Check
                                try:
                                    pesanan_str = str(row['Pesanan'])
                                    items_list = ast.literal_eval(pesanan_str) if pesanan_str != 'nan' else []
                                except: items_list = []
                                
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
                                    st.download_button("📩 Download PDF Penawaran Professional", data=pdf_b, file_name=f"TTS_{row['Customer']}.pdf", key=f"dl_a_{idx}")
                                    
                                    if st.button("✅ Selesai & Hapus dari Antrean", key=f"fin_a_{idx}"):
                                        sheet.update_cell(real_row_idx, 6, "Processed")
                                        st.success("Processed!"); st.rerun()
                    else: st.info(f"Antrean {MARKETING_NAME} kosong.")
            except Exception as e: st.error(f"Error detail: {e}")
