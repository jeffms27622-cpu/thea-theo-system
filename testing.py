import streamlit as st
import pandas as pd
import json
import ast
from datetime import datetime, timedelta
from fpdf import FPDF
import os
import gspread
from google.oauth2.service_account import Credentials
import io
import time
import logging
import re

# =========================================================
# 0. LOGGING SETUP
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =========================================================
# 1. KONFIGURASI UTAMA & DATA KANTOR
# =========================================================
MARKETING_NAME  = "Asin"
MARKETING_WA    = "0815-8199-775"
MARKETING_EMAIL = "alattulis.tts@gmail.com"

COMPANY_NAME    = "PT. THEA THEO STATIONARY"
SLOGAN          = "Office & School Supplies Solution"
ADDR            = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
OFFICE_PHONE    = "(021) 55780659"

ADMIN_PASSWORD        = st.secrets.get("ADMIN_PASSWORD", "admin")
MAX_LOGIN_ATTEMPTS    = 5
LOGIN_LOCKOUT_SECONDS = 300

COLOR_NAVY = (0, 40, 85)
COLOR_GOLD = (184, 134, 11)
COLOR_TEXT = (30, 30, 30)

st.set_page_config(page_title=f"{COMPANY_NAME} - {MARKETING_NAME}", layout="wide")

# =========================================================
# 2. SESSION STATE INIT
# =========================================================
def init_session():
    defaults = {
        "cart":           [],
        "widget_id":      0,
        "login_attempts": 0,
        "lockout_until":  None,
        "authenticated":  False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# =========================================================
# 3. VALIDASI
# =========================================================
def validate_wa(nomor: str) -> bool:
    clean = re.sub(r"[\s\-]", "", nomor)
    return clean.isdigit() and 9 <= len(clean) <= 15

# =========================================================
# 4. KONEKSI & DATABASE
# =========================================================
@st.cache_resource
def get_gsheet_client():
    """
    Cache koneksi GSheet di level resource — dibuat SEKALI selama app hidup.
    Tidak perlu buka koneksi baru setiap interaksi.
    """
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds  = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scope
        )
        client = gspread.authorize(creds)
        logger.info("GSheet client berhasil dibuat.")
        return client
    except Exception as e:
        logger.error(f"Gagal membuat GSheet client: {e}")
        return None


def get_sheet():
    """
    Ambil objek sheet dari client yang sudah di-cache.
    Ringan — tidak buka koneksi baru.
    """
    client = get_gsheet_client()
    if not client:
        st.error("Koneksi Google Sheets gagal. Cek konfigurasi secrets.")
        return None
    try:
        sheet = client.open("Antrean Penawaran TTS").sheet1
        return sheet
    except Exception as e:
        logger.error(f"Gagal membuka sheet: {e}")
        st.error(f"Gagal membuka spreadsheet: {e}")
        return None


@st.cache_data(ttl=30)
def load_sheet_data() -> pd.DataFrame:
    """
    Ambil semua data GSheet dan simpan di cache 30 detik.
    Semua operasi baca pakai fungsi ini — hanya 1 API call per 30 detik.
    Tulis/update tetap langsung ke sheet (tidak perlu cache).
    """
    sheet = get_sheet()
    if not sheet:
        return pd.DataFrame()
    try:
        all_vals = sheet.get_all_values()
        if len(all_vals) <= 1:
            return pd.DataFrame()

        # Normalisasi header: strip spasi + mapping ke nama standar
        raw_headers = [str(h).strip() for h in all_vals[0]]
        ALIASES = {
            "waktu":    "Waktu",
            "customer": "Customer",
            "up":       "UP",
            "wa":       "WA",
            "pesanan":  "Pesanan",
            "status":   "Status",
            "sales":    "Sales",
        }
        headers = [ALIASES.get(h.lower(), h) for h in raw_headers]

        df = pd.DataFrame(all_vals[1:], columns=headers)

        # Pastikan semua kolom wajib ada
        for col in ["Waktu", "Customer", "UP", "WA", "Pesanan", "Status", "Sales"]:
            if col not in df.columns:
                df[col] = ""

        return df
    except Exception as e:
        logger.error(f"Gagal load sheet data: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=600)
def load_db():
    if not os.path.exists("database_barang.csv"):
        st.warning(
            "⚠️ Database barang belum diupload. "
            "Masuk ke **Sales Dashboard → Update Database** untuk upload."
        )
        return pd.DataFrame(columns=["Nama Barang", "Harga", "Satuan"])
    try:
        df = pd.read_csv(
            "database_barang.csv",
            sep=None, engine="python", on_bad_lines="skip"
        )
        df.columns = df.columns.str.strip()
        if "Harga" in df.columns:
            df["Harga"] = pd.to_numeric(df["Harga"], errors="coerce").fillna(0)
        logger.info(f"Database loaded: {len(df)} items.")
        return df
    except Exception as e:
        logger.error(f"Gagal membaca CSV: {e}")
        st.error(f"Gagal membaca database: {e}")
        return pd.DataFrame(columns=["Nama Barang", "Harga", "Satuan"])

df_barang = load_db()

# =========================================================
# 5. HELPER: SERIALISASI JSON
# =========================================================
def pesanan_to_json(items: list) -> str:
    return json.dumps(items, ensure_ascii=False)

def json_to_pesanan(raw: str) -> list:
    raw = raw.strip()
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    try:
        result = ast.literal_eval(raw)
        if isinstance(result, list):
            return result
    except Exception:
        pass
    logger.warning(f"Gagal parse pesanan: {raw[:80]}")
    return []

# =========================================================
# 6. HELPER: HITUNG TOTAL
# =========================================================
def hitung_total(items: list):
    subtotal    = sum(float(x.get("Total_Row", 0)) for x in items)
    ppn         = subtotal * 0.11
    grand_total = subtotal + ppn
    return subtotal, ppn, grand_total

# =========================================================
# 7. AUTH
# =========================================================
def check_auth(pwd: str) -> bool:
    now = datetime.utcnow()
    if st.session_state.lockout_until:
        sisa = (st.session_state.lockout_until - now).total_seconds()
        if sisa > 0:
            st.sidebar.error(f"⛔ Terlalu banyak percobaan. Coba lagi dalam {int(sisa)} detik.")
            return False
        else:
            st.session_state.lockout_until  = None
            st.session_state.login_attempts = 0

    if pwd == ADMIN_PASSWORD:
        st.session_state.authenticated  = True
        st.session_state.login_attempts = 0
        logger.info("Admin login berhasil.")
        return True
    elif pwd:
        st.session_state.login_attempts += 1
        remaining = MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts
        if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
            st.session_state.lockout_until = now + timedelta(seconds=LOGIN_LOCKOUT_SECONDS)
            st.sidebar.error(f"⛔ Akun dikunci selama {LOGIN_LOCKOUT_SECONDS // 60} menit.")
            logger.warning("Admin login dikunci.")
        else:
            st.sidebar.warning(f"Password salah. Sisa percobaan: {remaining}")
    return False

# =========================================================
# 8. PDF ENGINE
# =========================================================
class PenawaranPDF(FPDF):
    def header(self):
        self.set_fill_color(*COLOR_NAVY)
        self.rect(0, 0, 210, 55, "F")
        self.set_fill_color(255, 255, 255)
        self.rect(10, 0, 50, 55, "F")
        self.set_fill_color(*COLOR_GOLD)
        self.rect(60, 0, 2, 55, "F")
        self.rect(64, 0, 0.5, 55, "F")
        if os.path.exists("logo.png"):
            self.image("logo.png", 15, 12, 40)
        self.set_y(12); self.set_x(72)
        self.set_font("Arial", "B", 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, COMPANY_NAME, ln=1)
        self.set_x(72)
        self.set_font("Arial", "B", 10)
        self.set_text_color(184, 134, 11)
        self.cell(0, 6, "  ".join(SLOGAN.upper()), ln=1)
        self.set_fill_color(255, 255, 255)
        self.rect(72, 28, 120, 0.2, "F")
        self.set_y(32); self.set_x(72)
        self.set_font("Arial", "", 8)
        self.set_text_color(220, 220, 220)
        self.cell(0, 4, ADDR, ln=1)
        self.set_x(72)
        self.cell(0, 4, f"Office: {OFFICE_PHONE}  |  WA: {MARKETING_WA}", ln=1)
        self.set_x(72)
        self.cell(0, 4, f"Email: {MARKETING_EMAIL}", ln=1)
        self.set_y(65)

    def footer(self):
        self.set_y(-25)
        self.set_fill_color(*COLOR_NAVY)
        self.rect(0, 272, 210, 25, "F")
        self.set_fill_color(*COLOR_GOLD)
        self.rect(0, 292, 210, 5, "F")
        self.set_y(-18)
        self.set_font("Arial", "B", 9)
        self.set_text_color(255, 255, 255)
        self.cell(0, 5, "THANK YOU FOR YOUR BUSINESS", 0, 1, "C")
        self.set_font("Arial", "", 7)
        self.set_text_color(184, 134, 11)
        self.cell(0, 4, f"Page {self.page_no()} | Generated by TTS System", 0, 0, "C")


def draw_table_header(pdf):
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(*COLOR_NAVY)
    pdf.cell(10, 10, "NO",          0, 0, "C", True)
    pdf.cell(90, 10, "DESCRIPTION", 0, 0, "L", True)
    pdf.cell(20, 10, "QTY",         0, 0, "C", True)
    pdf.cell(20, 10, "UNIT",        0, 0, "C", True)
    pdf.cell(25, 10, "PRICE",       0, 0, "R", True)
    pdf.cell(25, 10, "TOTAL",       0, 1, "R", True)


def generate_pdf(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    pdf = PenawaranPDF()
    pdf.set_margins(10, 70, 10)
    pdf.set_auto_page_break(auto=True, margin=30)
    pdf.add_page()

    pdf.set_y(70)
    pdf.set_font("Arial", "B", 24)
    pdf.set_text_color(*COLOR_NAVY)
    pdf.cell(0, 10, "QUOTATION", ln=1, align="R")
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, f"Reference: {no_surat}", ln=1, align="R")
    waktu_skrg = datetime.utcnow() + timedelta(hours=7)
    pdf.cell(0, 5, f"Date: {waktu_skrg.strftime('%d %B %Y')}", ln=1, align="R")

    pdf.set_y(70)
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*COLOR_GOLD)
    pdf.cell(0, 5, "PREPARED FOR:", ln=1)
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.cell(0, 7, str(nama_cust).upper(), ln=1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Attention: {pic}", ln=1)
    pdf.ln(10)

    draw_table_header(pdf)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*COLOR_TEXT)
    fill = False
    for i, row in df_order.iterrows():
        if pdf.get_y() > 240:
            pdf.add_page()
            draw_table_header(pdf)
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(*COLOR_TEXT)
        pdf.set_fill_color(248, 249, 252) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(10, 8, str(i + 1),                0, 0, "C", True)
        pdf.cell(90, 8, f" {row['Nama Barang']}",   0, 0, "L", True)
        pdf.cell(20, 8, str(int(row["Qty"])),       0, 0, "C", True)
        pdf.cell(20, 8, str(row["Satuan"]),         0, 0, "C", True)
        pdf.cell(25, 8, f"{row['Harga']:,.0f} ",    0, 0, "R", True)
        pdf.cell(25, 8, f"{row['Total_Row']:,.0f} ", 0, 1, "R", True)
        pdf.set_draw_color(184, 134, 11)
        pdf.set_line_width(0.1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        fill = not fill

    if pdf.get_y() > 220:
        pdf.add_page()
    pdf.ln(5)
    pdf.set_x(130)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(45, 8, "Sub Total",      0, 0, "L")
    pdf.cell(25, 8, f" {subtotal:,.0f}", 0, 1, "R")
    pdf.set_x(130)
    pdf.cell(45, 8, "VAT (PPN 11%)",  0, 0, "L")
    pdf.cell(25, 8, f" {ppn:,.0f}",   0, 1, "R")
    pdf.set_x(130)
    pdf.set_fill_color(*COLOR_NAVY)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(70, 10, f" TOTAL IDR {grand_total:,.0f} ", 0, 1, "R", True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*COLOR_NAVY)
    pdf.cell(0, 5, "TERMS & CONDITIONS:", ln=1)
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5,
        "Notes & Payment Terms:\n"
        "1. Prices are subject to change without notice.\n"
        "2. Validity: 7 Days from date of quotation.\n"
        "3. Delivery: Within 1 working day after PO confirmation.\n"
        "4. Payments must be transferred ONLY to the following account:\n"
        "   Bank Name     : Bank Mandiri\n"
        "   Account No.   : 1550010174996\n"
        "   Account Name  : PT THEA THEO STATIONARY"
    )

    pdf.ln(10)
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.cell(130, 5, "", 0, 0)
    pdf.cell(60, 5, "Yours Faithfully,", 0, 1, "C")
    pdf.ln(15)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(*COLOR_NAVY)
    pdf.cell(130, 5, "", 0, 0)
    pdf.cell(60, 5, MARKETING_NAME.upper(), 0, 1, "C")
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(130, 5, "", 0, 0)
    pdf.cell(60, 5, "Sales Consultant", 0, 1, "C")

    return pdf.output(dest="S").encode("latin-1")


# =========================================================
# 9. EXCEL ENGINE
# =========================================================
def generate_excel(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook  = writer.book
        worksheet = workbook.add_worksheet("Quotation")

        fmt_navy_bg    = workbook.add_format({"bg_color": "#002855", "font_color": "white",  "bold": True, "font_size": 18, "valign": "vcenter"})
        fmt_gold_text  = workbook.add_format({"font_color": "#B8860B", "bold": True,          "font_size": 10})
        fmt_white_text = workbook.add_format({"font_color": "white",   "font_size": 9})
        fmt_hdr_tbl    = workbook.add_format({"bg_color": "#002855", "font_color": "white",  "bold": True, "border": 1, "align": "center"})
        fmt_border     = workbook.add_format({"border": 1})
        fmt_money      = workbook.add_format({"border": 1, "num_format": "#,##0"})
        fmt_ttl_lbl    = workbook.add_format({"bold": True, "align": "right"})
        fmt_grand      = workbook.add_format({"bg_color": "#002855", "font_color": "white",  "bold": True, "num_format": "#,##0", "align": "right"})

        worksheet.set_column("A:A", 5)
        worksheet.set_column("B:B", 45)
        worksheet.set_column("C:C", 10)
        worksheet.set_column("D:D", 10)
        worksheet.set_column("E:E", 15)
        worksheet.set_column("F:F", 18)

        for r in range(5):
            worksheet.write_blank(r, 0, "", fmt_navy_bg)
        worksheet.merge_range("B2:F2", COMPANY_NAME, fmt_navy_bg)
        worksheet.write("B3", "  ".join(SLOGAN.upper()), fmt_gold_text)
        worksheet.write("B4", f"{ADDR} | Office: {OFFICE_PHONE}", fmt_white_text)
        worksheet.write("B5", f"WhatsApp: {MARKETING_WA} | Email: {MARKETING_EMAIL}", fmt_white_text)

        worksheet.write("B7", "PREPARED FOR:", fmt_gold_text)
        worksheet.write("B8", nama_cust.upper(), workbook.add_format({"bold": True, "font_size": 12}))
        worksheet.write("B9", f"Attention: {pic}")
        worksheet.write("F7", "QUOTATION", workbook.add_format({"bold": True, "font_size": 20, "align": "right", "font_color": "#002855"}))
        worksheet.write("F8", f"Ref: {no_surat}", workbook.add_format({"align": "right"}))
        worksheet.write("F9", f"Date: {(datetime.utcnow() + timedelta(hours=7)).strftime('%d %B %Y')}", workbook.add_format({"align": "right"}))

        for col_num, col_name in enumerate(["NO", "DESCRIPTION", "QTY", "UNIT", "PRICE", "TOTAL"]):
            worksheet.write(11, col_num, col_name, fmt_hdr_tbl)

        row_idx = 12
        for i, row in df_order.iterrows():
            worksheet.write(row_idx, 0, i + 1,              fmt_border)
            worksheet.write(row_idx, 1, row["Nama Barang"],  fmt_border)
            worksheet.write(row_idx, 2, row["Qty"],          fmt_border)
            worksheet.write(row_idx, 3, row["Satuan"],       fmt_border)
            worksheet.write(row_idx, 4, row["Harga"],        fmt_money)
            worksheet.write(row_idx, 5, row["Total_Row"],    fmt_money)
            row_idx += 1

        row_idx += 1
        worksheet.write(row_idx, 4, "Sub Total",     fmt_ttl_lbl)
        worksheet.write(row_idx, 5, subtotal,        fmt_money)
        row_idx += 1
        worksheet.write(row_idx, 4, "VAT (PPN 11%)", fmt_ttl_lbl)
        worksheet.write(row_idx, 5, ppn,             fmt_money)
        row_idx += 1
        worksheet.write(row_idx, 4, "GRAND TOTAL",   fmt_ttl_lbl)
        worksheet.write(row_idx, 5, grand_total,     fmt_grand)

    return output.getvalue()


# =========================================================
# 10. UI UTAMA
# =========================================================
st.sidebar.title(f"Portal {MARKETING_NAME}")
menu = st.sidebar.selectbox("Pilih Menu:", ["🏠 Home", "📝 Admin Sales", "👨‍💻 Sales Dashboard"])

# ─────────────────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────────────────
if menu == "🏠 Home":
    st.title(f"Selamat Datang di {COMPANY_NAME}")
    st.info(f"Marketing Aktif: **{MARKETING_NAME}** | 📞 {MARKETING_WA}")
    if df_barang.empty:
        st.warning(
            "⚠️ Database barang kosong atau belum diupload. "
            "Silakan masuk ke **Sales Dashboard → Update Database (.csv)**."
        )

# ─────────────────────────────────────────────────────────
# ADMIN SALES (PORTAL CUSTOMER)
# ─────────────────────────────────────────────────────────
elif menu == "📝 Admin Sales":
    st.subheader("Form Pengajuan Penawaran")

    if df_barang.empty:
        st.error("❌ Database barang belum tersedia. Hubungi tim sales.")
        st.stop()

    with st.container(border=True):
        col1, col2 = st.columns(2)
        nama_toko = col1.text_input("🏢 Nama Perusahaan / Toko")
        up_nama   = col2.text_input("👤 Nama Penerima (UP)")
        wa_nomor  = col1.text_input("📞 Nomor WhatsApp (contoh: 08123456789)")
        if wa_nomor and not validate_wa(wa_nomor):
            st.warning("⚠️ Nomor WhatsApp tidak valid. Masukkan angka saja, 9-15 digit.")

    with st.container(border=True):
        st.markdown("### 📦 Tambah Barang")
        pilihan_barang = st.selectbox(
            "Cari Nama Barang (Ketik di sini):",
            options=[""] + df_barang["Nama Barang"].tolist(),
            key=f"pilih_brg_{st.session_state.widget_id}",
            help="Ketik nama barang untuk mencari"
        )

        if pilihan_barang:
            row_m     = df_barang[df_barang["Nama Barang"] == pilihan_barang].iloc[0]
            h_master  = float(row_m["Harga"])
            satuan_db = str(row_m["Satuan"]).strip()

            c1, c2, c3 = st.columns([1.5, 1, 1])
            mode_c = c1.selectbox(
                f"Pilih Satuan (Default: {satuan_db})",
                ["Sesuai Database", "Lusin (12)", "Dus", "Box", "Pack", "Set"],
                key=f"m_c_{st.session_state.widget_id}"
            )

            mult_c    = 1
            sat_final = satuan_db
            if mode_c == "Lusin (12)":
                mult_c    = 12
                sat_final = "Lusin"
            elif mode_c in ["Dus", "Box", "Pack", "Set"]:
                isi_c     = c2.number_input(f"Isi per {mode_c}", min_value=1, value=10, key=f"isi_c_{st.session_state.widget_id}")
                mult_c    = isi_c
                sat_final = mode_c

            qty_c    = c3.number_input(f"Jumlah {sat_final}", min_value=1, value=1, key=f"qty_c_{st.session_state.widget_id}")
            h_jual_c = int(h_master * mult_c)
            st.info(f"Harga Penawaran: **Rp {h_jual_c:,.0f} / {sat_final}**")

            if st.button("➕ Masukkan ke Daftar Pesanan", use_container_width=True):
                st.session_state.cart = [i for i in st.session_state.cart if i["Nama Barang"] != pilihan_barang]
                st.session_state.cart.append({
                    "Nama Barang": pilihan_barang,
                    "Qty":         int(qty_c),
                    "Harga":       float(h_jual_c),
                    "Satuan":      sat_final,
                    "Total_Row":   float(qty_c * h_jual_c)
                })
                st.session_state.widget_id += 1
                st.toast(f"✅ Berhasil ditambah: {pilihan_barang}")
                time.sleep(0.2)
                st.rerun()
        else:
            st.write("👆 Silakan pilih atau ketik nama barang dulu.")

    if st.session_state.cart:
        st.markdown("### 📋 Daftar Pesanan Anda")
        total_p = 0
        for i, item in enumerate(st.session_state.cart):
            with st.container(border=True):
                ca, cb, cc, cd = st.columns([3, 1.5, 1.5, 0.5])
                ca.markdown(f"**{item['Nama Barang']}**")
                cb.markdown(f"{item['Qty']} {item['Satuan']} (@Rp {item['Harga']:,.0f})")
                cc.markdown(f"**Rp {item['Total_Row']:,.0f}**")
                if cd.button("❌", key=f"del_item_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
                total_p += item["Total_Row"]

        st.divider()
        if st.button(f"🚀 KIRIM PENAWARAN KE PAK {MARKETING_NAME.upper()}", use_container_width=True, type="primary"):
            errors = []
            if not nama_toko:
                errors.append("Nama Toko/Perusahaan wajib diisi.")
            if wa_nomor and not validate_wa(wa_nomor):
                errors.append("Nomor WhatsApp tidak valid.")
            if errors:
                for err in errors:
                    st.error(f"❌ {err}")
            else:
                sheet = get_sheet()
                if sheet:
                    wkt = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M")
                    sheet.append_row([wkt, nama_toko, up_nama, wa_nomor, pesanan_to_json(st.session_state.cart), "Pending", MARKETING_NAME])
                    load_sheet_data.clear()   # refresh cache setelah tulis
                    logger.info(f"Penawaran dikirim: {nama_toko}")
                    st.balloons()
                    st.success("✅ Penawaran berhasil dikirim!")
                    st.session_state.cart = []
                    time.sleep(1)
                    st.rerun()

# ─────────────────────────────────────────────────────────
# SALES DASHBOARD
# ─────────────────────────────────────────────────────────
elif menu == "👨‍💻 Sales Dashboard":
    st.title(f"Sales Dashboard — {MARKETING_NAME}")

    pwd = st.sidebar.text_input("Password:", type="password")
    if not st.session_state.authenticated:
        check_auth(pwd)
    if not st.session_state.authenticated:
        st.info("🔐 Masukkan password di sidebar untuk mengakses dashboard.")
        st.stop()

    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()

    # --- UPLOAD DATABASE ---
    with st.sidebar.expander("📁 Update Database (.csv)", expanded=False):
        up_f = st.file_uploader("Pilih file CSV", type=["csv"], key="admin_csv_up")
        if up_f and st.button("🚀 Update Sekarang"):
            with open("database_barang.csv", "wb") as f:
                f.write(up_f.getbuffer())
            load_db.clear()
            st.success("✅ Database terupdate!")
            logger.info("Database CSV diupdate.")
            time.sleep(1)
            st.rerun()

    # Tombol refresh manual (berguna jika ada pesanan masuk saat dashboard terbuka)
    if st.sidebar.button("🔄 Refresh Data"):
        load_sheet_data.clear()
        st.rerun()

    # ── Ambil data — SATU kali dari cache, semua operasi pakai ini ──
    df_gs = load_sheet_data()

    if df_gs.empty:
        st.info(f"Antrean bersih, Pak {MARKETING_NAME}! 🎉")
        st.stop()

    tab_pending, tab_riwayat = st.tabs(["📋 Antrean Pending", "📜 Riwayat Processed"])

    # ── TAB 1: PENDING ──────────────────────────────────────────────
    with tab_pending:
        pending = df_gs[(df_gs["Status"] == "Pending") & (df_gs["Sales"] == MARKETING_NAME)]

        if pending.empty:
            st.info(f"Antrean bersih, Pak {MARKETING_NAME}! 🎉")
        else:
            for idx in pending.index:
                row = df_gs.loc[idx]
                # row index di GSheet = idx + 2 (header di baris 1, data mulai baris 2, pandas 0-indexed)
                gsheet_row = idx + 2
                items_list = json_to_pesanan(str(row["Pesanan"]))

                with st.expander(f"🛠️ KELOLA: {row['Customer']}", expanded=True):
                    if not items_list:
                        st.warning("⚠️ Data pesanan tidak dapat dibaca.")
                        continue

                    st.write("### 📝 Edit Daftar Barang")
                    temp_up = []

                    for i, r in enumerate(items_list):
                        row_master        = df_barang[df_barang["Nama Barang"] == r["Nama Barang"]]
                        harga_master_asli = float(row_master["Harga"].values[0]) if not row_master.empty else float(r["Harga"])
                        u_k               = f"r{gsheet_row}_i{i}"

                        with st.container(border=True):
                            c1, c2, c3, c4, c5, c6 = st.columns([2.0, 1.1, 1.2, 1.3, 0.8, 0.4])
                            c1.markdown(f"**{r['Nama Barang']}**")
                            c1.caption(f"Master CSV: Rp {harga_master_asli:,.0f}")

                            list_mode = ["Pcs/Tetap", "Lusin (12)", "Dus", "Box", "Pack", "Set", "Rim"]
                            mode      = c2.selectbox("Ubah Satuan?", list_mode, key=f"m_{u_k}")

                            if mode == "Pcs/Tetap":
                                mult       = 1
                                sat_init   = str(r.get("Satuan", "Pcs"))
                                harga_init = int(float(r.get("Harga", harga_master_asli)))
                            elif mode == "Lusin (12)":
                                mult       = 12
                                sat_init   = "Lusin"
                                harga_init = int(harga_master_asli * 12)
                            elif mode == "Rim":
                                mult       = 1
                                sat_init   = "Rim"
                                harga_init = int(harga_master_asli)
                            else:
                                isi_m      = c3.number_input("Isi per...", min_value=1, value=10, key=f"isi_{u_k}")
                                mult       = isi_m
                                sat_init   = mode
                                harga_init = int(harga_master_asli * mult)

                            trigger_val = f"{mode}_{mult}"
                            if st.session_state.get(f"trig_{u_k}") != trigger_val:
                                st.session_state[f"h_{u_k}"] = harga_init
                                st.session_state[f"s_{u_k}"] = sat_init
                                st.session_state[f"trig_{u_k}"] = trigger_val

                            nq     = c2.number_input("Qty",        value=int(r["Qty"]), key=f"q_{u_k}")
                            ns     = c3.text_input("Unit",                              key=f"s_{u_k}")
                            nh     = c4.number_input("Harga Jual", step=500, format="%d", key=f"h_{u_k}")
                            np_val = c5.number_input("Pos",        value=float(i + 1), step=0.1, key=f"p_{u_k}")
                            td     = c6.checkbox("🗑️",             key=f"d_{u_k}")

                            temp_up.append({
                                "del":   td,
                                "pos":   np_val,
                                "Nama":  r["Nama Barang"],
                                "Qty":   nq,
                                "Harga": nh,
                                "Sat":   ns
                            })

                    st.write("---")
                    add_b = st.multiselect(
                        "Tambah Barang Baru:",
                        options=df_barang["Nama Barang"].tolist(),
                        key=f"add_new_{gsheet_row}"
                    )

                    col_save, col_done = st.columns(2)

                    # ── SIMPAN ──────────────────────────────────────
                    if col_save.button("💾 SIMPAN PERUBAHAN", key=f"btn_save_{gsheet_row}", use_container_width=True):
                        final = sorted([x for x in temp_up if not x["del"]], key=lambda x: x["pos"])
                        for p in add_b:
                            rb = df_barang[df_barang["Nama Barang"] == p].iloc[0]
                            final.append({"Nama": p, "Qty": 1, "Harga": float(rb["Harga"]), "Sat": str(rb["Satuan"])})

                        save_data = [
                            {
                                "Nama Barang": x["Nama"],
                                "Qty":         x["Qty"],
                                "Harga":       x["Harga"],
                                "Satuan":      x["Sat"],
                                "Total_Row":   x["Qty"] * x["Harga"]
                            }
                            for x in final
                        ]
                        try:
                            sheet = get_sheet()
                            sheet.update_cell(gsheet_row, 5, pesanan_to_json(save_data))
                            load_sheet_data.clear()   # refresh cache
                            logger.info(f"Data disimpan: {row['Customer']} baris {gsheet_row}")
                            st.success("✅ Tersimpan!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Gagal menyimpan: {e}")
                            logger.error(f"Gagal simpan baris {gsheet_row}: {e}")

                    # ── DOWNLOAD (pakai items_list dari cache, sudah cukup) ────
                    if items_list:
                        f_df = pd.DataFrame(items_list)
                        if "Total_Row" not in f_df.columns:
                            f_df["Total_Row"] = f_df["Qty"].astype(float) * f_df["Harga"].astype(float)

                        subt, tax, gtot = hitung_total(items_list)

                        st.markdown("### 🖨️ Menu Print & Download")
                        st.caption("💡 Klik **Simpan** dulu sebelum download agar data selalu terbaru.")

                        c_no, c_met = st.columns([2, 1])
                        no_s = c_no.text_input("No Surat:", value="/S-TTS/IV/2026", key=f"ns_print_{gsheet_row}")
                        c_met.metric("Total Quotation", f"Rp {gtot:,.0f}")

                        b1, b2 = st.columns(2)
                        pdf_data = generate_pdf(no_s, row["Customer"], row["UP"], f_df, subt, tax, gtot)
                        b1.download_button(
                            label="📩 DOWNLOAD PDF",
                            data=pdf_data,
                            file_name=f"Quo_{row['Customer']}.pdf",
                            key=f"btn_p_{gsheet_row}",
                            use_container_width=True
                        )
                        xls_data = generate_excel(no_s, row["Customer"], row["UP"], f_df, subt, tax, gtot)
                        b2.download_button(
                            label="📊 DOWNLOAD EXCEL",
                            data=xls_data,
                            file_name=f"{row['Customer']}.xlsx",
                            key=f"btn_x_{gsheet_row}",
                            use_container_width=True
                        )

                    # ── SELESAI ──────────────────────────────────────
                    if col_done.button(
                        "✅ PENAWARAN SELESAI",
                        key=f"done_btn_{gsheet_row}",
                        type="primary",
                        use_container_width=True
                    ):
                        try:
                            sheet = get_sheet()
                            sheet.update_cell(gsheet_row, 6, "Processed")
                            load_sheet_data.clear()
                            logger.info(f"Penawaran selesai: {row['Customer']} baris {gsheet_row}")
                            st.success("✅ Penawaran Selesai!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Gagal update status: {e}")
                            logger.error(f"Gagal update status baris {gsheet_row}: {e}")

    # ── TAB 2: RIWAYAT ──────────────────────────────────────────────
    with tab_riwayat:
        processed = df_gs[(df_gs["Status"] == "Processed") & (df_gs["Sales"] == MARKETING_NAME)]

        if processed.empty:
            st.info("Belum ada penawaran yang diproses.")
        else:
            search_q = st.text_input("🔍 Cari nama customer:", key="search_riwayat")
            if search_q:
                processed = processed[processed["Customer"].str.contains(search_q, case=False, na=False)]

            st.write(f"**{len(processed)} penawaran ditemukan.**")

            for idx in processed.index:
                row        = df_gs.loc[idx]
                gsheet_row = idx + 2
                items_list = json_to_pesanan(str(row["Pesanan"]))
                subt, tax, gtot = hitung_total(items_list) if items_list else (0, 0, 0)

                with st.expander(f"✅ {row['Customer']} — {row['Waktu']} | Total: Rp {gtot:,.0f}"):
                    st.write(f"**UP:** {row['UP']} | **WA:** {row['WA']}")

                    if items_list:
                        f_df = pd.DataFrame(items_list)
                        if "Total_Row" not in f_df.columns:
                            f_df["Total_Row"] = f_df["Qty"].astype(float) * f_df["Harga"].astype(float)
                        st.dataframe(
                            f_df[["Nama Barang", "Qty", "Satuan", "Harga", "Total_Row"]],
                            use_container_width=True
                        )

                        c_no2, _ = st.columns([2, 1])
                        no_s2    = c_no2.text_input("No Surat:", value="/S-TTS/IV/2026", key=f"ns_rw_{gsheet_row}")

                        b1r, b2r = st.columns(2)
                        pdf_data2 = generate_pdf(no_s2, row["Customer"], row["UP"], f_df, subt, tax, gtot)
                        b1r.download_button(label="📩 PDF",   data=pdf_data2, file_name=f"Quo_{row['Customer']}.pdf", key=f"btn_rw_p_{gsheet_row}", use_container_width=True)
                        xls_data2 = generate_excel(no_s2, row["Customer"], row["UP"], f_df, subt, tax, gtot)
                        b2r.download_button(label="📊 Excel", data=xls_data2, file_name=f"{row['Customer']}.xlsx",    key=f"btn_rw_x_{gsheet_row}", use_container_width=True)

                    if st.button("↩️ Kembalikan ke Pending", key=f"reopen_{gsheet_row}"):
                        try:
                            sheet = get_sheet()
                            sheet.update_cell(gsheet_row, 6, "Pending")
                            load_sheet_data.clear()
                            st.success("✅ Dikembalikan ke Pending!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Gagal: {e}")
                            logger.error(f"Gagal reopen baris {gsheet_row}: {e}")
