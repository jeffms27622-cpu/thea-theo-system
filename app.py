import streamlit as st
import pandas as pd
import ast
from datetime import datetime
from fpdf import FPDF
import os

# --- 1. KONFIGURASI IDENTITAS ---
COMPANY_NAME = "PT. THEA THEO STATIONARY"
SLOGAN = "Supplier Alat Tulis Kantor & Sekolah"
ADDR = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
CONTACT = "Ph: 021-55780659, WA: 08158199775 | email: alattulis.tts@gmail.com"
ADMIN_PASSWORD = "tts123" 

st.set_page_config(page_title=COMPANY_NAME, layout="wide")

# --- 2. FUNGSI DATABASE ---
def load_db():
    if os.path.exists("database_barang.xlsx"):
        try:
            df = pd.read_excel("database_barang.xlsx")
            df.columns = df.columns.str.strip()
            return df
        except:
            return pd.DataFrame(columns=['Nama Barang', 'Harga', 'Satuan'])
    return pd.DataFrame(columns=['Nama Barang', 'Harga', 'Satuan'])

df_barang = load_db()

# --- 3. MESIN PDF ---
class PenawaranPDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 25)
            self.set_x(38)
        
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
        
        self.line(10, 28, 200, 28)
        self.ln(12)

def generate_pdf(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    pdf = PenawaranPDF()
    pdf.add_page()
    
    pdf.set_font('Arial', '', 10)
    tgl_skrg = datetime.now().strftime('%d %B %Y')
    
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
    pdf.set_font('Arial', 'B', 10)
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

    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(160, 8, "Sub Total", 0, 0, 'R')
    pdf.cell(30, 8, f"{subtotal:,.0f}", 1, 1, 'R')
    pdf.cell(160, 8, "PPN 11%", 0, 0, 'R')
    pdf.cell(30, 8, f"{ppn:,.0f}", 1, 1, 'R')
    pdf.cell(160, 8, "GRAND TOTAL", 0, 0, 'R')
    pdf.cell(30, 8, f"{grand_total:,.0f}", 1, 1, 'R')

    pdf.ln(10)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, "Atas perhatian dan kerja samanya kami ucapkan terima kasih.", ln=1)
    pdf.ln(5)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "Dokumen ini diterbitkan secara otomatis oleh sistem aplikasi PT. THEA THEO STATIONARY.\nSah dan valid tanpa tanda tangan basah karena telah diverifikasi secara elektronik.")
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "Hormat Kami,", ln=1)
    pdf.ln(15)
    pdf.cell(0, 6, "Asin", ln=1)
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, "Sales Consultant", ln=1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. NAVIGASI MENU ---
menu = st.sidebar.selectbox("Pilih Menu:", ["🏠 Home", "📝 Portal Customer", "👨‍💻 Admin Dashboard"])

if menu == "🏠 Home":
    st.title(f"Selamat Datang di {COMPANY_NAME}")
    if os.path.exists("logo.png"):
        st.image("logo.png", width=200)
    st.write("Gunakan menu di samping untuk membuat pengajuan penawaran harga.")

elif menu == "📝 Portal Customer":
    st.title("🛒 Form Pengajuan Penawaran")
    st.info("Pilih barang dan tentukan jumlahnya di bawah.")
    
    with st.form("main_form"):
        col1, col2 = st.columns(2)
        nama_toko = col1.text_input("🏢 Nama Perusahaan / Toko", placeholder="Contoh: PT. Maju Jaya")
        up_nama = col2.text_input("👤 Nama Penerima (UP)", placeholder="Contoh: Ibu Rizka")
        wa_nomor = col1.text_input("📞 Nomor WhatsApp", placeholder="0815xxxx")
        pilihan = st.multiselect("📦 Pilih Barang:", options=df_barang['Nama Barang'].tolist())
        submit_data = st.form_submit_button("Lanjut ke Pengaturan Jumlah")

    if pilihan:
        st.write("---")
        st.subheader("🔢 Masukkan Jumlah (Qty)")
        list_pesanan = []
        for b in pilihan:
            row_data = df_barang[df_barang['Nama Barang'] == b].iloc[0]
            c_nama, c_satuan, c_qty = st.columns([3, 1, 1])
            c_nama.write(f"**{b}**")
            c_satuan.write(f"Satuan: `{row_data['Satuan']}`") # MENAMPILKAN SATUAN BAKU
            qty = c_qty.number_input(f"Qty", min_value=1, value=1, key=f"q_{b}", label_visibility="collapsed")
            list_pesanan.append({"Barang": str(b), "Qty": int(qty)})
        
        if st.button("🚀 Kirim Pengajuan Sekarang", use_container_width=True):
            if not nama_toko:
                st.error("Nama Toko wajib diisi!")
            else:
                new_entry = pd.DataFrame([{
                    "Tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                    "Customer": str(nama_toko), "UP": str(up_nama), "WA": str(wa_nomor), 
                    "Pesanan": str(list_pesanan), "Status": "Pending"
                }])
                try:
                    if os.path.exists("antrean_penawaran.xlsx"):
                        old = pd.read_excel("antrean_penawaran.xlsx")
                        pd.concat([old, new_entry], ignore_index=True).to_excel("antrean_penawaran.xlsx", index=False)
                    else:
                        new_entry.to_excel("antrean_penawaran.xlsx", index=False)
                    st.success("✅ Terkirim! Pak Asin akan segera memproses penawaran Anda.")
                except:
                    st.error("Gagal mengirim. Pastikan file antrean tidak dibuka di Excel.")

elif menu == "👨‍💻 Admin Dashboard":
    st.title("Admin Dashboard")
    pwd = st.sidebar.text_input("Password Admin:", type="password")
    
    if pwd == ADMIN_PASSWORD:
        if os.path.exists("antrean_penawaran.xlsx"):
            df_q = pd.read_excel("antrean_penawaran.xlsx")
            pending = df_q[df_q['Status'] == 'Pending']
            
            if pending.empty:
                st.info("Belum ada antrean baru.")
            else:
                for i, row in pending.iterrows():
                    with st.expander(f"ANTREAN: {row['Customer']} ({row['Tanggal']})"):
                        try:
                            items_raw = ast.literal_eval(row['Pesanan'])
                            df_req = pd.DataFrame(items_raw)
                            df_f = pd.merge(df_req, df_barang, left_on="Barang", right_on="Nama Barang", how="left")
                            
                            if 'Nama Barang' not in df_f.columns:
                                df_f['Nama Barang'] = df_f['Barang']
                                
                            df_f['Qty'] = df_f['Qty'].astype(int)
                            df_f['Harga'] = df_f['Harga'].fillna(0).astype(float)
                            df_f['Total_Row'] = df_f['Qty'] * df_f['Harga']
                            
                            dpp = df_f['Total_Row'].sum()
                            tax = dpp * 0.11
                            total_akhir = dpp + tax
                            
                            st.table(df_f[['Nama Barang', 'Qty', 'Satuan', 'Harga', 'Total_Row']])
                            
                            no_surat_input = st.text_input("📝 Nomor Surat:", value=f"..../S-TTS/II/{datetime.now().year}", key=f"no_txt_{i}")
                            pdf_bytes = generate_pdf(no_surat_input, row['Customer'], row['UP'], df_f, dpp, tax, total_akhir)
                            
                            st.download_button(
                                label="📥 Download PDF Penawaran",
                                data=pdf_bytes,
                                file_name=f"TTS_{row['Customer']}.pdf",
                                mime="application/pdf",
                                key=f"dl_btn_{i}"
                            )
                            
                            if st.button("✅ Selesai (Simpan & Hapus)", key=f"fin_btn_{i}"):
                                df_q.at[i, 'Status'] = 'Processed'
                                df_q.to_excel("antrean_penawaran.xlsx", index=False)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Gagal memproses baris ini: {e}")
        else:
            st.info("Belum ada data masuk.")
    else:
        st.warning("Gunakan password admin di sidebar.")
