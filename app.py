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
# 1. KONFIGURASI
# =========================================================
MARKETING_NAME  = "Asin"
MARKETING_WA    = "08158199775"
MARKETING_EMAIL = "alattulis.tts@gmail.com"
COMPANY_NAME    = "PT. THEA THEO STATIONARY"
SLOGAN          = "Supplier Alat Tulis Kantor & Sekolah"
ADDR            = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
OFFICE_PHONE    = "(021) 55780659"
ADMIN_PASSWORD  = st.secrets["ADMIN_PASSWORD"]

st.set_page_config(page_title=f"Sistem TTS - {MARKETING_NAME}", layout="wide")

# =========================================================
# 2. KONEKSI & DATABASE
# =========================================================
def connect_gsheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
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
# 3. PDF ENGINE (NAVY BLUE - PROFESSIONAL)
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
    
    # Header Tabel
    pdf.set_fill_color(0, 51, 102); pdf.set_text_color(255, 255, 255)
    pdf.cell(10, 10, 'NO', 1, 0, 'C', True); pdf.cell(85, 10, 'NAMA BARANG', 1, 0, 'C', True); pdf.cell(20, 10, 'QTY', 1, 0, 'C', True); pdf.cell(20, 10, 'SAT', 1, 0, 'C', True); pdf.cell(25, 10, 'HARGA', 1, 0, 'C', True); pdf.cell(30, 10, 'TOTAL', 1, 1, 'C', True)
    
    # Isi Tabel
    pdf.set_font('Arial', '', 9); pdf.set_text_color(0, 0, 0); fill = False
    for i, row in df_f.iterrows():
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(10, 8, str(i+1), 1, 0, 'C', True); pdf.cell(85, 8, f" {row['Nama Barang']}", 1, 0, 'L', True); pdf.cell(20, 8, str(int(row['Qty'])), 1, 0, 'C', True); pdf.cell(20, 8, str(row['Satuan']), 1, 0, 'C', True); pdf.cell(25, 8, f"{row['Harga']:,.0f} ", 1, 0, 'R', True); pdf.cell(30, 8, f"{row['Total_Row']:,.0f} ", 1, 1, 'R', True); fill = not fill
    
    pdf.ln(2); pdf.set_font('Arial', 'B', 10)
    pdf.cell(160, 8, "Sub Total", 0, 0, 'R'); pdf.cell(30, 8, f" {subt:,.0f}", 1, 1, 'R')
    pdf.cell(160, 8, "PPN 11%", 0, 0, 'R'); pdf.cell(30, 8, f" {tax:,.0f}", 1, 1, 'R')
    pdf.set_fill_color(0, 51, 102); pdf.set_text_color(255, 255, 255); pdf.cell(160, 10, "GRAND TOTAL  ", 0, 0, 'R'); pdf.cell(30, 10, f" {gtot:,.0f}", 1, 1, 'R', True)
    
    # Footer Panjang
    pdf.ln(10); pdf.set_font('Arial', 'I', 8); pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "* Dokumen ini diterbitkan secara otomatis melalui sistem PT. THEA THEO STATIONARY.\n* Surat penawaran ini sah dan valid secara hukum tanpa memerlukan tanda tangan dan cap basah.\n* Segala informasi yang tertera dalam dokumen ini bersifat rahasia dan mengikat.")
    
    pdf.ln(10); pdf.set_font('Arial', 'B', 11); pdf.set_text_color(0, 0, 0); pdf.cell(0, 6, "Hormat Kami,", ln=1); pdf.ln(15); pdf.cell(0, 6, MARKETING_NAME, ln=1); pdf.set_font('Arial', '', 10); pdf.cell(0, 5, "Sales Consultant", ln=1)
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# 4. APLIKASI UTAMA (SIMPLE 2 MENU)
# =========================================================
st.sidebar.title("NAVIGASI UTAMA")
menu = st.sidebar.selectbox("Pilih Menu:", ["1. Input Pesanan Baru", "2. KELOLA & CETAK (Admin)"])
sheet = connect_gsheet()

# --- MENU 1: INPUT SEDERHANA (SIAPAPUN BISA) ---
if menu == "1. Input Pesanan Baru":
    st.header("🛒 Input Pesanan Baru")
    st.info("Masukkan data customer dan barang awal di sini.")
    
    if 'cart' not in st.session_state: st.session_state.cart = []
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        nama_t = c1.text_input("Nama Toko/Customer")
        up = c2.text_input("UP (Nama Penerima)")
        wa = c1.text_input("Nomor WA")
        # Tambah barang disini
        barang_pilihan = st.multiselect("Cari Barang:", options=df_barang['Nama Barang'].tolist())
        if st.button("➕ Tambahkan ke List"):
            for b in barang_pilihan:
                if b not in st.session_state.cart: st.session_state.cart.append(b)
            st.rerun()

    # Tampilan Cart Sederhana
    if st.session_state.cart:
        st.write("---")
        st.write("### Daftar Barang Sementara:")
        list_pesanan = []
        for item in st.session_state.cart:
            rb = df_barang[df_barang['Nama Barang'] == item].iloc[0]
            with st.container(border=True):
                ca, cb, cc, cd, ce = st.columns([3, 1, 1, 1, 0.5])
                ca.write(f"**{item}**")
                cb.write(f"Sat: {rb['Satuan']}")
                cc.write(f"Rp {rb['Harga']:,.0f}")
                qty = cd.number_input("Qty", min_value=1, value=1, key=f"q_{item}")
                if ce.button("❌", key=f"d_{item}"): st.session_state.cart.remove(item); st.rerun()
                list_pesanan.append({"Nama Barang": item, "Qty": qty, "Harga": float(rb['Harga']), "Satuan": rb['Satuan'], "Total_Row": qty * rb['Harga']})
        
        if st.button("✅ KIRIM KE ADMIN/DASHBOARD", use_container_width=True):
            if sheet and nama_t:
                wkt = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")
                sheet.append_row([wkt, nama_t, up, wa, str(list_pesanan), "Pending", MARKETING_NAME])
                st.success("Terkirim! Silakan proses di Menu 2."); st.session_state.cart = []

# --- MENU 2: DASHBOARD SAKTI (SEMUA JADI SATU) ---
elif menu == "2. KELOLA & CETAK (Admin)":
    st.header("🔐 Dashboard Pengelola")
    pwd = st.sidebar.text_input("Password Admin:", type="password")
    
    if pwd == ADMIN_PASSWORD:
        if sheet:
            all_data = sheet.get_all_values()
            df = pd.DataFrame(all_data[1:], columns=all_data[0]) if len(all_data) > 1 else pd.DataFrame()
            
            # Filter hanya punya 'Asin' biar gak kecampur
            df = df[df['Sales'] == MARKETING_NAME]
            
            # Pilihan Tampilan Sederhana
            filter_status = st.radio("Tampilkan Data:", ["Antrean Baru (Pending)", "Sudah Selesai/Arsip"], horizontal=True)
            status_key = "Pending" if "Pending" in filter_status else "Processed"
            
            df_show = df[df['Status'] == status_key]
            
            if df_show.empty:
                st.info("Tidak ada data.")
            
            for idx, row in df_show.iterrows():
                real_idx = df.index[idx] + 2
                
                # --- SATU KOTAK UNTUK SEMUA ---
                with st.expander(f"📄 {row['Customer']} ({row['Tanggal']})", expanded=(status_key=="Pending")):
                    
                    # 1. Ambil Data
                    try: 
                        pesanan_str = str(row['Pesanan'])
                        items = ast.literal_eval(pesanan_str) if pesanan_str != 'nan' else []
                    except: items = []
                    
                    # 2. FITUR TAMBAH BARANG (Langsung disini)
                    st.caption("Tambah Barang Baru:")
                    add_items = st.multiselect("Cari Barang:", options=df_barang['Nama Barang'].tolist(), key=f"add_{idx}")
                    
                    # Gabung barang lama + baru
                    current_items = items.copy()
                    for new_item in add_items:
                        if not any(x['Nama Barang'] == new_item for x in current_items):
                            rb = df_barang[df_barang['Nama Barang'] == new_item].iloc[0]
                            current_items.append({"Nama Barang": new_item, "Qty": 1, "Harga": float(rb['Harga']), "Satuan": str(rb['Satuan']), "Total_Row": float(rb['Harga'])})
                    
                    # 3. TABEL EDIT (Harga, Qty, Hapus)
                    final_items = []
                    for i, item in enumerate(current_items):
                        c1, c2, c3, c4, c5 = st.columns([3, 0.7, 0.8, 1.2, 0.5])
                        c1.write(f"**{item['Nama Barang']}**")
                        nq = c2.number_input("Qty", value=int(item['Qty']), key=f"q_{idx}_{i}")
                        ns = c3.text_input("Sat", value=item['Satuan'], key=f"s_{idx}_{i}")
                        nh = c4.number_input("Harga", value=float(item['Harga']), key=f"h_{idx}_{i}")
                        hapus = c5.checkbox("Hapus", key=f"del_{idx}_{i}")
                        
                        if not hapus:
                            final_items.append({"Nama Barang": item['Nama Barang'], "Qty": nq, "Harga": nh, "Satuan": ns, "Total_Row": nq * nh})
                    
                    st.divider()
                    
                    # 4. BAGIAN BAWAH: SIMPAN & CETAK (BERDAMPINGAN)
                    col_save, col_print = st.columns([1, 1])
                    
                    # Tombol Simpan
                    if col_save.button("💾 UPDATE DATA", key=f"save_{idx}"):
                        sheet.update_cell(real_idx, 5, str(final_items))
                        st.toast("Data berhasil disimpan!")
                        st.rerun()
                        
                    # Tombol Cetak (Langsung disini, gak usah pindah menu)
                    df_final = pd.DataFrame(final_items)
                    if not df_final.empty:
                        subtotal = df_final['Total_Row'].sum()
                        ppn = subtotal * 0.11
                        grand_total = subtotal + ppn
                        
                        col_print.write(f"**Total: Rp {grand_total:,.0f}**")
                        no_surat = col_print.text_input("No Surat:", value=f"..../S-TTS/II/{datetime.now().year}", key=f"no_{idx}")
                        
                        pdf_bytes = generate_pdf(no_surat, row['Customer'], row['UP'], df_final, subtotal, ppn, grand_total)
                        
                        col_print.download_button("📩 DOWNLOAD PDF", data=pdf_bytes, file_name=f"Penawaran_{row['Customer']}.pdf", key=f"dl_{idx}")
                        
                        if col_print.button("✅ SELESAI (Arsipkan)", key=f"done_{idx}"):
                            sheet.update_cell(real_idx, 6, "Processed") # Ubah status jadi Processed
                            st.success("Selesai! Data masuk arsip."); st.rerun()
    else:
        st.warning("Masukkan Password untuk mengakses dashboard ini.")
