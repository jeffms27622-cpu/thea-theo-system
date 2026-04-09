import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta
from fpdf import FPDF
import os
import gspread
from google.oauth2.service_account import Credentials
import io
import time

# =========================================================
# 1. KONFIGURASI UTAMA
# =========================================================
MARKETING_NAME  = "Asin"
MARKETING_WA    = "0815-8199-775"
MARKETING_EMAIL = "alattulis.tts@gmail.com"
COMPANY_NAME    = "PT. THEA THEO STATIONARY"
SLOGAN          = "Office & School Supplies Solution"
ADDR            = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
OFFICE_PHONE    = "(021) 55780659"

if "ADMIN_PASSWORD" in st.secrets:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
else:
    ADMIN_PASSWORD = "admin" 

COLOR_NAVY = (0, 40, 85)
COLOR_GOLD = (184, 134, 11)
COLOR_TEXT = (30, 30, 30)

st.set_page_config(page_title=f"TTS System - {MARKETING_NAME}", layout="wide")

# =========================================================
# 2. FUNGSI KONEKSI (OPTIMIZED)
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

@st.cache_data(ttl=600)
def load_db():
    if os.path.exists("database_barang.csv"):
        try:
            df = pd.read_csv("database_barang.csv", sep=None, engine='python', on_bad_lines='skip')
            df.columns = df.columns.str.strip()
            if 'Harga' in df.columns:
                df['Harga'] = pd.to_numeric(df['Harga'], errors='coerce').fillna(0)
            return df
        except: pass
    return pd.DataFrame(columns=['Nama Barang', 'Harga', 'Satuan'])

df_barang = load_db()

# --- CACHING DATA ANTREAN AGAR TIDAK LEMOT ---
@st.cache_data(ttl=30)
def fetch_antrean_data_cached():
    sheet = connect_gsheet()
    if sheet:
        return sheet.get_all_values()
    return []

# =========================================================
# 3. PDF & EXCEL ENGINE
# =========================================================
class PenawaranPDF(FPDF):
    def header(self):
        self.set_fill_color(*COLOR_NAVY); self.rect(0, 0, 210, 50, 'F')
        if os.path.exists("logo.png"): self.image("logo.png", 15, 10, 35)
        self.set_y(15); self.set_x(60)
        self.set_font('Arial', 'B', 20); self.set_text_color(255, 255, 255); self.cell(0, 8, COMPANY_NAME, ln=1)
        self.set_x(60); self.set_font('Arial', 'B', 8); self.set_text_color(*COLOR_GOLD); self.cell(0, 5, SLOGAN.upper(), ln=1)

def generate_pdf(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    pdf = PenawaranPDF(); pdf.set_margins(10, 60, 10); pdf.add_page()
    pdf.set_y(55); pdf.set_font('Arial', 'B', 22); pdf.set_text_color(*COLOR_NAVY); pdf.cell(0, 10, "QUOTATION", ln=1, align='R')
    pdf.set_font('Arial', '', 9); pdf.set_text_color(120, 120, 120); pdf.cell(0, 5, f"Ref: {no_surat} | Date: {datetime.now().strftime('%d %B %Y')}", ln=1, align='R')
    
    pdf.set_y(55); pdf.set_font('Arial', 'B', 9); pdf.set_text_color(*COLOR_GOLD); pdf.cell(0, 5, "PREPARED FOR:", ln=1)
    pdf.set_font('Arial', 'B', 13); pdf.set_text_color(30,30,30); pdf.cell(0, 7, str(nama_cust).upper(), ln=1)
    pdf.set_font('Arial', '', 10); pdf.cell(0, 5, f"Attention: {pic}", ln=1); pdf.ln(10)

    # Header Tabel
    pdf.set_fill_color(*COLOR_NAVY); pdf.set_text_color(255,255,255); pdf.set_font('Arial', 'B', 9)
    pdf.cell(10, 10, 'NO', 1, 0, 'C', True); pdf.cell(90, 10, 'DESCRIPTION', 1, 0, 'L', True)
    pdf.cell(20, 10, 'QTY', 1, 0, 'C', True); pdf.cell(20, 10, 'UNIT', 1, 0, 'C', True)
    pdf.cell(25, 10, 'PRICE', 1, 0, 'R', True); pdf.cell(25, 10, 'TOTAL', 1, 1, 'R', True)

    pdf.set_font('Arial', '', 9); pdf.set_text_color(30,30,30)
    for i, row in df_order.iterrows():
        pdf.cell(10, 8, str(i+1), 1, 0, 'C'); pdf.cell(90, 8, f" {row['Nama Barang']}", 1, 0, 'L')
        pdf.cell(20, 8, str(int(row['Qty'])), 1, 0, 'C'); pdf.cell(20, 8, str(row['Satuan']), 1, 0, 'C')
        pdf.cell(25, 8, f"{row['Harga']:,.0f} ", 1, 0, 'R'); pdf.cell(25, 8, f"{row['Total_Row']:,.0f} ", 1, 1, 'R')

    pdf.ln(5); pdf.set_x(130); pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 8, "Sub Total", 0, 0); pdf.cell(25, 8, f"{subtotal:,.0f}", 0, 1, 'R')
    pdf.cell(130); pdf.cell(45, 8, "VAT 11%", 0, 0); pdf.cell(25, 8, f"{ppn:,.0f}", 0, 1, 'R')
    pdf.set_fill_color(*COLOR_NAVY); pdf.set_text_color(255,255,255); pdf.cell(130)
    pdf.cell(70, 10, f" TOTAL IDR {grand_total:,.0f} ", 0, 1, 'R', True)
    return pdf.output(dest='S').encode('latin-1')

def generate_excel(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book; worksheet = workbook.add_worksheet('Quotation')
        fmt_h = workbook.add_format({'bg_color': '#002855', 'font_color': 'white', 'bold': True, 'align': 'center'})
        worksheet.write('A1', COMPANY_NAME); worksheet.write('A2', f"Ref: {no_surat}")
        df_order.to_excel(writer, startrow=4, index=False, sheet_name='Quotation')
    return output.getvalue()

# =========================================================
# 4. DASHBOARD FRAGMENT (SOLUSI ANTI-LAG)
# =========================================================
@st.fragment
def manage_order_card(row_data, real_row_idx, sheet):
    with st.expander(f"🛠️ KELOLA: {row_data['Customer']}", expanded=True):
        try: items_list = ast.literal_eval(str(row_data['Pesanan']))
        except: items_list = []

        with st.form(key=f"form_{real_row_idx}"):
            st.markdown("##### 📝 Edit Harga & Konversi Satuan")
            temp_up = []
            
            for i, r in enumerate(items_list):
                # Ambil Harga Master
                row_m = df_barang[df_barang['Nama Barang'] == r['Nama Barang']]
                h_master = float(row_m['Harga'].values[0]) if not row_m.empty else float(r['Harga'])
                
                u_k = f"row{real_row_idx}_i{i}"
                c1, c2, c3, c4, c5 = st.columns([2.5, 1.3, 1.2, 1.5, 0.4])
                
                c1.markdown(f"**{r['Nama Barang']}**")
                c1.caption(f"Master: Rp {h_master:,.0f}/Pcs")

                mode = c2.selectbox("Jual Per?", ["Pcs", "Lusin (12x)", "Pack/Box"], key=f"m_{u_k}")
                nq = c2.number_input("Qty", min_value=1, value=int(r['Qty']), key=f"q_{u_k}")

                mult = 1; s_auto = "Pcs"
                if mode == "Lusin (12x)": mult = 12; s_auto = "Lusin"
                elif mode == "Pack/Box":
                    isi = c3.number_input("Isi per Pack", min_value=1, value=10, key=f"isi_{u_k}")
                    mult = isi; s_auto = "Pack"
                
                ns = c3.text_input("Satuan", value=s_auto, key=f"s_{u_k}")
                nh = c4.number_input("Harga Jual", value=int(h_master * mult), step=500, key=f"h_{u_k}")
                td = c5.checkbox("🗑️", key=f"d_{u_k}")
                
                temp_up.append({"del": td, "Nama": r['Nama Barang'], "Qty": nq, "Harga": nh, "Sat": ns})

            st.write("---")
            add_b = st.multiselect("➕ Tambah Barang:", options=df_barang['Nama Barang'].tolist(), key=f"add_{real_row_idx}")
            
            if st.form_submit_button("💾 SIMPAN PERUBAHAN", use_container_width=True):
                final = [x for x in temp_up if not x['del']]
                for p in add_b:
                    rb = df_barang[df_barang['Nama Barang'] == p].iloc[0]
                    final.append({"Nama": p, "Qty": 1, "Harga": float(rb['Harga']), "Sat": str(rb['Satuan'])})
                
                save_data = [{"Nama Barang": x['Nama'], "Qty": x['Qty'], "Harga": x['Harga'], "Satuan": x['Sat'], "Total_Row": x['Qty']*x['Harga']} for x in final]
                sheet.update_cell(real_row_idx, 5, str(save_data))
                st.cache_data.clear()
                st.success("Tersimpan!"); time.sleep(1); st.rerun()

        # Download & Print Area
        if items_list:
            df_curr = pd.DataFrame(items_list)
            subt = df_curr['Total_Row'].sum(); tax = subt * 0.11; gtot = subt + tax
            
            c_no, c_met = st.columns([2, 1])
            no_s = c_no.text_input("No Surat:", value="/S-TTS/IV/2026", key=f"ns_{real_row_idx}")
            c_met.metric("Total", f"Rp {gtot:,.0f}")
            
            b1, b2, b3 = st.columns(3)
            p_data = generate_pdf(no_s, row_data['Customer'], row_data['UP'], df_curr, subt, tax, gtot)
            b1.download_button("📩 PDF", p_data, f"Quo_{row_data['Customer']}.pdf", key=f"p_{real_row_idx}", use_container_width=True)
            
            x_data = generate_excel(no_s, row_data['Customer'], row_data['UP'], df_curr, subt, tax, gtot)
            b2.download_button("📊 Excel", x_data, f"Quo_{row_data['Customer']}.xlsx", key=f"x_{real_row_idx}", use_container_width=True)
            
            if b3.button("✅ SELESAI", key=f"ok_{real_row_idx}", use_container_width=True, type="primary"):
                sheet.update_cell(real_row_idx, 6, "Processed")
                st.cache_data.clear(); st.rerun()

# =========================================================
# 5. UI MAIN
# =========================================================
st.sidebar.title(f"Portal {MARKETING_NAME}")
if st.sidebar.button("🧹 Refresh & Bersihkan Memori"):
    st.cache_data.clear(); st.rerun()

menu = st.sidebar.selectbox("Pilih Menu:", ["🏠 Home", "📝 Portal Customer", "👨‍💻 Admin Dashboard"])

if menu == "🏠 Home":
    st.title(f"Selamat Datang di {COMPANY_NAME}")
    st.info(f"Marketing Aktif: {MARKETING_NAME} | {MARKETING_WA}")

elif menu == "📝 Portal Customer":
    st.subheader("Form Pengajuan Penawaran")
    with st.form("form_cust"):
        c1, c2 = st.columns(2)
        n_toko = c1.text_input("🏢 Nama Toko")
        n_up = c2.text_input("👤 UP")
        wa = c1.text_input("📞 WA")
        items = st.multiselect("📦 Pilih Barang", options=df_barang['Nama Barang'].tolist())
        if st.form_submit_button("🚀 Kirim Pengajuan"):
            sheet = connect_gsheet()
            if sheet and n_toko:
                wkt = (datetime.now() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")
                list_p = []
                for p in items:
                    rb = df_barang[df_barang['Nama Barang'] == p].iloc[0]
                    list_p.append({"Nama Barang": p, "Qty": 1, "Harga": rb['Harga'], "Satuan": rb['Satuan'], "Total_Row": rb['Harga']})
                sheet.append_row([wkt, n_toko, n_up, wa, str(list_p), "Pending", MARKETING_NAME])
                st.cache_data.clear(); st.success("Terkirim!")

elif menu == "👨‍💻 Admin Dashboard":
    st.title(f"Admin Dashboard - {MARKETING_NAME}")
    pwd = st.sidebar.text_input("Password:", type="password")
    if pwd == ADMIN_PASSWORD:
        all_vals = fetch_antrean_data_cached()
        if len(all_vals) > 1:
            df_gs = pd.DataFrame(all_vals[1:], columns=all_vals[0])
            df_gs.columns = df_gs.columns.str.strip()
            pending = df_gs[(df_gs['Status'] == 'Pending') & (df_gs['Sales'] == MARKETING_NAME)]
            
            if not pending.empty:
                sheet = connect_gsheet()
                for idx, row in pending.iterrows():
                    manage_order_card(row, df_gs.index[idx] + 2, sheet)
            else: st.success("Antrean Bersih!")
    else: st.warning("Masukkan Password di Sidebar.")
