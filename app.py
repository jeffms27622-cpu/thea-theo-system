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
import hashlib
import urllib.parse
from streamlit_searchbox import st_searchbox
from rapidfuzz import process, fuzz

COMPANY_NAME = "PT. THEA THEO STATIONARY"
SLOGAN = "Office & School Supplies Solution"
ADDR = "Komp. Ruko Modernland Cipondoh Blok. AR No. 27, Tangerang"
OFFICE_PHONE = "(021) 55780659"

# ── Akun Sales & Marketing (login per-orang, password beda-beda) ──
def _load_users():
    if "users" in st.secrets:
        return {uname: dict(cfg) for uname, cfg in st.secrets["users"].items()}
    return {
        "asin": {
            "password": "asin123", "name": "Asin", "title": "Koordinator Sales & Marketing",
            "wa": "0815-8199-775", "email": "alattulis.tts@gmail.com",
        },
        "artini": {
            "password": "artini123", "name": "Artini", "title": "Sales Executive",
            "wa": "08xx-xxxx-xxxx", "email": "artini.tts@gmail.com",
        },
        "topan": {
            "password": "topan123", "name": "Topan", "title": "Sales Executive",
            "wa": "08xx-xxxx-xxxx", "email": "topan.tts@gmail.com",
        },
    }

USERS = _load_users()

COLOR_NAVY = (0, 40, 85)
COLOR_GOLD = (184, 134, 11)
COLOR_TEXT = (30, 30, 30)

ROMAN_MONTHS = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

st.set_page_config(
    page_title=COMPANY_NAME,
    layout="wide",
    page_icon="📎",
    initial_sidebar_state="collapsed",
)

# =========================================================
# MODERN UI CSS
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
    -webkit-tap-highlight-color: transparent;
    -webkit-text-size-adjust: 100%;
}
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

.stApp {
    background: linear-gradient(150deg, #f3f6fb 0%, #eaeff7 55%, #f6f2ea 100%);
    min-height: 100vh;
}

.block-container {
    padding: 0.75rem 1rem 3rem 1rem !important;
    max-width: 100% !important;
}
@media (min-width: 768px) {
    .block-container {
        padding: 1.25rem 2.5rem 3.5rem 2.5rem !important;
        max-width: 1320px !important;
        margin: 0 auto !important;
    }
}

/* ── Styled Native Border Containers ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border-radius: 14px !important;
    border: 1px solid #dde6f0 !important;
    box-shadow: 0 4px 16px rgba(0, 40, 85, 0.05) !important;
    padding: 4px !important;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #c5d4e6 !important;
    box-shadow: 0 6px 22px rgba(0, 40, 85, 0.08) !important;
}

/* ── Hero Header ── */
.top-header {
    background: linear-gradient(135deg, #002248 0%, #003b75 60%, #002855 100%);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 18px;
    border-bottom: 4px solid #B8860B;
    box-shadow: 0 10px 28px rgba(0, 40, 85, 0.22);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
}
.top-header-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.45rem;
    font-weight: 700;
    color: #ffffff !important;
    margin: 0;
    line-height: 1.25;
}
.top-header-subtitle {
    font-size: 0.74rem;
    color: #f0c040 !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 600;
    margin-top: 4px;
}
.top-header-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(240, 192, 64, 0.6);
    color: #ffda6b !important;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
@media (min-width: 768px) {
    .top-header { padding: 24px 32px; }
    .top-header-title { font-size: 1.85rem; }
}

/* ── Section Title ── */
.section-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.98rem;
    color: #002855 !important;
    font-weight: 800;
    border-left: 4px solid #B8860B;
    padding-left: 10px;
    margin: 14px 0 10px 0;
    letter-spacing: 0.02em;
}

/* ── User Status Pill Bar ── */
.user-bar {
    background: #ffffff;
    border: 1px solid #dce6f2;
    border-left: 4px solid #002855;
    border-radius: 12px;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    box-shadow: 0 2px 10px rgba(0,40,85,0.04);
}
.user-bar-info {
    font-size: 0.85rem;
    color: #1e293b;
    font-weight: 600;
}
.user-bar-role {
    display: inline-block;
    background: #eef4fb;
    color: #002855;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 99px;
    margin-left: 6px;
    border: 1px solid #cbdcf0;
}

/* ── Inputs & Selectboxes ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    color: #1e1e1e !important;
    border-radius: 10px !important;
    border: 1.5px solid #cbd5e1 !important;
    background: #ffffff !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 10px 14px !important;
    min-height: 44px !important;
}
.stTextInput > div > div > input::placeholder,
.stNumberInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #94a3b8 !important;
    opacity: 1 !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #002855 !important;
    box-shadow: 0 0 0 3px rgba(0,40,85,0.12) !important;
    outline: none !important;
}

[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    border-radius: 10px !important;
    border: 1.5px solid #cbd5e1 !important;
    background: white !important;
    color: #1e1e1e !important;
    min-height: 44px !important;
}
[data-testid="stSelectbox"] span,
[data-testid="stMultiSelect"] span,
[data-testid="stSelectbox"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSelectbox"] div[role="combobox"] p,
[data-baseweb="select"] div[data-testid="stMarkdownContainer"] p {
    color: #1e1e1e !important;
}

[data-baseweb="select"] [data-baseweb="option"],
[data-baseweb="popover"] li,
ul[role="listbox"] li {
    color: #1e1e1e !important;
    background: white !important;
    padding: 10px 14px !important;
    font-size: 0.92rem !important;
}

[data-baseweb="select"] input,
[data-baseweb="select"] input[type="text"],
[data-testid="stSelectbox"] input,
[data-testid="stMultiSelect"] input,
div[data-baseweb="select"] div input {
    color: #1e1e1e !important;
    -webkit-text-fill-color: #1e1e1e !important;
    background: white !important;
    caret-color: #1e1e1e !important;
}
[data-baseweb="select"] input::placeholder,
[data-testid="stSelectbox"] input::placeholder,
[data-testid="stMultiSelect"] input::placeholder {
    color: #94a3b8 !important;
    -webkit-text-fill-color: #94a3b8 !important;
}

/* ── Labels ── */
section.main .stTextInput label,
section.main .stSelectbox label,
section.main .stNumberInput label,
section.main .stMultiSelect label,
section.main .stCheckbox label,
section.main .stTextArea label,
div[data-testid="stForm"] label {
    font-weight: 700 !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    color: #002855 !important;
}

/* ── Buttons ── */
.stButton > button,
.stFormSubmitButton > button {
    min-height: 44px !important;
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.04em !important;
    transition: all 0.18s ease !important;
    cursor: pointer !important;
    width: 100% !important;
}
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, #002855 0%, #004080 100%) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(0,40,85,0.25) !important;
    border-bottom: 3px solid #B8860B !important;
}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(0,40,85,0.35) !important;
}
.stButton > button:not([kind="primary"]),
.stFormSubmitButton > button:not([kind="primary"]) {
    background: #ffffff !important;
    color: #002855 !important;
    border: 1.5px solid #c5d4e6 !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: #002855 !important;
    background: #f4f8fc !important;
}

.stDownloadButton > button {
    min-height: 46px !important;
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    width: 100% !important;
}

/* ── WhatsApp Link Button ── */
.wa-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 46px;
    background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
    color: #ffffff !important;
    font-weight: 700;
    font-size: 0.82rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    text-decoration: none !important;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(22, 163, 74, 0.25);
    border-bottom: 3px solid #14532d;
    transition: all 0.2s ease;
}
.wa-btn:hover {
    opacity: 0.95;
    transform: translateY(-1px);
}

/* ── Expanders & Metrics ── */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, #f8fafd 0%, #eef4fb 100%) !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    color: #002855 !important;
    font-size: 0.9rem !important;
    border: 1px solid #d5e3f2 !important;
}

[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #e0e8f0 !important;
    border-radius: 14px !important;
    padding: 12px 16px !important;
    box-shadow: 0 2px 10px rgba(0,40,85,0.05) !important;
    border-top: 3px solid #B8860B !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: #64748b !important;
}
[data-testid="stMetricValue"] {
    font-weight: 800 !important;
    color: #002855 !important;
    font-size: 1.15rem !important;
}
@media (min-width: 768px) {
    [data-testid="stMetricValue"] { font-size: 1.45rem !important; }
}

/* ── Price Preview Box ── */
.price-info-box {
    background: linear-gradient(135deg, #002855, #003e80);
    color: white !important;
    border-radius: 12px;
    padding: 14px 18px;
    font-weight: 600;
    font-size: 0.88rem;
    border-left: 4px solid #B8860B;
    box-shadow: 0 4px 14px rgba(0,40,85,0.2);
    margin: 10px 0;
    line-height: 1.7;
}
.price-info-box span { color: #ffda6b !important; font-weight: 800; font-size: 1.02rem; }

/* ── Feature Card ── */
.feature-card {
    background: white;
    border-radius: 14px;
    padding: 20px 16px 12px 16px;
    border: 1px solid #e2e8f0;
    border-top: 4px solid #B8860B;
    box-shadow: 0 4px 14px rgba(0,40,85,0.05);
    text-align: center;
    margin-bottom: 8px;
}
.feature-card .icon { font-size: 2.1rem; margin-bottom: 8px; }
.feature-card h4 { color: #002855 !important; font-weight: 800; font-size: 1rem; margin-bottom: 6px; }
.feature-card p { color: #64748b !important; font-size: 0.8rem; line-height: 1.5; margin: 0; min-height: 40px; }

/* ── Badges ── */
.pill-badge {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-right: 6px;
}
.pill-master { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
.pill-saved { background: #fef9c3; color: #854d0e; border: 1px solid #fde047; }
.pill-sub { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }

section.main .stMarkdown p,
section.main .stMarkdown strong,
section.main [data-testid="stMarkdownContainer"] p,
section.main [data-testid="stMarkdownContainer"] strong { color: #1e293b; }
section.main [data-testid="stCaptionContainer"] p,
section.main .stCaption p { color: #64748b !important; }

hr {
    border: none !important;
    background: linear-gradient(90deg, transparent, #cbd5e1, transparent) !important;
    height: 1.5px !important;
    margin: 14px 0 !important;
}
[data-testid="stToast"] {
    background: #002855 !important;
    color: white !important;
    border-left: 4px solid #B8860B !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# HELPERS & DATA LOADERS
# =========================================================
def get_wib_now():
    return datetime.utcnow() + timedelta(hours=7)

def default_nomor_surat(seq_num=None):
    now = get_wib_now()
    roman = ROMAN_MONTHS[now.month]
    prefix = f"{seq_num:03d}" if seq_num else ""
    return f"{prefix}/S-TTS/{roman}/{now.year}"

def format_wa_link(phone_raw, customer_name, pic_name, grand_total):
    digits = "".join(ch for ch in str(phone_raw) if ch.isdigit())
    if not digits:
        return None
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif not digits.startswith("62"):
        digits = "62" + digits
    sapaan = f"Bapak/Ibu {pic_name}" if pic_name else str(customer_name)
    msg = (
        f"Halo {sapaan} ({customer_name}),\n\n"
        f"Berikut kami lampirkan Surat Penawaran Harga (Quotation) dari *{COMPANY_NAME}* "
        f"dengan total penawaran sebesar *Rp {grand_total:,.0f}*.\n\n"
        f"Silakan ditinjau, apabila ada item atau kuantitas yang ingin disesuaikan silakan kabari kami. Terima kasih."
    )
    return f"https://wa.me/{digits}?text={urllib.parse.quote(msg)}"

def render_header(title, subtitle="", right_badge=""):
    badge_html = f'<div class="top-header-badge">{right_badge}</div>' if right_badge else ""
    st.markdown(f"""
    <div class="top-header">
        <div>
            <div class="top-header-title">{title}</div>
            <div class="top-header-subtitle">{subtitle if subtitle else SLOGAN}</div>
        </div>
        {badge_html}
    </div>
    """, unsafe_allow_html=True)

def render_section_title(text):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)

def get_creds():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)

SHEET_HEADERS = ["Waktu", "Customer", "UP", "WA", "Pesanan", "Status", "Sales"]

@st.cache_resource(show_spinner=False)
def get_user_worksheet(username):
    """Buka (atau buat baru kalau belum ada) tab Google Sheets khusus milik `username`."""
    try:
        client = gspread.authorize(get_creds())
        spreadsheet = client.open("Antrean Penawaran TTS")
    except Exception as e:
        st.error(f"Koneksi GSheets Gagal: {e}")
        return None

    cfg = USERS.get(username, {})
    display_name = str(cfg.get("name", username)).strip().replace(" ", "_")
    sheet_title = f"Antrean_{display_name}"

    try:
        ws = spreadsheet.worksheet(sheet_title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=sheet_title, rows=500, cols=len(SHEET_HEADERS))
        ws.append_row(SHEET_HEADERS)

    if not ws.get_all_values():
        ws.append_row(SHEET_HEADERS)

    return ws

REQUIRED_DB_COLS = ['Nama Barang', 'Harga', 'Satuan']

def _normalize_col(c):
    c = str(c).replace('\ufeff', '').strip()
    c = c.replace('_', ' ')
    c = ' '.join(c.split())
    return c

def _try_read_csv(path, sep):
    kwargs = dict(engine='python', on_bad_lines='skip')
    kwargs['sep'] = sep
    return pd.read_csv(path, **kwargs)

@st.cache_data(ttl=300)
def load_db():
    empty_df = pd.DataFrame(columns=REQUIRED_DB_COLS)
    if not os.path.exists("database_barang.csv"):
        return empty_df

    for sep in (None, ',', ';', '\t'):
        try:
            df = _try_read_csv("database_barang.csv", sep)
            df.columns = [_normalize_col(c) for c in df.columns]

            col_map = {c.lower(): c for c in df.columns}
            rename_dict = {}
            for req in REQUIRED_DB_COLS:
                if req.lower() in col_map:
                    rename_dict[col_map[req.lower()]] = req
            df = df.rename(columns=rename_dict)

            if all(req in df.columns for req in REQUIRED_DB_COLS):
                df['Harga'] = pd.to_numeric(df['Harga'], errors='coerce').fillna(0)
                df['Nama Barang'] = df['Nama Barang'].astype(str).str.strip()
                df['Satuan'] = df['Satuan'].astype(str).str.strip()
                return df
        except Exception:
            continue

    try:
        preview_cols = list(pd.read_csv("database_barang.csv", sep=None, engine='python',
                                        on_bad_lines='skip', nrows=0).columns)
    except Exception:
        preview_cols = []
    st.error(
        "⚠️ Gagal membaca database_barang.csv: kolom wajib "
        f"{REQUIRED_DB_COLS} tidak ditemukan. Kolom yang terbaca: {preview_cols}. "
        "Pastikan header CSV persis bernama 'Nama Barang', 'Harga', 'Satuan'."
    )
    return empty_df

df_barang = load_db()
_ALL_NAMA_BARANG = df_barang['Nama Barang'].tolist()

def search_barang(searchterm: str):
    if not searchterm or len(searchterm) < 2:
        return []
    kw = searchterm.strip().lower()

    substring_matches = [n for n in _ALL_NAMA_BARANG if kw in n.lower()]
    if substring_matches:
        return substring_matches[:100]

    fuzzy_matches = process.extract(searchterm, _ALL_NAMA_BARANG, scorer=fuzz.WRatio, limit=50)
    return [m[0] for m in fuzzy_matches if m[1] > 35]

def item_key(row_idx, nama_barang):
    h = hashlib.md5(nama_barang.encode()).hexdigest()[:8]
    return f"r{row_idx}_{h}"

def clear_row_state(real_row_idx):
    keys_to_del = [k for k in list(st.session_state.keys()) if k.startswith(f"r{real_row_idx}_")]
    for k in keys_to_del:
        del st.session_state[k]

def read_row_fresh(sheet, row_idx):
    try:
        vals = sheet.row_values(row_idx)
        if len(vals) > 4 and vals[4].strip():
            return ast.literal_eval(vals[4])
        return []
    except Exception:
        return []

def save_to_gsheet_verified(sheet, row_idx, save_data):
    try:
        sheet.update_cell(row_idx, 5, str(save_data))
        time.sleep(0.8)
        verify = sheet.row_values(row_idx)
        if len(verify) > 4:
            try:
                parsed = ast.literal_eval(verify[4])
                if len(parsed) == len(save_data):
                    return True, "OK"
                else:
                    return False, f"Jumlah item tidak cocok: {len(parsed)} vs {len(save_data)}"
            except Exception:
                return False, "Gagal parse data setelah simpan"
        return False, "Row kosong setelah simpan"
    except Exception as e:
        return False, str(e)


# =========================================================
# SESSION STATE
# =========================================================
if "active_menu" not in st.session_state:
    st.session_state.active_menu = "🏠 Home"
if "cart" not in st.session_state:
    st.session_state.cart = []
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None
if "widget_id" not in st.session_state:
    st.session_state.widget_id = 0
if "saved_items_cache" not in st.session_state:
    st.session_state.saved_items_cache = {}


# =========================================================
# AUTH & USER PROFILE
# =========================================================
def current_profile():
    u = st.session_state.auth_user
    if u and u in USERS:
        cfg = USERS[u]
        return cfg.get("name", ""), cfg.get("title", ""), cfg.get("wa", ""), cfg.get("email", "")
    return "", "", "", ""

MARKETING_NAME, MARKETING_TITLE, MARKETING_WA, MARKETING_EMAIL = current_profile()

TTD_FILES = {
    "asin": "ttd_clean.png",
    "artini": "ttd_artini.png",
    "topan": "ttd_topan.png",
}
_ttd_candidate = TTD_FILES.get(st.session_state.auth_user, "ttd_clean.png")
TTD_PATH = _ttd_candidate if os.path.exists(_ttd_candidate) else "ttd_clean.png"

def require_login():
    """Tampilkan form login dengan dukungan tombol Enter (st.form)."""
    if st.session_state.auth_user:
        return True

    st.markdown("<br>", unsafe_allow_html=True)
    _, mid_col, _ = st.columns([1, 1.6, 1])
    with mid_col:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align:center; padding: 12px 0 18px 0;">
                <div style="font-size:2.6rem; line-height:1;">🔐</div>
                <div style="font-family:'Playfair Display',serif;font-size:1.3rem;color:#002855;font-weight:700;margin-top:8px;">
                    Portal Login Sales
                </div>
                <div style="font-size:0.82rem;color:#64748b;margin-top:4px;">
                    Masuk dengan akun Sales & Marketing Anda (tekan Enter untuk masuk)
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.form("login_form_unified", clear_on_submit=False):
                uname_input = st.text_input("👤 Username", placeholder="Contoh: asin / artini / topan")
                pwd_input = st.text_input("🔑 Password", type="password", placeholder="Masukkan password...")
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                submitted = st.form_submit_button("🚀 MASUK SEKARANG", use_container_width=True, type="primary")

                if submitted:
                    uname_clean = uname_input.strip().lower()
                    cfg = USERS.get(uname_clean)
                    if cfg and pwd_input == cfg.get("password"):
                        st.session_state.auth_user = uname_clean
                        st.session_state.pop("gs_all_vals", None)
                        st.toast(f"Selamat datang, {cfg.get('name')}!")
                        st.rerun()
                    else:
                        st.error("❌ Username atau password salah. Silakan periksa kembali.")
    return False


# =========================================================
# TOP NAVIGATION BAR & USER STATUS BAR
# =========================================================
cart_count = len(st.session_state.cart)
admin_label = f"📝 Admin Sales ({cart_count})" if cart_count > 0 else "📝 Admin Sales"

with st.container(border=True):
    nc1, nc2, nc3 = st.columns(3)
    with nc1:
        if st.button("🏠 Beranda", key="nav_home", use_container_width=True,
                     type="primary" if st.session_state.active_menu == "🏠 Home" else "secondary"):
            st.session_state.active_menu = "🏠 Home"
            st.rerun()
    with nc2:
        if st.button(admin_label, key="nav_admin", use_container_width=True,
                     type="primary" if st.session_state.active_menu == "📝 Admin Sales" else "secondary"):
            st.session_state.active_menu = "📝 Admin Sales"
            st.rerun()
    with nc3:
        if st.button("📊 Sales Dashboard", key="nav_dash", use_container_width=True,
                     type="primary" if st.session_state.active_menu == "👨‍💻 Sales Dashboard" else "secondary"):
            st.session_state.active_menu = "👨‍💻 Sales Dashboard"
            st.rerun()

# Tampilkan bar profil ringkas jika sedang login
if st.session_state.auth_user:
    u_col1, u_col2 = st.columns([5, 1])
    with u_col1:
        st.markdown(
            f"""<div class="user-bar">
                <div class="user-bar-info">
                    🟢 Aktif sebagai: <strong>{MARKETING_NAME}</strong>
                    <span class="user-bar-role">{MARKETING_TITLE}</span>
                </div>
                <div style="font-size:0.78rem; color:#64748b;">
                    📞 {MARKETING_WA} &nbsp;|&nbsp; ✉️ {MARKETING_EMAIL}
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
    with u_col2:
        if st.button("🚪 Logout", key="top_logout_btn", use_container_width=True):
            st.session_state.auth_user = None
            st.session_state.pop("gs_all_vals", None)
            st.rerun()

menu = st.session_state.active_menu


# =========================================================
# PDF GENERATOR
# =========================================================
class PenawaranPDF(FPDF):
    def __init__(self, total_pages=1):
        super().__init__()
        self.total_pages = total_pages

    def header(self):
        self.set_fill_color(*COLOR_NAVY)
        self.rect(0, 0, 210, 52, 'F')

        self.set_fill_color(255, 255, 255)
        self.rect(10, 6, 44, 40, 'F')

        self.set_fill_color(*COLOR_GOLD)
        self.rect(58, 0, 3, 52, 'F')

        if os.path.exists("logo.png"):
            self.image("logo.png", 13, 10, 38)

        self.set_y(10); self.set_x(66)
        self.set_font('Arial', 'B', 17)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, COMPANY_NAME, ln=1)

        self.set_x(66)
        self.set_font('Arial', 'B', 8.5)
        self.set_text_color(*COLOR_GOLD)
        self.cell(0, 5, "  ".join(SLOGAN.upper()), ln=1)

        self.set_fill_color(255, 255, 255)
        self.rect(66, 26, 132, 0.3, 'F')

        self.set_y(29); self.set_x(66)
        self.set_font('Arial', '', 7.5)
        self.set_text_color(210, 220, 235)
        self.cell(0, 4.5, ADDR, ln=1)
        self.set_x(66)
        self.cell(0, 4.5, f"Office: {OFFICE_PHONE}  |  WA: {MARKETING_WA}", ln=1)
        self.set_x(66)
        self.cell(0, 4.5, f"Email: {MARKETING_EMAIL}", ln=1)

        self.set_fill_color(*COLOR_GOLD)
        self.rect(0, 52, 210, 2.5, 'F')

        self.set_y(62)

    def footer(self):
        self.set_y(-18)
        self.set_fill_color(*COLOR_GOLD)
        self.rect(0, self.get_y(), 210, 1.5, 'F')

        self.set_fill_color(*COLOR_NAVY)
        self.rect(0, self.get_y() + 1.5, 210, 17, 'F')

        self.set_y(-14)
        self.set_font('Arial', 'B', 8)
        self.set_text_color(255, 255, 255)
        self.cell(0, 5, SLOGAN.upper(), 0, 1, 'C')

        self.set_font('Arial', '', 7)
        self.set_text_color(*COLOR_GOLD)
        self.cell(0, 4,
                  f"{COMPANY_NAME}  |  {ADDR}  |  Hal. {self.page_no()} / {self.total_pages}",
                  0, 0, 'C')


def draw_table_header(pdf):
    pdf.set_fill_color(*COLOR_NAVY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_draw_color(*COLOR_GOLD)
    pdf.set_line_width(0.4)

    pdf.cell(10, 10, 'NO',        border=1, align='C', fill=True)
    pdf.cell(82, 10, 'DESKRIPSI', border=1, align='C', fill=True)
    pdf.cell(18, 10, 'QTY',       border=1, align='C', fill=True)
    pdf.cell(20, 10, 'SATUAN',    border=1, align='C', fill=True)
    pdf.cell(30, 10, 'HARGA',     border=1, align='C', fill=True)
    pdf.cell(30, 10, 'TOTAL',     border=1, align='C', fill=True)
    pdf.ln()


def generate_pdf(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    def _render(pdf):
        pdf.set_margins(10, 70, 10)
        pdf.set_auto_page_break(auto=True, margin=28)
        pdf.add_page()

        pdf.set_y(62)
        pdf.set_font('Arial', 'B', 26)
        pdf.set_text_color(*COLOR_NAVY)
        pdf.cell(0, 10, "QUOTATION", ln=1, align='R')

        pdf.set_draw_color(*COLOR_GOLD)
        pdf.set_line_width(0.8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

        waktu_skrg  = get_wib_now()
        expiry_date = waktu_skrg + timedelta(days=7)
        pdf.set_font('Arial', '', 8.5)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"No. Surat   : {no_surat}", ln=1, align='R')
        pdf.cell(0, 5, f"Tanggal     : {waktu_skrg.strftime('%d %B %Y')}", ln=1, align='R')
        pdf.cell(0, 5, f"Berlaku s/d : {expiry_date.strftime('%d %B %Y')}", ln=1, align='R')
        pdf.ln(4)

        pdf.set_x(10)
        pdf.set_font('Arial', 'B', 7.5)
        pdf.set_text_color(*COLOR_GOLD)
        pdf.cell(90, 5, "DITUJUKAN KEPADA:", ln=1)

        pdf.set_x(10)
        pdf.set_font('Arial', 'B', 13)
        pdf.set_text_color(*COLOR_NAVY)
        pdf.cell(90, 7, str(nama_cust).upper(), ln=1)

        pdf.set_x(10)
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(*COLOR_TEXT)
        pdf.cell(90, 5, f"U/P: {pic}", ln=1)
        pdf.ln(6)

        draw_table_header(pdf)
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(*COLOR_TEXT)

        for i, row in df_order.iterrows():
            if pdf.get_y() > 170:
                pdf.add_page()
                draw_table_header(pdf)
                pdf.set_font('Arial', '', 9)
                pdf.set_text_color(*COLOR_TEXT)

            if i % 2 == 0:
                pdf.set_fill_color(240, 245, 252)
            else:
                pdf.set_fill_color(255, 255, 255)

            pdf.set_draw_color(180, 195, 215)
            pdf.set_line_width(0.2)

            pdf.cell(10, 8, str(i + 1),                    border=1, align='C', fill=True)
            pdf.cell(82, 8, f" {str(row['Nama Barang'])}", border=1, align='L', fill=True)
            pdf.cell(18, 8, str(int(row['Qty'])),          border=1, align='C', fill=True)
            pdf.cell(20, 8, str(row['Satuan']),            border=1, align='C', fill=True)
            pdf.cell(30, 8, f"Rp {row['Harga']:,.0f}",     border=1, align='R', fill=True)
            pdf.cell(30, 8, f"Rp {row['Total_Row']:,.0f}", border=1, align='R', fill=True)
            pdf.ln()

        pdf.ln(4)
        pdf.set_draw_color(*COLOR_GOLD)
        pdf.set_line_width(0.6)
        pdf.line(120, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(*COLOR_TEXT)
        pdf.set_x(120)
        pdf.cell(50, 7, "Sub Total", align='L')
        pdf.cell(30, 7, f"Rp {subtotal:,.0f}", align='R', ln=1)

        if ppn > 0:
            pdf.set_x(120)
            pdf.cell(50, 7, "PPN 11%", align='L')
            pdf.cell(30, 7, f"Rp {ppn:,.0f}", align='R', ln=1)

        pdf.set_draw_color(*COLOR_NAVY)
        pdf.set_line_width(0.4)
        pdf.line(120, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(1)

        pdf.set_fill_color(*COLOR_NAVY)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_x(120)
        pdf.cell(50, 10, "  GRAND TOTAL", border=0, align='L', fill=True)
        pdf.cell(30, 10, f"Rp {grand_total:,.0f}  ", border=0, align='R', fill=True, ln=1)

        pdf.set_draw_color(*COLOR_GOLD)
        pdf.set_line_width(0.8)
        pdf.line(120, pdf.get_y(), 200, pdf.get_y())

        TC_HEIGHT = 62
        BOTTOM_LIMIT = 297 - 28
        if pdf.get_y() + 10 + TC_HEIGHT > BOTTOM_LIMIT:
            pdf.add_page()
            pdf.set_y(68)
        else:
            pdf.ln(10)

        y_tc = pdf.get_y()

        pdf.set_fill_color(248, 250, 253)
        pdf.set_draw_color(*COLOR_NAVY)
        pdf.set_line_width(0.4)
        pdf.rect(10, y_tc, 120, TC_HEIGHT, 'DF')

        pdf.set_y(y_tc + 3)
        pdf.set_x(13)
        pdf.set_font('Arial', 'B', 9)
        pdf.set_text_color(*COLOR_NAVY)
        pdf.cell(116, 5, "SYARAT & KETENTUAN:", ln=1)

        pdf.set_draw_color(*COLOR_GOLD)
        pdf.set_line_width(0.5)
        pdf.line(13, pdf.get_y(), 127, pdf.get_y())
        pdf.ln(2)

        pdf.set_x(13)
        pdf.set_font('Arial', '', 8.5)
        pdf.set_text_color(50, 50, 50)
        terms = (
            "1. Harga dapat berubah sewaktu-waktu tanpa pemberitahuan.\n"
            "2. Penawaran berlaku 7 hari dari tanggal surat.\n"
            "3. Pengiriman 1 hari kerja setelah konfirmasi PO.\n"
            "4. Pembayaran ditransfer HANYA ke rekening berikut:\n"
            "   Bank       : Bank BCA\n"
            "   No. Rek    : 658 033 8818\n"
            "   Atas Nama  : PT THEA THEO STATIONARY"
        )
        pdf.set_x(13)
        pdf.multi_cell(114, 5.5, terms)

        pdf.set_y(y_tc + 3)
        pdf.set_x(138)
        pdf.set_font('Arial', 'B', 8.5)
        pdf.set_text_color(*COLOR_GOLD)
        pdf.cell(60, 5, "Hormat Kami,", ln=1)

        ttd_path = TTD_PATH
        TTD_MAX_W, TTD_MAX_H = 50, 45
        ttd_render_h = 0
        if os.path.exists(ttd_path):
            try:
                from PIL import Image as PILImage
                import numpy as _np
                ttd_img = PILImage.open(ttd_path).convert("RGBA")
                img_to_draw = ttd_path

                if os.path.exists("logo.png"):
                    logo_img = PILImage.open("logo.png").convert("RGBA")
                    lw = int(ttd_img.width * 0.75)
                    lh = int(logo_img.height * lw / logo_img.width)
                    logo_img = logo_img.resize((lw, lh), PILImage.LANCZOS)
                    logo_arr = _np.array(logo_img)
                    logo_arr[:, :, 3] = (logo_arr[:, :, 3] * 0.82).astype(_np.uint8)
                    logo_faded = PILImage.fromarray(logo_arr)
                    lx = (ttd_img.width - lw) // 2
                    ly = max(0, (ttd_img.height - lh) // 2)
                    canvas = ttd_img.copy()
                    canvas.paste(logo_faded, (lx, ly), logo_faded)
                    tmp_path = f"/tmp/ttd_stamp_combined_{os.path.splitext(os.path.basename(ttd_path))[0]}.png"
                    canvas.save(tmp_path)
                    img_to_draw = tmp_path

                aspect_h_per_w = ttd_img.height / ttd_img.width
                render_w = TTD_MAX_W
                render_h = render_w * aspect_h_per_w
                if render_h > TTD_MAX_H:
                    render_h = TTD_MAX_H
                    render_w = render_h / aspect_h_per_w

                pdf.image(img_to_draw, x=133, y=pdf.get_y() + 1, w=render_w, h=render_h)
                ttd_render_h = render_h
            except Exception:
                pdf.image(ttd_path, x=133, y=pdf.get_y() + 1, w=TTD_MAX_W)
                ttd_render_h = TTD_MAX_H
            pdf.set_y(pdf.get_y() + max(ttd_render_h, 10) + 4)
        else:
            pdf.ln(10)

        pdf.set_x(138)
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(*COLOR_NAVY)
        pdf.cell(60, 7, MARKETING_NAME.upper(), ln=1)

        pdf.set_x(138)
        pdf.set_font('Arial', 'I', 8.5)
        pdf.set_text_color(*COLOR_TEXT)
        pdf.cell(60, 4.5, MARKETING_TITLE, ln=1)

        pdf.set_x(138)
        pdf.set_font('Arial', '', 8.5)
        pdf.set_text_color(*COLOR_TEXT)
        pdf.cell(60, 5, f"WA    : {MARKETING_WA}", ln=1)
        pdf.set_x(138)
        pdf.cell(60, 5, f"Email : {MARKETING_EMAIL}", ln=1)

    pdf1 = PenawaranPDF(total_pages=99)
    _render(pdf1)
    total_pages = pdf1.page

    pdf2 = PenawaranPDF(total_pages=total_pages)
    _render(pdf2)

    return pdf2.output(dest='S').encode('latin-1')


# =========================================================
# EXCEL GENERATOR
# =========================================================
def generate_excel(no_surat, nama_cust, pic, df_order, subtotal, ppn, grand_total):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook  = writer.book
        worksheet = workbook.add_worksheet('Quotation')
        fmt_navy_bg      = workbook.add_format({'bg_color': '#002855', 'font_color': 'white', 'bold': True, 'font_size': 18, 'valign': 'vcenter'})
        fmt_gold_text    = workbook.add_format({'font_color': '#B8860B', 'bold': True, 'font_size': 10})
        fmt_white_text   = workbook.add_format({'font_color': 'white', 'font_size': 9})
        fmt_header_table = workbook.add_format({'bg_color': '#002855', 'font_color': 'white', 'bold': True, 'border': 1, 'align': 'center'})
        fmt_border       = workbook.add_format({'border': 1})
        fmt_money        = workbook.add_format({'border': 1, 'num_format': '#,##0'})
        fmt_total_label  = workbook.add_format({'bold': True, 'align': 'right'})
        fmt_grand_total  = workbook.add_format({'bg_color': '#002855', 'font_color': 'white', 'bold': True, 'num_format': '#,##0', 'align': 'right'})
        worksheet.set_column('A:A', 5);  worksheet.set_column('B:B', 45); worksheet.set_column('C:C', 10)
        worksheet.set_column('D:D', 10); worksheet.set_column('E:E', 15); worksheet.set_column('F:F', 18)
        for r in range(0, 5):
            worksheet.write_blank(r, 0, '', fmt_navy_bg)
        worksheet.merge_range('B2:F2', COMPANY_NAME, fmt_navy_bg)
        worksheet.write('B3', "  ".join(SLOGAN.upper()), fmt_gold_text)
        worksheet.write('B4', f"{ADDR} | Office: {OFFICE_PHONE}", fmt_white_text)
        worksheet.write('B5', f"WhatsApp: {MARKETING_WA} | Email: {MARKETING_EMAIL}", fmt_white_text)
        worksheet.write('B7', "PREPARED FOR:", fmt_gold_text)
        worksheet.write('B8', nama_cust.upper(), workbook.add_format({'bold': True, 'font_size': 12}))
        worksheet.write('B9', f"Attention: {pic}")
        worksheet.write('F7', "QUOTATION", workbook.add_format({'bold': True, 'font_size': 20, 'align': 'right', 'font_color': '#002855'}))
        worksheet.write('F8', f"Ref: {no_surat}", workbook.add_format({'align': 'right'}))
        worksheet.write('F9', f"Date: {get_wib_now().strftime('%d %B %Y')}", workbook.add_format({'align': 'right'}))
        header_row = 11
        for col_num, data in enumerate(['NO', 'DESCRIPTION', 'QTY', 'UNIT', 'PRICE', 'TOTAL']):
            worksheet.write(header_row, col_num, data, fmt_header_table)
        row_idx = 12
        for i, row in df_order.iterrows():
            worksheet.write(row_idx, 0, i + 1, fmt_border)
            worksheet.write(row_idx, 1, row['Nama Barang'], fmt_border)
            worksheet.write(row_idx, 2, row['Qty'], fmt_border)
            worksheet.write(row_idx, 3, row['Satuan'], fmt_border)
            worksheet.write(row_idx, 4, row['Harga'], fmt_money)
            worksheet.write(row_idx, 5, row['Total_Row'], fmt_money)
            row_idx += 1
        row_idx += 1
        worksheet.write(row_idx, 4, "Sub Total", fmt_total_label)
        worksheet.write(row_idx, 5, subtotal, fmt_money)
        row_idx += 1
        if ppn > 0:
            worksheet.write(row_idx, 4, "VAT (PPN 11%)", fmt_total_label)
            worksheet.write(row_idx, 5, ppn, fmt_money)
            row_idx += 1
        worksheet.write(row_idx, 4, "GRAND TOTAL", fmt_total_label)
        worksheet.write(row_idx, 5, grand_total, fmt_grand_total)

        worksheet.write(row_idx + 3, 0, MARKETING_NAME, workbook.add_format({'bold': True}))
        worksheet.write(row_idx + 4, 0, MARKETING_TITLE, workbook.add_format({'italic': True, 'font_color': '#002855'}))

    return output.getvalue()


# =========================================================
# 1. HOME PAGE
# =========================================================
if menu == "🏠 Home":
    render_header(COMPANY_NAME, SLOGAN, f"📍 {ADDR.split(',')[0]}")

    # Ringkasan Metrik Atas
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 Katalog Database", f"{len(df_barang):,} SKU")
    m2.metric("🛒 Isi Keranjang", f"{len(st.session_state.cart)} Item")
    m3.metric("🏢 Telepon Kantor", OFFICE_PHONE)
    m4.metric("👤 Status Akun", MARKETING_NAME if st.session_state.auth_user else "Belum Login")

    st.markdown("<br>", unsafe_allow_html=True)
    render_section_title("🚀 Akses Cepat Menu Utama")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">📝</div>
            <h4>Input Penawaran Baru</h4>
            <p>Susun daftar barang pesanan pelanggan, sesuaikan satuan & harga, lalu simpan ke antrean.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Buka Admin Sales →", key="home_go_admin", use_container_width=True, type="primary"):
            st.session_state.active_menu = "📝 Admin Sales"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">📊</div>
            <h4>Kelola Antrean & Cetak</h4>
            <p>Review antrean penawaran, edit urutan atau harga barang, dan unduh PDF / Excel siap kirim.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Buka Sales Dashboard →", key="home_go_dash", use_container_width=True, type="primary"):
            st.session_state.active_menu = "👨‍💻 Sales Dashboard"
            st.rerun()

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon">💬</div>
            <h4>Kirim Cepat ke Pelanggan</h4>
            <p>Dokumen PDF dilengkapi tanda tangan resmi & tombol pintas WhatsApp langsung ke PIC pelanggan.</p>
        </div>
        """, unsafe_allow_html=True)
        if not st.session_state.auth_user:
            if st.button("🔐 Login Akun Sales", key="home_go_login", use_container_width=True):
                st.session_state.active_menu = "📝 Admin Sales"
                st.rerun()
        else:
            st.button(f"✅ Login: {MARKETING_NAME}", disabled=True, use_container_width=True)


# =========================================================
# 2. ADMIN SALES (SPLIT WORKSPACE)
# =========================================================
elif menu == "📝 Admin Sales":
    render_header("Form Penawaran Harga", "Buat & kirim daftar pesanan ke antrean", "📋 Admin Sales")

    if not require_login():
        st.stop()

    # Split Layout: Kiri (Input Pelanggan & Cari Barang) | Kanan (Keranjang Live)
    left_col, right_col = st.columns([1.3, 1], gap="medium")

    with left_col:
        render_section_title("👤 1. Data Pelanggan")
        with st.container(border=True):
            c_cust1, c_cust2 = st.columns(2)
            nama_toko = c_cust1.text_input("🏢 Nama Perusahaan / Toko *", placeholder="PT. Contoh Maju Bersama", key="in_nama_toko")
            up_nama   = c_cust2.text_input("👤 Nama Penerima (UP)", placeholder="Bapak / Ibu ...", key="in_up_nama")
            wa_nomor  = st.text_input("📞 Nomor WhatsApp Pelanggan", placeholder="08xx-xxxx-xxxx (Opsional untuk fitur klik WA)", key="in_wa_nomor")

        render_section_title("📦 2. Tambah Barang ke Keranjang")
        with st.container(border=True):
            tab_db, tab_manual = st.tabs(["🔍 Cari dari Database", "✍️ Input Barang Manual"])

            # ── TAB 1: CARI DARI DATABASE ──
            with tab_db:
                pilihan_barang = st_searchbox(
                    search_barang,
                    placeholder="Ketik nama barang (min. 2 huruf)...",
                    label="Cari & Pilih Nama Barang:",
                    key=f"searchbox_brg_{st.session_state.widget_id}",
                    clear_on_submit=False,
                    style_overrides={
                        "clear": {"width": 18, "height": 18, "icon": "cross", "clearable": "after-submit"},
                        "dropdown": {"width": 26, "height": 26, "fill": "#002855"},
                        "searchbox": {
                            "menuList": {"backgroundColor": "white"},
                            "singleValue": {"color": "#1e1e1e"},
                            "option": {
                                "color": "#1e1e1e",
                                "backgroundColor": "white",
                                "highlightColor": "#B8860B",
                            },
                        },
                    },
                )

                if pilihan_barang:
                    row_m = df_barang[df_barang['Nama Barang'] == pilihan_barang].iloc[0]
                    h_master = float(row_m['Harga'])
                    satuan_db = str(row_m['Satuan']).strip()

                    c1, c2 = st.columns(2)
                    mode_c = c1.selectbox(
                        f"Satuan (Default: {satuan_db})",
                        ["Sesuai Database", "Lusin (12)", "Dus", "Box", "Pack", "Set", "Rim"],
                        key=f"m_c_{st.session_state.widget_id}"
                    )
                    mult_c = 1
                    sat_final = satuan_db
                    if mode_c == "Lusin (12)":
                        mult_c = 12
                        sat_final = "Lusin"
                    elif mode_c == "Rim":
                        mult_c = 1
                        sat_final = "Rim"
                    elif mode_c in ["Dus", "Box", "Pack", "Set"]:
                        isi_c = st.number_input(
                            f"Isi per {mode_c}", min_value=1, value=10,
                            key=f"isi_c_{st.session_state.widget_id}"
                        )
                        mult_c = isi_c
                        sat_final = mode_c

                    qty_c = c2.number_input(
                        f"Jumlah ({sat_final})", min_value=1, value=1,
                        key=f"qty_c_{st.session_state.widget_id}"
                    )

                    default_h_jual = int(h_master * mult_c)
                    h_jual_c = st.number_input(
                        f"Harga Jual per {sat_final} (Rp) — Bisa disesuaikan",
                        min_value=0,
                        value=default_h_jual,
                        step=500,
                        key=f"hj_c_{st.session_state.widget_id}_{mode_c}_{mult_c}"
                    )

                    st.markdown(f"""
                    <div class="price-info-box">
                        📋 Harga Master: Rp {h_master:,.0f} / {satuan_db}<br>
                        💰 Harga Jual: <span>Rp {h_jual_c:,.0f}</span> / {sat_final} &nbsp;|&nbsp;
                        🔢 Qty: <span>{int(qty_c)} {sat_final}</span> &nbsp;|&nbsp;
                        💵 Subtotal: <span>Rp {int(qty_c * h_jual_c):,.0f}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("➕ Masukkan ke Keranjang", use_container_width=True, type="primary", key="btn_add_db"):
                        st.session_state.cart = [x for x in st.session_state.cart if x['Nama Barang'] != pilihan_barang]
                        st.session_state.cart.append({
                            "Nama Barang": pilihan_barang,
                            "Qty": int(qty_c),
                            "Harga": float(h_jual_c),
                            "Satuan": sat_final,
                            "Total_Row": float(qty_c * h_jual_c),
                        })
                        st.session_state.widget_id += 1
                        st.toast(f"✅ Ditambahkan: {pilihan_barang}")
                        time.sleep(0.15)
                        st.rerun()
                else:
                    st.markdown("""
                    <div style="text-align:center; padding:18px 0; color:#64748b;">
                        <div style="font-size:1.8rem; margin-bottom:6px;">🔍</div>
                        <div style="font-size:0.85rem;">Ketik minimal 2 huruf pada kotak pencarian di atas untuk memilih barang.</div>
                    </div>
                    """, unsafe_allow_html=True)

            # ── TAB 2: INPUT BARANG MANUAL (CUSTOM) ──
            with tab_manual:
                st.caption("Gunakan fitur ini jika barang yang diminta pelanggan belum ada di database CSV.")
                with st.form("form_manual_item", clear_on_submit=True):
                    m_nama = st.text_input("Nama Barang Custom", placeholder="Contoh: Kertas Continuous Form 3 Ply")
                    mc1, mc2, mc3 = st.columns(3)
                    m_qty = mc1.number_input("Qty", min_value=1, value=1, step=1)
                    m_sat = mc2.text_input("Satuan", value="Pcs")
                    m_hrg = mc3.number_input("Harga Satuan (Rp)", min_value=0, value=10000, step=500)
                    sub_manual = st.form_submit_button("➕ Tambah Barang Custom", use_container_width=True, type="primary")
                    if sub_manual:
                        if not m_nama.strip():
                            st.warning("⚠️ Nama barang tidak boleh kosong.")
                        else:
                            clean_n = m_nama.strip()
                            st.session_state.cart.append({
                                "Nama Barang": clean_n,
                                "Qty": int(m_qty),
                                "Harga": float(m_hrg),
                                "Satuan": m_sat.strip() or "Pcs",
                                "Total_Row": float(m_qty * m_hrg),
                            })
                            st.toast(f"✅ Barang custom ditambahkan: {clean_n}")
                            st.rerun()

    # ── KOLOM KANAN: KERANJANG LIVE ──
    with right_col:
        render_section_title(f"🛒 3. Keranjang Penawaran ({len(st.session_state.cart)} Item)")
        with st.container(border=True):
            if not st.session_state.cart:
                st.markdown("""
                <div style="text-align:center; padding:42px 16px; color:#64748b;">
                    <div style="font-size:2.6rem; margin-bottom:8px;">🛒</div>
                    <div style="font-weight:700; color:#002855; font-size:0.98rem;">Keranjang Masih Kosong</div>
                    <div style="font-size:0.82rem; margin-top:4px;">Cari dan tambahkan barang dari panel di sebelah kiri.</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                total_cart = sum(x['Total_Row'] for x in st.session_state.cart)
                tax_cart   = total_cart * 0.11
                grand_cart = total_cart + tax_cart

                km1, km2 = st.columns(2)
                km1.metric("💵 Sub Total", f"Rp {total_cart:,.0f}")
                km2.metric("🧾 Total + PPN 11%", f"Rp {grand_cart:,.0f}")

                st.markdown("<hr>", unsafe_allow_html=True)

                for i, item in enumerate(st.session_state.cart):
                    with st.container(border=True):
                        top_c1, top_c2 = st.columns([4, 1])
                        top_c1.markdown(
                            f"<div style='color:#002855;font-weight:700;font-size:0.9rem;line-height:1.3;'>"
                            f"{i+1}. {item['Nama Barang']}</div>"
                            f"<div style='color:#64748b;font-size:0.76rem;margin-top:2px;'>"
                            f"@ Rp {item['Harga']:,.0f} / {item['Satuan']}</div>",
                            unsafe_allow_html=True
                        )
                        if top_c2.button("🗑️", key=f"del_item_{i}", help="Hapus item ini"):
                            st.session_state.cart.pop(i)
                            st.rerun()

                        bot_c1, bot_c2 = st.columns([1.2, 1.8])
                        new_q = bot_c1.number_input(
                            f"Qty ({item['Satuan']})",
                            min_value=1,
                            value=int(item['Qty']),
                            step=1,
                            key=f"cart_qty_{i}_{item['Nama Barang']}",
                            label_visibility="collapsed"
                        )
                        if new_q != item['Qty']:
                            st.session_state.cart[i]['Qty'] = int(new_q)
                            st.session_state.cart[i]['Total_Row'] = float(new_q * item['Harga'])
                            st.rerun()

                        bot_c2.markdown(
                            f"<div style='text-align:right; padding-top:10px; color:#002855; font-weight:800; font-size:0.92rem;'>"
                            f"Rp {item['Total_Row']:,.0f}</div>",
                            unsafe_allow_html=True
                        )

                st.markdown("<hr>", unsafe_allow_html=True)

                if st.button(f"🚀 SIMPAN KE ANTREAN ({MARKETING_NAME.upper()})", use_container_width=True, type="primary"):
                    if not nama_toko.strip():
                        st.error("⚠️ Nama Perusahaan / Toko wajib diisi di sebelah kiri!")
                    else:
                        sheet = get_user_worksheet(st.session_state.auth_user)
                        if sheet:
                            wkt = get_wib_now().strftime("%Y-%m-%d %H:%M")
                            sheet.append_row([
                                wkt,
                                nama_toko.strip(),
                                up_nama.strip(),
                                wa_nomor.strip(),
                                str(st.session_state.cart),
                                "Pending",
                                MARKETING_NAME
                            ])
                            st.session_state.pop("gs_all_vals", None)
                            st.balloons()
                            st.success(f"✅ Penawaran untuk **{nama_toko}** berhasil masuk ke antrean Dashboard!")
                            st.session_state.cart = []
                            time.sleep(0.9)
                            st.rerun()

                if st.button("🗑️ Kosongkan Keranjang", use_container_width=True):
                    st.session_state.cart = []
                    st.rerun()


# =========================================================
# 3. SALES DASHBOARD
# =========================================================
elif menu == "👨‍💻 Sales Dashboard":
    render_header("Sales Dashboard", "Kelola antrean, edit harga & cetak Quotation", f"🧑‍💼 {MARKETING_NAME or 'Login Diperlukan'}")

    if not require_login():
        st.stop()

    # Toolbar Pencarian & Refresh
    tb1, tb2, tb3 = st.columns([3, 1, 1])
    search_cust_q = tb1.text_input("🔎 Filter Nama Pelanggan / UP", placeholder="Ketik nama PT atau nama penerima...", label_visibility="collapsed")
    with tb2:
        if st.button("🔄 Refresh Data", use_container_width=True, key="btn_refresh", type="primary"):
            st.session_state.saved_items_cache = {}
            st.session_state.pop("gs_all_vals", None)
            st.cache_data.clear()
            st.toast("Data berhasil diperbarui dari Google Sheets")
            st.rerun()
    with tb3:
        if st.button("➕ Buat Baru", use_container_width=True, key="btn_go_new"):
            st.session_state.active_menu = "📝 Admin Sales"
            st.rerun()

    # Khusus Koordinator (Asin): Update CSV Database
    if st.session_state.auth_user == "asin":
        with st.expander("📁 Update Database Barang Master (.csv)", expanded=False):
            st.caption("Upload file CSV baru (`Nama Barang`, `Harga`, `Satuan`) untuk memperbarui katalog produk.")
            up_f2 = st.file_uploader("Pilih file CSV baru:", type=["csv"], key="csv_up_login")
            if up_f2:
                if st.button("🚀 Update Database Sekarang", key="btn_csv_login", type="primary"):
                    with open("database_barang.csv", "wb") as f:
                        f.write(up_f2.getbuffer())
                    st.cache_data.clear()
                    st.success("✅ Database berhasil diperbarui!")
                    time.sleep(1)
                    st.rerun()

    sheet = get_user_worksheet(st.session_state.auth_user)
    if sheet:
        try:
            if "gs_all_vals" not in st.session_state:
                with st.spinner("Mengambil data antrean dari Google Sheets..."):
                    st.session_state.gs_all_vals = sheet.get_all_values()
            all_vals = st.session_state.gs_all_vals

            if len(all_vals) > 1:
                raw_headers   = all_vals[0]
                clean_headers = [h.strip().lstrip('\ufeff') for h in raw_headers]
                required_cols = ["Waktu", "Customer", "UP", "WA", "Pesanan", "Status", "Sales"]
                df_gs = pd.DataFrame(all_vals[1:], columns=clean_headers)
                for col in required_cols:
                    if col not in df_gs.columns:
                        df_gs[col] = ""
                    df_gs[col] = df_gs[col].astype(str).str.strip()

                # Filter pencarian jika diisi
                if search_cust_q.strip():
                    q_low = search_cust_q.strip().lower()
                    mask_q = (
                        df_gs['Customer'].str.lower().str.contains(q_low, na=False) |
                        df_gs['UP'].str.lower().str.contains(q_low, na=False)
                    )
                    df_gs_filtered = df_gs[mask_q]
                else:
                    df_gs_filtered = df_gs

                pending   = df_gs_filtered[df_gs_filtered['Status'].str.lower() == 'pending']
                processed = df_gs_filtered[df_gs_filtered['Status'].str.lower() != 'pending']

                total_all     = len(df_gs)
                total_pending = len(df_gs[df_gs['Status'].str.lower() == 'pending'])
                total_done    = total_all - total_pending

                dm1, dm2, dm3 = st.columns(3)
                dm1.metric("📋 Total Semua Data", total_all)
                dm2.metric("⏳ Antrean Pending", total_pending)
                dm3.metric("✅ Sudah Selesai", total_done)

                st.markdown("<br>", unsafe_allow_html=True)

                tab_pending, tab_done = st.tabs([
                    f"⏳ Antrean Pending ({len(pending)})",
                    f"✅ Riwayat Selesai ({len(processed)})"
                ])

                # ── TAB 1: ANTREAN PENDING ──
                with tab_pending:
                    if not pending.empty:
                        for idx, row in pending.iterrows():
                            real_row_idx = idx + 2
                            try:
                                items_preview = ast.literal_eval(str(row['Pesanan']))
                                n_items = len(items_preview)
                            except Exception:
                                items_preview = []
                                n_items = 0

                            waktu_val    = row.get('Waktu', '')
                            customer_val = row.get('Customer', '')
                            up_val       = row.get('UP', '')
                            wa_val       = row.get('WA', '')

                            with st.expander(f"🏢 {customer_val}  ·  📦 {n_items} Item  ·  🕒 {waktu_val}", expanded=True):
                                st.info(f"🏢 Customer: **{customer_val}** &nbsp;|&nbsp; 👤 UP: **{up_val or '-'}** &nbsp;|&nbsp; 📞 WA: **{wa_val or '-'}**")

                                try:
                                    items_list = ast.literal_eval(str(row['Pesanan']))
                                except Exception:
                                    items_list = []

                                if real_row_idx in st.session_state.saved_items_cache:
                                    items_list = st.session_state.saved_items_cache[real_row_idx]

                                render_section_title("📝 Edit Daftar Barang")
                                st.caption("💡 Ubah **Pos** untuk mengatur urutan baris di PDF. Centang **🗑️ Hapus** lalu klik **Simpan Perubahan** untuk menghapus item.")

                                for i, r in enumerate(items_list):
                                    nama_item = r['Nama Barang']
                                    u_k = item_key(real_row_idx, nama_item)
                                    if f"h_{u_k}" not in st.session_state:
                                        st.session_state[f"h_{u_k}"] = int(float(r.get('Harga', 0)))
                                    if f"s_{u_k}" not in st.session_state:
                                        st.session_state[f"s_{u_k}"] = str(r.get('Satuan', 'Pcs')).strip()
                                    if f"q_{u_k}" not in st.session_state:
                                        st.session_state[f"q_{u_k}"] = int(r.get('Qty', 1))
                                    if f"p_{u_k}" not in st.session_state:
                                        st.session_state[f"p_{u_k}"] = float(i + 1)
                                    if f"m_{u_k}" not in st.session_state:
                                        st.session_state[f"m_{u_k}"] = "Pcs/Tetap"
                                    if f"isi_{u_k}" not in st.session_state:
                                        st.session_state[f"isi_{u_k}"] = 10

                                temp_up   = []
                                list_mode = ["Pcs/Tetap", "Lusin (12)", "Dus", "Box", "Pack", "Set", "Rim"]

                                for i, r in enumerate(items_list):
                                    nama_item     = r['Nama Barang']
                                    u_k           = item_key(real_row_idx, nama_item)
                                    row_master    = df_barang[df_barang['Nama Barang'] == nama_item]
                                    harga_master  = float(row_master['Harga'].values[0]) if not row_master.empty else float(r.get('Harga', 0))
                                    satuan_master = str(row_master['Satuan'].values[0]).strip() if not row_master.empty else str(r.get('Satuan', 'Pcs'))

                                    with st.container(border=True):
                                        harga_tersimpan  = st.session_state.get(f"h_{u_k}", int(float(r.get('Harga', 0))))
                                        satuan_tersimpan = st.session_state.get(f"s_{u_k}", str(r.get('Satuan', '')))
                                        qty_tersimpan    = st.session_state.get(f"q_{u_k}", int(r.get('Qty', 1)))
                                        sub_item_live    = harga_tersimpan * qty_tersimpan

                                        st.markdown(
                                            f"<div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:6px; margin-bottom:6px;'>"
                                            f"<div style='color:#002855;font-weight:800;font-size:0.95rem;'>{i+1}. {nama_item}</div>"
                                            f"<div>"
                                            f"<span class='pill-badge pill-master'>Master: Rp {harga_master:,.0f}/{satuan_master}</span>"
                                            f"<span class='pill-badge pill-saved'>Aktif: Rp {harga_tersimpan:,.0f}/{satuan_tersimpan}</span>"
                                            f"<span class='pill-badge pill-sub'>Subtotal: Rp {sub_item_live:,.0f}</span>"
                                            f"</div></div>",
                                            unsafe_allow_html=True
                                        )

                                        ic1, ic2, ic3, ic4, ic5, ic6 = st.columns([1.4, 1, 1.1, 1.5, 0.9, 0.8])
                                        mode = ic1.selectbox("Kalkulasi", list_mode, key=f"m_{u_k}")
                                        nq   = ic2.number_input("Qty", min_value=1, step=1, key=f"q_{u_k}")
                                        ns   = ic3.text_input("Satuan", key=f"s_{u_k}")
                                        nh   = ic4.number_input("Harga Jual", min_value=0, step=500, key=f"h_{u_k}", format="%d")
                                        np_  = ic5.number_input("Pos", min_value=0.1, step=0.1, format="%.1f", key=f"p_{u_k}")
                                        with ic6:
                                            st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
                                            td = st.checkbox("🗑️ Hapus", key=f"d_{u_k}")

                                        if mode in ["Dus", "Box", "Pack", "Set"]:
                                            st.number_input(f"Isi per {mode}", min_value=1, step=1, key=f"isi_{u_k}")

                                        if mode != "Pcs/Tetap":
                                            if mode == "Lusin (12)":
                                                harga_kalkulasi = int(harga_master * 12)
                                                sat_kalkulasi = "Lusin"
                                            elif mode == "Rim":
                                                harga_kalkulasi = int(harga_master)
                                                sat_kalkulasi = "Rim"
                                            else:
                                                isi_val = st.session_state.get(f"isi_{u_k}", 10)
                                                harga_kalkulasi = int(harga_master * isi_val)
                                                sat_kalkulasi = mode
                                            if st.button(f"▶ Terapkan Harga {sat_kalkulasi} (Rp {harga_kalkulasi:,.0f})", key=f"apply_{u_k}"):
                                                st.session_state[f"h_{u_k}"] = harga_kalkulasi
                                                st.session_state[f"s_{u_k}"] = sat_kalkulasi
                                                st.rerun()

                                        temp_up.append({"del": td, "pos": np_, "Nama": nama_item, "Qty": nq, "Harga": nh, "Sat": ns})

                                add_b = st.multiselect(
                                    "➕ Tambah Barang dari Database ke Penawaran Ini:",
                                    options=df_barang['Nama Barang'].tolist(),
                                    key=f"add_new_{real_row_idx}",
                                    placeholder="Ketik untuk mencari dan menambahkan barang..."
                                )

                                if st.button("💾 SIMPAN PERUBAHAN DATA KE GOOGLE SHEETS", key=f"btn_save_{real_row_idx}", use_container_width=True, type="primary"):
                                    final = sorted([x for x in temp_up if not x['del']], key=lambda x: x['pos'])
                                    for p in add_b:
                                        rb = df_barang[df_barang['Nama Barang'] == p].iloc[0]
                                        final.append({"Nama": p, "Qty": 1, "Harga": float(rb['Harga']), "Sat": str(rb['Satuan'])})
                                    save_data = [
                                        {
                                            "Nama Barang": x['Nama'],
                                            "Qty": x['Qty'],
                                            "Harga": x['Harga'],
                                            "Satuan": x['Sat'],
                                            "Total_Row": x['Qty'] * x['Harga']
                                        }
                                        for x in final
                                    ]

                                    with st.spinner("Menyimpan & memverifikasi ke Google Sheets..."):
                                        ok, msg = save_to_gsheet_verified(sheet, real_row_idx, save_data)

                                    if ok:
                                        st.session_state.saved_items_cache[real_row_idx] = save_data
                                        st.session_state.pop("gs_all_vals", None)
                                        clear_row_state(real_row_idx)
                                        st.success(f"✅ Tersimpan & terverifikasi! ({len(save_data)} jenis barang)")
                                        time.sleep(0.8)
                                        st.rerun()
                                    else:
                                        st.error(f"⚠️ Simpan gagal: {msg}. Silakan coba lagi.")

                                if real_row_idx in st.session_state.saved_items_cache:
                                    current_items = st.session_state.saved_items_cache[real_row_idx]
                                else:
                                    current_items = read_row_fresh(sheet, real_row_idx)
                                    if not current_items:
                                        current_items = items_list
                                    st.session_state.saved_items_cache[real_row_idx] = current_items

                                if current_items:
                                    f_df = pd.DataFrame(current_items)
                                    subt = f_df['Total_Row'].sum()

                                    st.markdown("---")
                                    render_section_title("🖨️ Cetak & Kirim Quotation")

                                    opt_c1, opt_c2 = st.columns([2, 1])
                                    no_s = opt_c1.text_input(
                                        "📄 Nomor Surat Quotation:",
                                        value=default_nomor_surat(real_row_idx - 1),
                                        key=f"ns_print_{real_row_idx}"
                                    )
                                    with opt_c2:
                                        st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
                                        use_ppn = st.checkbox("Sertakan PPN 11%", value=True, key=f"ppn_chk_{real_row_idx}")

                                    tax  = subt * 0.11 if use_ppn else 0.0
                                    gtot = subt + tax

                                    t1, t2, t3 = st.columns(3)
                                    t1.metric("Sub Total",   f"Rp {subt:,.0f}")
                                    t2.metric("PPN 11%",     f"Rp {tax:,.0f}" if use_ppn else "Rp 0 (Non-PPN)")
                                    t3.metric("Grand Total", f"Rp {gtot:,.0f}")

                                    waktu_file = get_wib_now().strftime("%d%m%y_%H%M")
                                    safe_cust  = "".join(
                                        c for c in str(customer_val) if c.isalnum() or c in (" ", "-", "_")
                                    ).strip().replace(" ", "_")

                                    b1, b2, b3 = st.columns(3)
                                    pdf_data = generate_pdf(no_s, customer_val, up_val, f_df, subt, tax, gtot)
                                    b1.download_button(
                                        label="📩 Download PDF",
                                        data=pdf_data,
                                        file_name=f"Quo_{safe_cust}_{waktu_file}.pdf",
                                        mime="application/pdf",
                                        key=f"btn_p_{real_row_idx}",
                                        use_container_width=True,
                                        type="primary"
                                    )
                                    xls_data = generate_excel(no_s, customer_val, up_val, f_df, subt, tax, gtot)
                                    b2.download_button(
                                        label="📊 Download Excel",
                                        data=xls_data,
                                        file_name=f"Quo_{safe_cust}_{waktu_file}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"btn_x_{real_row_idx}",
                                        use_container_width=True
                                    )
                                    wa_url = format_wa_link(wa_val, customer_val, up_val, gtot)
                                    with b3:
                                        if wa_url:
                                            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">💬 Chat WA Customer</a>', unsafe_allow_html=True)
                                        else:
                                            st.button("💬 Nomor WA Kosong", disabled=True, use_container_width=True, key=f"nowa_{real_row_idx}")

                                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                                    if st.button("✅ TANDAI SELESAI & PINDAHKAN KE RIWAYAT",
                                                 key=f"done_btn_{real_row_idx}",
                                                 use_container_width=True):
                                        sheet.update_cell(real_row_idx, 6, "Processed")
                                        if real_row_idx in st.session_state.saved_items_cache:
                                            del st.session_state.saved_items_cache[real_row_idx]
                                        st.session_state.pop("gs_all_vals", None)
                                        st.success(f"✅ Penawaran {customer_val} ditandai selesai.")
                                        st.rerun()
                    else:
                        st.markdown(f"""
                        <div style="text-align:center; padding:48px 20px; color:#64748b;">
                            <div style="font-size:3rem; margin-bottom:10px;">🎉</div>
                            <div style="font-size:1.1rem; font-weight:800; color:#002855;">Antrean Pending Bersih!</div>
                            <div style="font-size:0.85rem; margin-top:6px;">Semua penawaran sudah diproses, {MARKETING_NAME}.</div>
                        </div>
                        """, unsafe_allow_html=True)

                # ── TAB 2: RIWAYAT SELESAI (PROCESSED) ──
                with tab_done:
                    if not processed.empty:
                        for idx, row in processed.iloc[::-1].iterrows():
                            real_row_idx = idx + 2
                            waktu_val    = row.get('Waktu', '')
                            customer_val = row.get('Customer', '')
                            up_val       = row.get('UP', '')
                            wa_val       = row.get('WA', '')
                            try:
                                done_items = ast.literal_eval(str(row['Pesanan']))
                            except Exception:
                                done_items = []

                            with st.expander(f"✅ {customer_val}  ·  {len(done_items)} Item  ·  {waktu_val}", expanded=False):
                                st.caption(f"👤 UP: **{up_val or '-'}** &nbsp;|&nbsp; 📞 WA: **{wa_val or '-'}**")
                                if done_items:
                                    df_done = pd.DataFrame(done_items)
                                    st.dataframe(df_done, use_container_width=True, hide_index=True)
                                    sub_d = df_done['Total_Row'].sum()
                                    tax_d = sub_d * 0.11
                                    gt_d  = sub_d + tax_d

                                    rc1, rc2, rc3 = st.columns(3)
                                    waktu_f = get_wib_now().strftime("%d%m%y_%H%M")
                                    safe_c  = "".join(c for c in str(customer_val) if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
                                    no_s_d  = default_nomor_surat(real_row_idx - 1)

                                    rc1.download_button(
                                        "📩 Unduh Ulang PDF",
                                        data=generate_pdf(no_s_d, customer_val, up_val, df_done, sub_d, tax_d, gt_d),
                                        file_name=f"Quo_{safe_c}_{waktu_f}.pdf",
                                        mime="application/pdf",
                                        key=f"re_pdf_{real_row_idx}",
                                        use_container_width=True
                                    )
                                    rc2.download_button(
                                        "📊 Unduh Ulang Excel",
                                        data=generate_excel(no_s_d, customer_val, up_val, df_done, sub_d, tax_d, gt_d),
                                        file_name=f"Quo_{safe_c}_{waktu_f}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"re_xls_{real_row_idx}",
                                        use_container_width=True
                                    )
                                    if rc3.button("↩️ Kembalikan ke Pending", key=f"restore_{real_row_idx}", use_container_width=True):
                                        sheet.update_cell(real_row_idx, 6, "Pending")
                                        st.session_state.pop("gs_all_vals", None)
                                        st.toast(f"Dikembalikan ke antrean Pending: {customer_val}")
                                        st.rerun()
                    else:
                        st.info("Belum ada riwayat penawaran yang ditandai selesai.")
            else:
                st.info("Belum ada data penawaran di Google Sheets Anda. Silakan buat penawaran baru melalui menu **Admin Sales**.")

        except Exception as e:
            st.error(f"❌ Error Sistem: {e}")
            import traceback
            st.code(traceback.format_exc(), language="python")
