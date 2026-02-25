import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
import gspread
from google.oauth2.service_account import Credentials

# --- KONFIGURASI HALAMAN WEB ---
st.set_page_config(page_title="Sistem Penawaran TTS", layout="wide")

# --- WARNA TEMA (NAVY & GOLD) ---
COLOR_NAVY = (0, 40, 85)
COLOR_GOLD = (184, 134, 11)
COLOR_TEXT = (40, 40, 40)

# --- DATANYA PAK ASIN (PATEN) ---
MARKETING_NAME = "ASIN"
MARKETING_PHONE = "0815-8199-775"
OFFICE_PHONE = "(021) 55780659"
EMAIL_OFFICE = "alattullis.tts@gmail.com"
OFFICE_ADDRESS = "Ruko Modernland Blok AR NO 27 Cipondoh Tangerang" # Sesuaikan jika perlu

# --- KONEKSI GOOGLE SHEETS (ANTREAN) ---
def get_google_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open("Antrean Penawaran TTS").sheet1
    except Exception as e:
        st.error(f"Koneksi GSheet Gagal: {e}")
        return None

# --- FUNGSI BACA DATABASE (ANTI-ERROR) ---
def load_db():
    if os.path.exists("database_barang.xlsx"):
        try:
            df = pd.read_excel("database_barang.xlsx")
            df.columns = df.columns.str.strip() # Bersihkan spasi nama kolom
            
            # Kita hanya ambil kolom penting agar tidak error kalau ada kolom 'Kategori'
            needed_cols = ['Nama Barang', 'Harga', 'Satuan']
            if all(col in df.columns for col in needed_cols):
                # Ambil hanya kolom yang dibutuhkan, abaikan sisanya
                df_final = df[needed_cols].copy()
                df_final['Harga'] = pd.to_numeric(df_final['Harga'], errors='coerce').fillna(0)
                return df_final
            else:
                st.error("Kolom di Excel tidak lengkap! Wajib ada: Nama Barang, Harga, Satuan")
        except Exception as e:
            st.error(f"Error membaca database: {e}")
    return pd.DataFrame(columns=['Nama Barang', 'Harga', 'Satuan'])

# --- KELAS PDF (FORMAT SURAT PENAWARAN) ---
class PenawaranPDF(FPDF):
    def header(self):
        # 1. LOGO (Kiri Atas)
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 25)
        
        # 2. NAMA PERUSAHAAN (Navy Besar)
        self.set_y(10)
        self.set_x(38)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(*COLOR_NAVY)
        self.cell(0, 8, 'PT. THEA THEO STATIONARY', ln=1)
        
        # 3. SLOGAN (Gold Miring)
        self.set_x(38)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(*COLOR_GOLD)
        self.cell(0, 5, 'Premium Office & School Supplies Solution', ln=1)
        
        # 4. KONTAK INFO (Kanan Atas - Rapi)
        self.set_y(9)
        self.set_font('Arial', '', 7)
        self.set_text_color(80, 80, 80)
        self.cell(0, 4, OFFICE_ADDRESS, ln=1, align='R')
        self.cell(0, 4, f'Telp: {OFFICE_PHONE} | Email: {EMAIL_OFFICE}', ln=1, align='R')
        
        # Info Marketing (Pak Asin) - Bold Navy
        self.set_font('Arial', 'B', 8)
        self.set_text_color(*COLOR_NAVY)
        self.cell(0, 4, f'Contact Person: {MARKETING_NAME} ({MARKETING_PHONE})', ln=1, align='R')

        # 5. GARIS MEWAH (Pemisah Header)
        self.ln(3)
        y_now = self.get_y()
        self.set_fill_color(*COLOR_NAVY) # Garis Tebal Navy
        self.rect(10, y_now, 190, 1.5, 'F')
        self.set_fill_color(*COLOR_GOLD) # Garis Tipis Gold
        self.rect(10, y_now + 1.5, 190, 0.5, 'F')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Halaman {self.page_no()} | PT. THEA THEO STATIONARY - Official Document', 0, 0, 'C')

# --- FUNGSI GENERATE PDF ---
def generate_pdf(customer_name, items_df, perihal):
    pdf = PenawaranPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # Tanggal & Info Customer
    pdf.set_y(40)
    pdf.set_font('Arial', '', 10); pdf.set_text_color(0, 0, 0)
    tanggal = datetime.now().strftime("%d %B %Y")
    pdf.cell(0, 5, f"Tangerang, {tanggal}", ln=1, align='R')
    
    pdf.ln(5)
    pdf.cell(0, 5, "Kepada Yth,", ln=1)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 5, customer_name.upper(), ln=1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, "Di Tempat", ln=1)
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(20, 5, "Perihal:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 5, perihal, ln=1)
    
    pdf.ln(5)
    pdf.multi_cell(0, 5, "Dengan hormat,\nBersama ini kami sampaikan penawaran harga untuk kebutuhan ATK & Perlengkapan Kantor sebagai berikut:")
    pdf.ln(5)
    
    # --- TABEL HARGA (Style Navy) ---
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(*COLOR_NAVY)
    pdf.set_text_color(255, 255, 255)
    
    # Header Tabel
    pdf.cell(10, 8, "NO", 1, 0, 'C', True)
    pdf.cell(90, 8, "NAMA BARANG", 1, 0, 'L', True)
    pdf.cell(25, 8, "SATUAN", 1, 0, 'C', True)
    pdf.cell(35, 8, "HARGA", 1, 0, 'C', True)
    pdf.cell(30, 8, "TOTAL", 1, 1, 'C', True)
    
    # Isi Tabel
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(0, 0, 0)
    
    total_grand = 0
    no = 1
    
    for _, row in items_df.iterrows():
        nama = row['Nama Barang']
        satuan = row['Satuan']
        qty = row['Qty']
        harga = row['Harga']
        subtotal = qty * harga
        total_grand += subtotal
        
        # Zebra Striping (Baris selang seling)
        bg_color = (245, 245, 245) if no % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg_color)
        
        pdf.cell(10, 7, str(no), 1, 0, 'C', True)
        pdf.cell(90, 7, f" {nama}", 1, 0, 'L', True) # Spasi dikit biar ga nempel garis
        pdf.cell(25, 7, f"{qty} {satuan}", 1, 0, 'C', True)
        pdf.cell(35, 7, f"Rp {harga:,.0f}", 1, 0, 'R', True)
        pdf.cell(30, 7, f"Rp {subtotal:,.0f}", 1, 1, 'R', True)
        no += 1
        
    # Total Grand
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(160, 8, "GRAND TOTAL", 1, 0, 'R')
    pdf.set_text_color(*COLOR_NAVY)
    pdf.cell(30, 8, f"Rp {total_grand:,.0f}", 1, 1, 'R')
    
    # Penutup & Tanda Tangan
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, "Demikian penawaran ini kami sampaikan. Harga dapat berubah sewaktu-waktu tanpa pemberitahuan sebelumnya. Atas perhatian dan kerjasamanya kami ucapkan terima kasih.")
    
    pdf.ln(10)
    pdf.cell(0, 5, "Hormat Kami,", ln=1)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 5, "PT. THEA THEO STATIONARY", ln=1)
    pdf.ln(25) # Spasi Tanda Tangan
    
    pdf.set_font('Arial', 'B', 10); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, f"({MARKETING_NAME})", ln=1)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 4, "Executive Sales Consultant", ln=1)
    pdf.cell(0, 4, f"WA: {MARKETING_PHONE}", ln=1)

    return pdf.output(dest='S').encode('latin-1')

# --- MAIN PROGRAM (STREAMLIT) ---
def main():
    st.title("💼 Sistem Penawaran TTS")
    st.caption(f"Logged in as: {MARKETING_NAME} | Mode: Executive Luxury")
    
    # Load Database
    df_barang = load_db()
    
    # Tabs Menu
    tab1, tab2 = st.tabs(["📝 Buat Penawaran", "📋 Antrean Admin"])
    
    # --- TAB 1: INPUT PENAWARAN ---
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            customer = st.text_input("Nama Customer / PT")
        with col2:
            perihal = st.text_input("Perihal", value="Penawaran Harga ATK")
            
        st.divider()
        
        # Keranjang Belanja (Session State)
        if 'keranjang' not in st.session_state:
            st.session_state.keranjang = []
            
        # Pilih Barang
        pilih_barang = st.selectbox("Pilih Barang", df_barang['Nama Barang'].unique())
        
        # Ambil detail barang yg dipilih
        detail = df_barang[df_barang['Nama Barang'] == pilih_barang].iloc[0]
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.info(f"Harga: Rp {detail['Harga']:,.0f} / {detail['Satuan']}")
        with c2:
            qty = st.number_input("Jumlah (Qty)", min_value=1, value=1)
        with c3:
            if st.button("➕ Tambah"):
                st.session_state.keranjang.append({
                    'Nama Barang': pilih_barang,
                    'Harga': detail['Harga'],
                    'Satuan': detail['Satuan'],
                    'Qty': qty
                })
                st.success("Masuk keranjang!")
                
        # Tabel Keranjang
        if st.session_state.keranjang:
            df_cart = pd.DataFrame(st.session_state.keranjang)
            st.dataframe(df_cart, use_container_width=True)
            
            if st.button("🖨️ GENERATE PDF & SIMPAN KE ANTREAN"):
                if customer:
                    # 1. Buat PDF
                    pdf_bytes = generate_pdf(customer, df_cart, perihal)
                    
                    # 2. Simpan ke GSheet
                    sheet = get_google_sheet()
                    if sheet:
                        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        data_row = [waktu, customer, perihal, MARKETING_NAME, str(len(df_cart)) + " Item", "Pending"]
                        sheet.append_row(data_row)
                    
                    # 3. Tombol Download
                    st.download_button(
                        label=f"📥 Download Penawaran_{customer}.pdf",
                        data=pdf_bytes,
                        file_name=f"Penawaran_TTS_{customer}.pdf",
                        mime='application/pdf'
                    )
                    
                    # 4. Reset
                    if st.button("Buat Baru (Reset)"):
                        st.session_state.keranjang = []
                        st.rerun()
                else:
                    st.warning("Isi nama customer dulu!")
            
            if st.button("Hapus Keranjang"):
                st.session_state.keranjang = []
                st.rerun()

    # --- TAB 2: DASHBOARD ADMIN (ANTREAN) ---
    with tab2:
        st.header("Monitor Antrean Pesanan")
        sheet = get_google_sheet()
        if sheet:
            try:
                data = sheet.get_all_records()
                if data:
                    df_antrean = pd.DataFrame(data)
                    st.dataframe(df_antrean)
                    
                    # Fitur Selesai (Update Status)
                    st.divider()
                    st.subheader("Update Status")
                    
                    # Trik agar index sesuai baris asli di GSheet (mulai baris 2 karena header)
                    for idx, row in df_antrean.iterrows():
                        if row['Status'] == "Pending":
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.text(f"{row['Customer']} - {row['Waktu']}")
                            with col_b:
                                # Hitung nomor baris asli di Google Sheet
                                # idx mulai dari 0, header baris 1, jadi data pertama baris 2
                                real_row_idx = idx + 2 
                                
                                if st.button("✅ Selesai", key=f"done_{idx}"):
                                    sheet.update_cell(real_row_idx, 6, "Processed")
                                    st.success("Status diupdate!")
                                    st.rerun()
                else:
                    st.info("Belum ada antrean.")
            except Exception as e:
                st.error(f"Error memuat data: {e}")

if __name__ == "__main__":
    main()
