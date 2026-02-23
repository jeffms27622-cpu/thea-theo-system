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
# 1. KONFIGURASI UTAMA
# =========================================================
MARKETING_NAME  = "Asin"
MARKETING_WA    = "08158199775"
MARKETING_EMAIL = "alattulis.tts@gmail.com"

COMPANY_NAME    = "PT. THEA THEO STATIONARY"
SLOGAN          = "Supplier Alat Tulis Kantor & Sekolah"
ADDR            = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
OFFICE_PHONE    = "(021) 55780659"

ADMIN_PASSWORD  = st.secrets["ADMIN_PASSWORD"]

st.set_page_config(page_title=f"{COMPANY_NAME}", layout="wide")

# =========================================================
# 2. KONEKSI DATA
# =========================================================
def get_creds():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)

def connect_gsheet():
    try:
        client = gspread.authorize(get_creds())
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
# 3. PDF ENGINE (PROFESSIONAL NAVY)
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
    pdf.set_fill_color(0, 51, 102); pdf.set_text_color(255, 255, 255)
    pdf.cell(10, 10, 'NO', 1, 0, 'C', True); pdf.cell(85, 10, 'NAMA BARANG', 1, 0, 'C', True); pdf.cell(20, 10, 'QTY', 1, 0, 'C', True); pdf.cell(20, 10, 'SAT', 1, 0, 'C', True); pdf.cell(25, 10, 'HARGA', 1, 0, 'C', True); pdf.cell(30, 10, 'TOTAL', 1, 1, 'C', True)
    pdf.set_font('Arial', '', 9); pdf.set_text_color(0, 0, 0); fill = False
    for i, row in df_f.iterrows():
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(10, 8, str(i+1), 1, 0, 'C', True); pdf.cell(85, 8, f" {row['Nama Barang']}", 1, 0, 'L', True); pdf.cell(20, 8, str(int(row['Qty'])), 1, 0, 'C', True); pdf.cell(20, 8, str(row['Satuan']), 1, 0, 'C', True); pdf.cell(25, 8, f"{row['Harga']:,.0f} ", 1, 0, 'R', True); pdf.cell(30, 8, f"{row['Total_Row']:,.0f} ", 1, 1, 'R', True); fill = not fill
    pdf.ln(2); pdf.set_font('Arial', 'B', 10)
    pdf.cell(160, 8, "Sub Total", 0, 0, 'R'); pdf.cell(30, 8, f" {subt:,.0f}", 1, 1, 'R')
    pdf.cell(160, 8, "PPN 11%", 0, 0, 'R'); pdf.cell(30, 8, f" {tax:,.0f}", 1, 1, 'R')
    pdf.set_fill_color(0, 51, 102); pdf.set_text_color(255, 255, 255); pdf.cell(160, 10, "GRAND TOTAL  ", 0, 0, 'R'); pdf.cell(30, 10, f" {gtot:,.0f}", 1, 1, 'R', True)
    pdf.ln(10); pdf.set_font('Arial', 'I', 8); pdf.set_text_color(100, 100, 100); pdf.multi_cell(0, 4, "* Dokumen otomatis sistem TTS. Sah tanpa tanda tangan basah."); pdf.ln(10); pdf.set_font('Arial', 'B', 11); pdf.set_text_color(0, 0, 0); pdf.cell(0, 6, "Hormat Kami,", ln=1); pdf.ln(15); pdf.cell(0, 6, MARKETING_NAME, ln=1); pdf.set_font('Arial', '', 10); pdf.cell(0, 5, "Sales Consultant", ln=1)
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# 4. MENU APLIKASI
# =========================================================
st.sidebar.title("NAVIGASI TTS")
menu = st.sidebar.selectbox("Pilih Menu:", ["🏠 Home", "🛒 1. Input Staff", "🔐 2. Pak Asin (Nego)", "📄 3. Cetak Staff"])
sheet = connect_gsheet()

# --- MENU 1: HOME ---
if menu == "🏠 Home":
    st.title(f"Portal Penawaran {COMPANY_NAME}")
    st.info("Selamat bekerja! Gunakan menu di samping untuk memproses penawaran.")

# --- MENU 2: INPUT STAFF (SUDAH DIPERBAIKI) ---
elif menu == "🛒 1. Input Staff":
    st.header("Admin/Staff: Masukkan Pesanan Awal")
    if 'cart' not in st.session_state: st.session_state.cart = []
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        nama_t = c1.text_input("Nama Toko/Customer")
        up = c2.text_input("UP (Nama Penerima)")
        wa = c1.text_input("Nomor WhatsApp")
        barang_pilihan = st.multiselect("Pilih Barang dari Database:", options=df_barang['Nama Barang'].tolist())
        if st.button("Tambahkan ke Daftar"):
            for b in barang_pilihan:
                if b not in st.session_state.cart: st.session_state.cart.append(b)
            st.rerun()

    if st.session_state.cart:
        st.markdown("### 📋 Preview Pesanan")
        list_p = []
        for item in st.session_state.cart:
            # Ambil detail barang dari database
            rb = df_barang[df_barang['Nama Barang'] == item].iloc[0]
            with st.container(border=True):
                ca, cb, cc, cd, ce = st.columns([3, 1, 1, 1.2, 0.5])
                ca.markdown(f"**{item}**")
                cb.write(f"Sat: {rb['Satuan']}") # Menampilkan Satuan
                cc.write(f"Rp {rb['Harga']:,.0f}") # Menampilkan Harga Standar
                qty = cd.number_input("Jumlah (Qty)", min_value=1, value=1, key=f"staff_q_{item}")
                if ce.button("❌", key=f"staff_d_{item}"): 
                    st.session_state.cart.remove(item); st.rerun()
                
                list_p.append({
                    "Nama Barang": item, 
                    "Qty": qty, 
                    "Harga": float(rb['Harga']), 
                    "Satuan": rb['Satuan'], 
                    "Total_Row": qty * rb['Harga']
                })
        
        if st.button("🚀 Kirim ke Pak Asin", use_container_width=True):
            if sheet and nama_t:
                wkt = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")
                sheet.append_row([wkt, nama_t, up, wa, str(list_p), "Pending", MARKETING_NAME])
                st.success(f"Tersimpan! Silakan lapor ke Pak Asin untuk penawaran {nama_t}."); st.session_state.cart = []

# --- MENU 3: PAK ASIN (TETAP SAMA) ---
elif menu == "🔐 2. Pak Asin (Nego)":
    st.header("🔐 Bagian Pak Asin: Finalisasi Harga & Item")
    pwd = st.text_input("Password:", type="password")
    if pwd == ADMIN_PASSWORD:
        if sheet:
            all_v = sheet.get_all_values()
            df_g = pd.DataFrame(all_v[1:], columns=all_v[0]) if len(all_v) > 1 else pd.DataFrame()
            status_f = st.radio("Cek Data:", ["🆕 Baru (Pending)", "🔄 Siap Cetak (Ready)", "✅ Selesai (Processed)"], horizontal=True)
            f_val = "Pending"
            if "Ready" in status_f: f_val = "Ready"
            if "Processed" in status_f: f_val = "Processed"
            
            data_edit = df_g[df_g['Status'] == f_val]
            if data_edit.empty: st.info(f"Data {f_val} tidak ditemukan.")
            for idx, row in data_edit.iterrows():
                real_idx = df_g.index[idx] + 2
                with st.expander(f"🛠️ KELOLA: {row['Customer']}", expanded=(f_val == "Pending")):
                    items_asli = ast.literal_eval(str(row['Pesanan']))
                    
                    st.markdown("### ➕ Tambah Barang Baru:")
                    tambah_b = st.multiselect("Tambah barang yang belum ada:", options=df_barang['Nama Barang'].tolist(), key=f"pa_add_{idx}")
                    
                    combined = items_asli.copy()
                    for t in tambah_b:
                        if not any(d['Nama Barang'] == t for d in items_asli):
                            rb_t = df_barang[df_barang['Nama Barang'] == t].iloc[0]
                            combined.append({"Nama Barang": t, "Qty": 1, "Harga": float(rb_t['Harga']), "Satuan": str(rb_t['Satuan']), "Total_Row": float(rb_t['Harga'])})
                    
                    st.markdown("### 📋 Edit Harga & Qty:")
                    final_save = []
                    for i, r in enumerate(combined):
                        with st.container(border=True):
                            c1, c2, c3, c4 = st.columns([3, 0.8, 1, 1.2])
                            c1.markdown(f"**{r['Nama Barang']}**")
                            nq = c2.number_input("Qty", value=int(r['Qty']), key=f"pa_q_{idx}_{i}")
                            ns = c3.text_input("Sat", value=r['Satuan'], key=f"pa_s_{idx}_{i}")
                            nh = c4.number_input("Harga Nego", value=float(r['Harga']), key=f"pa_h_{idx}_{i}")
                            final_save.append({"Nama Barang": r['Nama Barang'], "Qty": nq, "Harga": nh, "Satuan": ns, "Total_Row": nq * nh})

                    if st.button("💾 SIMPAN FINAL", key=f"pa_sv_{idx}"):
                        sheet.update_cell(real_idx, 5, str(final_save))
                        sheet.update_cell(real_idx, 6, "Ready")
                        st.success("Berhasil! Admin bisa cetak di Menu 3."); st.rerun()

# --- MENU 4: CETAK STAFF ---
elif menu == "📄 3. Cetak Staff":
    st.header("📄 Admin: Download PDF")
    if sheet:
        all_v = sheet.get_all_values()
        df_g = pd.DataFrame(all_v[1:], columns=all_v[0]) if len(all_v) > 1 else pd.DataFrame()
        data_c = df_g[df_g['Status'] == 'Ready']
        if data_c.empty: st.warning("Menunggu finalisasi harga dari Pak Asin.")
        for idx, row in data_c.iterrows():
            real_idx = df_g.index[idx] + 2
            with st.expander(f"🖨️ CETAK: {row['Customer']}", expanded=True):
                itms = pd.DataFrame(ast.literal_eval(str(row['Pesanan'])))
                sb = itms['Total_Row'].sum(); tx, gt = sb * 0.11, sb * 1.11
                st.write(f"Total: **Rp {gt:,.0f}**")
                nosur = st.text_input("No Surat:", value=f"..../S-TTS/II/{datetime.now().year}", key=f"ad_no_{idx}")
                p_file = generate_pdf(nosur, row['Customer'], row['UP'], itms, sb, tx, gt)
                st.download_button("📩 Download PDF", data=p_file, file_name=f"TTS_{row['Customer']}.pdf", key=f"ad_dl_{idx}")
                if st.button("✅ Selesai", key=f"ad_ok_{idx}"):
                    sheet.update_cell(real_idx, 6, "Processed"); st.rerun()
