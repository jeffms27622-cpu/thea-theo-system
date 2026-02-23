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

COMPANY_NAME    = "PT. THEA THEO STATIONARY"
SLOGAN          = "Supplier Alat Tulis Kantor & Sekolah"
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

# =========================================================
# 3. PDF ENGINE (PROFESSIONAL NAVY)
# =========================================================
class PenawaranPDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 10, 30)
            self.set_x(45)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.cell(0, 8, COMPANY_NAME, ln=1)
        self.set_x(45)
        self.set_font('Arial', '', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, SLOGAN, ln=1)
        self.set_x(45)
        self.cell(0, 5, ADDR, ln=1)
        self.set_x(45)
        self.cell(0, 5, f"Telp: {OFFICE_PHONE}", ln=1)
        self.set_y(12)
        self.set_font('Arial', '', 8)
        self.set_text_color(0, 0, 0)
        self.cell(0, 4, f"WhatsApp: {MARKETING_WA}", ln=1, align='R')
        self.cell(0, 4, f"Email: {MARKETING_EMAIL}", ln=1, align='R')
        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.8)
        self.line(10, 40, 200, 40)
        self.ln(22)

def generate_pdf(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    pdf = PenawaranPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 7, "SURAT PENAWARAN HARGA", ln=1, align='C')
    pdf.ln(5)
    waktu_jkt = datetime.utcnow() + timedelta(hours=7)
    tgl_skrg = waktu_jkt.strftime('%d %B %Y')
    pdf.set_font('Arial', '', 10)
    pdf.cell(95, 6, f"No Surat : {no_surat}", ln=0)
    pdf.cell(95, 6, f"Tanggal : {tgl_skrg}", ln=1, align='R')
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "Kepada Yth,", ln=1)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 6, str(nama_cust).upper(), ln=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f"Up. {pic}", ln=1)
    pdf.ln(8)
    # Header Tabel
    pdf.set_fill_color(0, 51, 102); pdf.set_text_color(255, 255, 255)
    pdf.cell(10, 10, 'NO', 1, 0, 'C', True); pdf.cell(85, 10, 'NAMA BARANG', 1, 0, 'C', True)
    pdf.cell(20, 10, 'QTY', 1, 0, 'C', True); pdf.cell(20, 10, 'SATUAN', 1, 0, 'C', True)
    pdf.cell(25, 10, 'HARGA', 1, 0, 'C', True); pdf.cell(30, 10, 'TOTAL', 1, 1, 'C', True)
    # Isi Tabel
    pdf.set_font('Arial', '', 9); pdf.set_text_color(0, 0, 0)
    fill = False
    for i, row in df_order.iterrows():
        pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(10, 8, str(i+1), 1, 0, 'C', True); pdf.cell(85, 8, f" {row['Nama Barang']}", 1, 0, 'L', True)
        pdf.cell(20, 8, str(int(row['Qty'])), 1, 0, 'C', True); pdf.cell(20, 8, str(row['Satuan']), 1, 0, 'C', True)
        pdf.cell(25, 8, f"{row['Harga']:,.0f} ", 1, 0, 'R', True); pdf.cell(30, 8, f"{row['Total_Row']:,.0f} ", 1, 1, 'R', True)
        fill = not fill
    # Total
    pdf.ln(2); pdf.set_font('Arial', 'B', 10)
    pdf.cell(160, 8, "Sub Total", 0, 0, 'R'); pdf.cell(30, 8, f" {subtotal:,.0f}", 1, 1, 'R')
    pdf.cell(160, 8, "PPN 11%", 0, 0, 'R'); pdf.cell(30, 8, f" {ppn:,.0f}", 1, 1, 'R')
    pdf.set_fill_color(0, 51, 102); pdf.set_text_color(255, 255, 255)
    pdf.cell(160, 10, "GRAND TOTAL  ", 0, 0, 'R'); pdf.cell(30, 10, f" {grand_total:,.0f}", 1, 1, 'R', True)
    pdf.ln(10); pdf.set_font('Arial', 'I', 8); pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "* Dokumen otomatis sistem TTS. Sah tanpa tanda tangan basah.")
    pdf.ln(10); pdf.set_font('Arial', 'B', 11); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, "Hormat Kami,", ln=1); pdf.ln(15); pdf.cell(0, 6, MARKETING_NAME, ln=1)
    pdf.set_font('Arial', '', 10); pdf.cell(0, 5, "Sales Consultant", ln=1)
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# 4. DASHBOARD UTAMA
# =========================================================
st.sidebar.title(f"Portal {MARKETING_NAME}")
menu = st.sidebar.selectbox("Pilih Menu:", ["🏠 Home", "📝 Portal Customer", "👨‍💻 Admin Dashboard"])

if menu == "👨‍💻 Admin Dashboard":
    st.title("Admin Dashboard - PT TTS")
    pwd = st.sidebar.text_input("Password:", type="password")
    
    if pwd == ADMIN_PASSWORD:
        sheet = connect_gsheet()
        if sheet:
            # BAGIAN TAB (PEMISAH TUGAS)
            tab_sales, tab_admin = st.tabs(["🛠️ 1. Edit Harga (Pak Asin)", "📦 2. Cetak PDF (Admin)"])
            
            all_vals = sheet.get_all_values()
            df_gs = pd.DataFrame(all_vals[1:], columns=all_vals[0]) if len(all_vals) > 1 else pd.DataFrame()
            pending = df_gs[(df_gs['Status'] == 'Pending') & (df_gs['Sales'] == MARKETING_NAME)]

            with tab_sales:
                st.subheader("Tugas Pak Asin: Negosiasi & Update Barang")
                if pending.empty: st.info("Tidak ada penawaran yang perlu diedit.")
                for idx, row in pending.iterrows():
                    real_row_idx = df_gs.index[idx] + 2
                    with st.expander(f"📝 EDIT HARGA: {row['Customer']}", expanded=False):
                        items = ast.literal_eval(str(row['Pesanan']))
                        new_items = []
                        for i, r in enumerate(items):
                            c1, c2, c3, c4 = st.columns([3, 1, 1, 1.5])
                            c1.markdown(f"**{r['Nama Barang']}**")
                            nq = c2.number_input("Qty", value=int(r['Qty']), key=f"s_q_{idx}_{i}")
                            ns = c3.text_input("Satuan", value=r['Satuan'], key=f"s_s_{idx}_{i}")
                            nh = c4.number_input("Harga Nego", value=float(r['Harga']), key=f"s_h_{idx}_{i}")
                            new_items.append({"Nama Barang": r['Nama Barang'], "Qty": nq, "Harga": nh, "Satuan": ns, "Total_Row": nq * nh})
                        
                        if st.button("💾 Simpan Perubahan Nego", key=f"btn_s_{idx}"):
                            sheet.update_cell(real_row_idx, 5, str(new_items))
                            st.success(f"Harga {row['Customer']} berhasil diupdate! Beritahu Admin untuk cetak."); st.rerun()

            with tab_admin:
                st.subheader("Tugas Admin: Penomoran & Download PDF")
                if pending.empty: st.info("Belum ada data siap cetak.")
                for idx, row in pending.iterrows():
                    real_row_idx = df_gs.index[idx] + 2
                    with st.expander(f"🖨️ CETAK: {row['Customer']}", expanded=True):
                        items = ast.literal_eval(str(row['Pesanan']))
                        df_final = pd.DataFrame(items)
                        subt = df_final['Total_Row'].sum()
                        tax, gtot = subt * 0.11, subt * 1.11
                        
                        st.write(f"**Total Penawaran:** Rp {gtot:,.0f}")
                        no_s = st.text_input("Masukkan Nomor Surat:", value=f"..../S-TTS/II/{datetime.now().year}", key=f"no_ad_{idx}")
                        
                        col_a, col_b = st.columns(2)
                        pdf_file = generate_pdf(no_s, row['Customer'], row['UP'], df_final, subt, tax, gtot)
                        col_a.download_button("📩 Download PDF", data=pdf_file, file_name=f"Penawaran_{row['Customer']}.pdf", key=f"dl_ad_{idx}")
                        
                        if col_b.button("✅ Selesai (Hapus Antrean)", key=f"fin_ad_{idx}"):
                            sheet.update_cell(real_row_idx, 6, "Processed")
                            st.success("Berhasil diproses!"); st.rerun()

# --- Sisa Menu Home & Portal (Tetap Sama) ---
elif menu == "🏠 Home":
    st.title(f"Selamat Datang di {COMPANY_NAME}")
    st.info(f"Marketing: {MARKETING_NAME}")

elif menu == "📝 Portal Customer":
    # (Kode Portal Customer Bapak yang lama tetap di sini agar customer bisa input)
    st.write("Silakan input pesanan baru di sini...")
    # ... (Gunakan kode Portal Customer dari versi sebelumnya)
