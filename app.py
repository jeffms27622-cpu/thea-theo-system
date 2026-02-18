import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta
from fpdf import FPDF
import os
import gspread
from google.oauth2.service_account import Credentials

# --- 1. KONFIGURASI IDENTITAS ---
COMPANY_NAME = "PT. THEA THEO STATIONARY"
SLOGAN = "Supplier Alat Tulis Kantor & Sekolah"
ADDR = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
CONTACT = "Ph: 021-55780659, WA: 08158199775 | email: alattulis.tts@gmail.com"
ADMIN_PASSWORD = "tts123" 

st.set_page_config(page_title=COMPANY_NAME, layout="wide")

# --- 2. KONEKSI GOOGLE SHEETS ---
def connect_gsheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open("Antrean Penawaran TTS").sheet1
    except Exception as e:
        st.error(f"Koneksi GSheets Gagal: {e}")
        return None

# --- 3. FUNGSI DATABASE LOKAL ---
def load_db():
    if os.path.exists("database_barang.xlsx"):
        df = pd.read_excel("database_barang.xlsx")
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame(columns=['Nama Barang', 'Harga', 'Satuan'])

df_barang = load_db()

# --- 4. MESIN PDF ---
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
    pdf.cell(30, 8, f"{grand_total:,.0f}", 1, 1, 'R')
    
    pdf.ln(10); pdf.set_font('Arial', 'I', 8); pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "Dokumen ini diterbitkan secara otomatis oleh sistem PT. THEA THEO STATIONARY.\nSah dan valid tanpa tanda tangan basah.")
    pdf.set_text_color(0, 0, 0); pdf.ln(5); pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, "Hormat Kami,", ln=1); pdf.ln(15); pdf.cell(0, 6, "A.Sin", ln=1)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. LOGIKA MENU ---
menu = st.sidebar.selectbox("Pilih Menu:", ["🏠 Home", "📝 Portal Customer", "👨‍💻 Admin Dashboard"])

if 'cart' not in st.session_state:
    st.session_state.cart = []

if menu == "🏠 Home":
    st.title(f"Selamat Datang di {COMPANY_NAME}")
    st.write("Sistem Penawaran Otomatis v3.0 (Full Admin Control: Edit, Hapus & Tambah Item)")

elif menu == "📝 Portal Customer":
    st.title("🛒 Form Pengajuan Penawaran")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        nama_toko = col1.text_input("🏢 Nama Perusahaan / Toko")
        up_nama = col2.text_input("👤 Nama Penerima (UP)")
        wa_nomor = col1.text_input("📞 Nomor WhatsApp")
        picks = st.multiselect("📦 Pilih Barang:", options=df_barang['Nama Barang'].tolist())
        if st.button("Tambahkan Barang"):
            for p in picks:
                if p not in st.session_state.cart: st.session_state.cart.append(p)
            st.rerun()

    if st.session_state.cart:
        list_pesanan = []
        for item in st.session_state.cart:
            row = df_barang[df_barang['Nama Barang'] == item].iloc[0]
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 1, 1, 0.5])
                c1.write(f"**{item}**")
                qty = c3.number_input(f"Qty {item}", min_value=1, value=1, key=f"q_{item}")
                if c4.button("❌", key=f"del_{item}"):
                    st.session_state.cart.remove(item); st.rerun()
                list_pesanan.append({"Nama Barang": str(item), "Qty": int(qty), "Harga": float(row['Harga']), "Satuan": str(row['Satuan']), "Total_Row": float(qty * row['Harga'])})

        if st.button("🚀 Kirim Pengajuan", use_container_width=True):
            sheet = connect_gsheet()
            if sheet and nama_toko:
                waktu_jkt = datetime.utcnow() + timedelta(hours=7)
                sheet.append_row([waktu_jkt.strftime("%Y-%m-%d %H:%M"), nama_toko, up_nama, wa_nomor, str(list_pesanan), "Pending"])
                st.success("Terkirim! Terima kasih.")
                st.session_state.cart = []

elif menu == "👨‍💻 Admin Dashboard":
    st.title("Admin Dashboard (Editor Mode v3.0)")
    pwd = st.sidebar.text_input("Password:", type="password")
    if pwd == ADMIN_PASSWORD:
        sheet = connect_gsheet()
        if sheet:
            data = sheet.get_all_records()
            if data:
                df_gs = pd.DataFrame(data)
                pending = df_gs[df_gs['Status'] == 'Pending']
                
                if pending.empty:
                    st.info("Tidak ada antrean baru.")
                else:
                    for idx, row in pending.iterrows():
                        with st.expander(f"🛠️ EDIT PESANAN: {row['Customer']}"):
                            # 1. Load Data Pesanan Saat Ini
                            items_list = ast.literal_eval(str(row['Pesanan']))
                            current_items_df = pd.DataFrame(items_list)
                            
                            st.subheader("1. Edit Item Terdaftar")
                            edited_items = []
                            for i, r in current_items_df.iterrows():
                                col_a, col_b, col_c = st.columns([3, 1, 1])
                                col_a.write(f"**{r['Nama Barang']}** ({r['Satuan']})")
                                new_qty = col_b.number_input(f"Qty", value=int(r['Qty']), key=f"ed_qty_{idx}_{i}")
                                hapus = col_c.checkbox("Hapus Item", key=f"ed_del_{idx}_{i}")
                                
                                if not hapus:
                                    edited_items.append({
                                        "Nama Barang": r['Nama Barang'],
                                        "Qty": new_qty,
                                        "Harga": r['Harga'],
                                        "Satuan": r['Satuan'],
                                        "Total_Row": new_qty * r['Harga']
                                    })
                            
                            st.divider()
                            st.subheader("2. Tambah Barang Baru ke Pesanan")
                            new_picks = st.multiselect("Pilih Barang Tambahan:", options=df_barang['Nama Barang'].tolist(), key=f"add_item_{idx}")
                            
                            for p in new_picks:
                                row_b = df_barang[df_barang['Nama Barang'] == p].iloc[0]
                                with st.container():
                                    ca, cb = st.columns([3, 1])
                                    ca.write(f"Menambahkan: **{p}**")
                                    a_qty = cb.number_input(f"Qty Tambahan", min_value=1, value=1, key=f"add_qty_{idx}_{p}")
                                    edited_items.append({
                                        "Nama Barang": str(p),
                                        "Qty": int(a_qty),
                                        "Harga": float(row_b['Harga']),
                                        "Satuan": str(row_b['Satuan']),
                                        "Total_Row": float(a_qty * row_b['Harga'])
                                    })

                            # 2. Simpan Semua Perubahan (Edit + Hapus + Tambah)
                            if st.button("💾 Simpan Perubahan ke Google Sheets", key=f"btn_save_{idx}"):
                                sheet.update_cell(idx + 2, 5, str(edited_items))
                                st.success("Database GSheets telah diperbarui!")
                                st.rerun()

                            # 3. Preview & Cetak PDF
                            st.divider()
                            final_df = pd.DataFrame(edited_items)
                            if not final_df.empty:
                                dpp = final_df['Total_Row'].sum()
                                tax = dpp * 0.11
                                total = dpp + tax
                                
                                st.write(f"**Preview Total Baru:** Rp {total:,.0f}")
                                
                                no_surat = st.text_input("No Surat:", value=f"..../S-TTS/II/{datetime.now().year}", key=f"no_{idx}")
                                pdf_bytes = generate_pdf(no_surat, row['Customer'], row['UP'], final_df, dpp, tax, total)
                                
                                st.download_button("📩 Download PDF Final", data=pdf_bytes, file_name=f"TTS_{row['Customer']}.pdf", key=f"dl_{idx}")
                                
                                if st.button("✅ Selesai & Arsipkan", key=f"fin_{idx}"):
                                    sheet.update_cell(idx + 2, 6, "Processed")
                                    st.rerun()
                            else:
                                st.warning("Daftar pesanan kosong.")
