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
# 1. KONFIGURASI & IDENTITAS
# =========================================================
MARKETING_NAME  = "Asin"
COMPANY_NAME    = "PT. THEA THEO STATIONARY"
SLOGAN          = "Partner Terpercaya Kebutuhan Kantor & Sekolah"
ADDR            = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
OFFICE_PHONE    = "(021) 55780659"
WA_MARKETING    = "08158199775"
EMAIL_MARKETING = "alattulis.tts@gmail.com"
PAJAK_FOLDER_ID = "19i_mLcu4VtV85NLwZY67zZTGwxBgdG1z"
ADMIN_PASSWORD  = st.secrets["ADMIN_PASSWORD"]

st.set_page_config(page_title=f"Sistem TTS - {MARKETING_NAME}", layout="wide")

# =========================================================
# 2. KONEKSI GOOGLE (SHEET & DRIVE)
# =========================================================
def get_creds():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)

def connect_gsheet():
    try:
        client = gspread.authorize(get_creds())
        return client.open("Antrean Penawaran TTS").sheet1
    except: return None

def search_pajak_file(inv_keyword, name_keyword):
    try:
        service = build('drive', 'v3', credentials=get_creds())
        query = f"'{PAJAK_FOLDER_ID}' in parents and mimeType = 'application/pdf' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)", pageSize=1000).execute()
        files = results.get('files', [])
        
        clean_inv = re.sub(r'[^A-Z0-9]', '', inv_keyword.upper()) if inv_keyword else ""
        clean_name = re.sub(r'[^A-Z0-9]', '', name_keyword.upper()) if name_keyword else ""
        
        for f in files:
            fname = re.sub(r'[^A-Z0-9]', '', f['name'].upper())
            match_inv = clean_inv in fname if clean_inv else True
            match_name = clean_name in fname if clean_name else True
            if (clean_inv or clean_name) and match_inv and match_name:
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
# 3. PDF ENGINE (TAMPILAN PROFESIONAL)
# =========================================================
class PenawaranPDF(FPDF):
    def header(self):
        self.set_fill_color(0, 51, 102)
        self.rect(0, 0, 210, 5, 'F')
        if os.path.exists("logo.png"): self.image("logo.png", 10, 10, 30)
        self.set_x(45); self.set_font('Arial', 'B', 16); self.set_text_color(0, 51, 102); self.cell(0, 8, COMPANY_NAME, ln=1)
        self.set_x(45); self.set_font('Arial', '', 9); self.set_text_color(100, 100, 100); self.cell(0, 5, SLOGAN, ln=1)
        self.set_x(45); self.cell(0, 5, f"{ADDR} | Telp: {OFFICE_PHONE}", ln=1)
        self.set_y(12); self.set_font('Arial', '', 8); self.set_text_color(0, 0, 0); self.cell(0, 4, f"WA: {WA_MARKETING}", ln=1, align='R'); self.cell(0, 4, f"Email: {EMAIL_MARKETING}", ln=1, align='R')
        self.set_draw_color(0, 51, 102); self.set_line_width(0.8); self.line(10, 40, 200, 40); self.ln(22)

def generate_pdf(no_s, cust, pic, df_f, subt, tax, gtot):
    pdf = PenawaranPDF()
    pdf.add_page(); pdf.set_font('Arial', 'B', 12); pdf.cell(0, 7, "SURAT PENAWARAN HARGA", ln=1, align='C'); pdf.ln(5)
    tgl = (datetime.utcnow() + timedelta(hours=7)).strftime('%d %B %Y')
    pdf.set_font('Arial', '', 10); pdf.cell(95, 6, f"No: {no_s}", 0); pdf.cell(95, 6, f"Tanggal: {tgl}", 0, 1, 'R'); pdf.ln(5)
    pdf.set_font('Arial', 'B', 10); pdf.cell(0, 6, "Kepada Yth,", ln=1); pdf.set_font('Arial', 'B', 11); pdf.cell(0, 6, str(cust).upper(), ln=1); pdf.set_font('Arial', '', 10); pdf.cell(0, 6, f"Up. {pic}", ln=1); pdf.ln(8)
    
    # Tabel
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
    
    pdf.ln(10); pdf.set_font('Arial', 'I', 8); pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "* Dokumen ini diterbitkan secara otomatis. Sah tanpa tanda tangan basah.\n* Harga dapat berubah sewaktu-waktu.")
    pdf.ln(10); pdf.set_font('Arial', 'B', 11); pdf.set_text_color(0, 0, 0); pdf.cell(0, 6, "Hormat Kami,", ln=1); pdf.ln(15); pdf.cell(0, 6, MARKETING_NAME, ln=1); pdf.set_font('Arial', '', 10); pdf.cell(0, 5, "Sales Consultant", ln=1)
    return pdf.output(dest='S').encode('latin-1')

# --- LANJUT KE BAGIAN 2 DI BAWAH ---
# =========================================================
# 4. APLIKASI UTAMA (MENU & LOGIKA)
# =========================================================
st.sidebar.header(f"PORTAL {MARKETING_NAME}")
# GANTI JADI RADIO BUTTON AGAR JELAS
menu = st.sidebar.radio("PILIH AREA KERJA:", ["🛒 AREA STAFF", "🔐 AREA BOSS (ADMIN)"])

sheet = connect_gsheet()

# --- MENU 1: AREA STAFF (INPUT & PAJAK) ---
if menu == "🛒 AREA STAFF":
    # Buat 2 Tab di sini
    tab1, tab2 = st.tabs(["📝 INPUT PESANAN", "📂 CARI FAKTUR PAJAK"])
    
    # TAB 1: INPUT PESANAN
    with tab1:
        st.subheader("Input Pesanan Customer")
        if 'cart' not in st.session_state: st.session_state.cart = []
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            toko = c1.text_input("Nama Toko")
            up = c2.text_input("Nama UP")
            wa = c1.text_input("WhatsApp")
            
            pilih_barang = st.multiselect("Pilih Barang:", options=df_barang['Nama Barang'].tolist())
            if st.button("➕ Tambah"):
                for p in pilih_barang:
                    if p not in st.session_state.cart: st.session_state.cart.append(p)
                st.rerun()

        if st.session_state.cart:
            st.warning("Daftar Barang Sementara:")
            final_list = []
            for item in st.session_state.cart:
                d = df_barang[df_barang['Nama Barang'] == item].iloc[0]
                with st.container(border=True):
                    kc1, kc2, kc3 = st.columns([3, 1, 0.5])
                    kc1.write(f"**{item}** (Sat: {d['Satuan']} | Rp {d['Harga']:,.0f})")
                    qty = kc2.number_input("Qty", 1, key=f"q_{item}")
                    if kc3.button("❌", key=f"d_{item}"): st.session_state.cart.remove(item); st.rerun()
                    final_list.append({"Nama Barang": item, "Qty": qty, "Harga": float(d['Harga']), "Satuan": d['Satuan'], "Total_Row": qty*d['Harga']})
            
            if st.button("🚀 KIRIM KE ADMIN", use_container_width=True):
                if sheet and toko:
                    wkt = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")
                    sheet.append_row([wkt, toko, up, wa, str(final_list), "Pending", MARKETING_NAME])
                    st.success("Terkirim ke Area Boss!"); st.session_state.cart = []

    # TAB 2: PAJAK (ADA DI MENU STAFF)
    with tab2:
        st.subheader("Cari Faktur Pajak")
        col_inv, col_name = st.columns(2)
        inv = col_inv.text_input("No Invoice")
        nam = col_name.text_input("Nama PT")
        
        if st.button("🔍 Cari di Drive"):
            with st.spinner("Mencari..."):
                f = search_pajak_file(inv, nam)
                if f:
                    st.success(f"Ketemu: {f['name']}")
                    st.download_button("📥 Download PDF", download_drive_file(f['id']), f['name'])
                else: st.error("Tidak ditemukan.")

# --- MENU 2: AREA BOSS (ADMIN) ---
elif menu == "🔐 AREA BOSS (ADMIN)":
    st.header("🔐 Dashboard Admin")
    pwd = st.sidebar.text_input("Password Admin:", type="password")
    
    if pwd == ADMIN_PASSWORD:
        if sheet:
            # Filter Data
            all = sheet.get_all_values()
            df = pd.DataFrame(all[1:], columns=all[0]) if len(all)>1 else pd.DataFrame()
            df = df[df['Sales'] == MARKETING_NAME]
            
            view_mode = st.radio("Status:", ["Antrean (Pending)", "Selesai (Processed)"], horizontal=True)
            stat = "Pending" if "Pending" in view_mode else "Processed"
            df_show = df[df['Status'] == stat]
            
            if df_show.empty: st.info("Kosong.")
            
            for idx, row in df_show.iterrows():
                real_idx = idx + 2 # FIX INDEX
                with st.expander(f"📄 {row['Customer']}", expanded=(stat=="Pending")):
                    # Ambil Data Aman
                    try: items = ast.literal_eval(str(row['Pesanan']))
                    except: items = []
                    
                    # 1. Tambah Barang
                    add = st.multiselect("Tambah Item:", df_barang['Nama Barang'].tolist(), key=f"a_{idx}")
                    for a in add:
                        if not any(x['Nama Barang'] == a for x in items):
                            d = df_barang[df_barang['Nama Barang'] == a].iloc[0]
                            items.append({"Nama Barang": a, "Qty": 1, "Harga": float(d['Harga']), "Satuan": str(d['Satuan']), "Total_Row": float(d['Harga'])})
                    
                    # 2. Edit Table
                    new_items = []
                    for i, it in enumerate(items):
                        c1, c2, c3, c4, c5 = st.columns([3, 0.7, 0.8, 1.2, 0.5])
                        c1.write(f"**{it['Nama Barang']}**")
                        nq = c2.number_input("Q", value=int(it['Qty']), key=f"q_{idx}_{i}")
                        ns = c3.text_input("S", value=it['Satuan'], key=f"s_{idx}_{i}")
                        nh = c4.number_input("Rp", value=float(it['Harga']), key=f"h_{idx}_{i}")
                        delt = c5.checkbox("Hapus", key=f"dl_{idx}_{i}")
                        if not delt:
                            new_items.append({"Nama Barang": it['Nama Barang'], "Qty": nq, "Harga": nh, "Satuan": ns, "Total_Row": nq*nh})
                    
                    st.divider()
                    
                    # 3. Action Buttons
                    sc1, sc2 = st.columns(2)
                    if sc1.button("💾 UPDATE DATA", key=f"sv_{idx}"):
                        sheet.update_cell(real_idx, 5, str(new_items))
                        st.success("Disimpan!"); st.rerun()
                        
                    df_print = pd.DataFrame(new_items)
                    if not df_print.empty:
                        sub = df_print['Total_Row'].sum(); tax = sub*0.11; tot = sub+tax
                        sc2.write(f"**Total: Rp {tot:,.0f}**")
                        nos = sc2.text_input("No Surat:", f"..../S-TTS/II/{datetime.now().year}", key=f"no_{idx}")
                        pdf_b = generate_pdf(nos, row['Customer'], row['UP'], df_print, sub, tax, tot)
                        sc2.download_button("📩 PDF", pdf_b, f"{row['Customer']}.pdf", key=f"pd_{idx}")
                        if sc2.button("✅ SELESAI", key=f"dn_{idx}"):
                            sheet.update_cell(real_idx, 6, "Processed"); st.rerun()
