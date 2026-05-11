import streamlit as st
import re
from datetime import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Formularz Redakcyjny KL", layout="wide")

# --- FUNKCJE POMOCNICZE ---
def usun_polskie_znaki(tekst):
    polskie_znaki = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
    return tekst.translate(polskie_znaki)

def wyczysc_brudy_kopiowania(tekst):
    tekst = tekst.replace('\xa0', ' ').replace('<span class="Apple-converted-space"> </span>', ' ')
    return tekst.strip()

def formatuj_tekst_glowny(tekst):
    tekst = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', tekst)
    tekst = re.sub(r'\*(.*?)\*', r'<b>\1</b>', tekst)
    tekst = re.sub(r'\[(\d+)\]', r'<sup style="font-size: 0.8em; vertical-align: super;">[\1]</sup>', tekst)
    return tekst

def formatuj_proste(tekst):
    tekst = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', tekst)
    tekst = re.sub(r'\*(.*?)\*', r'<b>\1</b>', tekst)
    return tekst

def uczyn_linki_klikalnymi(tekst):
    wzor_url = r'(https?://[^\s\]<]+)'
    return re.sub(wzor_url, r'<a href="\1" target="_blank">\1</a>', tekst)

def generuj_obrazek(tag_content, author_code, base_url, ext):
    clean_tag = tag_content.lower().strip().replace('.', '')
    if "cover" in clean_tag: return None
    w = 500 if ("pion" in clean_tag or "kwadrat" in clean_tag) else 675
    file_tag = usun_polskie_znaki(clean_tag).replace(" ", "_").replace("-", "_")
    f_name = f"{author_code}_{file_tag}{ext}"
    full_url = f"{base_url.rstrip('/')}/{f_name}"
    return f'<img src="{full_url}" alt="" width="{w}" height="auto" style="display: block; margin: 20px auto;" />'

def reset_calkowity():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# --- PANEL BOCZNY ---
with st.sidebar:
    st.header("⚙️ Ustawienia")
    author_code = st.text_input("Kod autora:", placeholder="rybak", key="auth_c").lower().strip()
    year = st.text_input("Rok:", value=str(datetime.now().year), key="y_c")
    month = st.text_input("Miesiąc:", value=datetime.now().strftime("%m"), key="m_c")
    file_ext = st.selectbox("Format zdjęć:", [".jpg", ".png", ".jpeg"], key="ext_c")
    
    st.divider()
    st.subheader("🖼️ Dodatkowy banner")
    wybor_banneru = st.radio("Wybierz opcję:", ["Brak", "MKiDN", "Inny"], index=0)
    
    st.divider()
    if st.button("🗑️ WYCZYŚĆ CAŁY FORMULARZ", use_container_width=True):
        reset_calkowity()
    
    base_url = f"https://kulturaliberalna.pl/wp-content/uploads/{year}/{month}/"

# --- UKŁAD FORMULARZA ---
st.title("📑 Formularz Redakcyjny KL")
col1, col2 = st.columns(2)

with col1:
    st.subheader("🖋️ Artykuł")
    f_tytul_seo = st.text_input("Tytuł:", key="f_tit")
    f_lead = st.text_area("Lead (Wstęp):", height=120, key="f_led")
    f_body = st.text_area("Tekst główny:", height=450, key="f_bod")
    
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #dcdfe3;">
        <span style="font-size: 1.2em;">💡</span> <b>Instrukcja:</b><br><br>
        <ul style="list-style-type: none; padding-left: 0;">
            <li style="margin-bottom: 8px;"><code>*tekst*</code> – <b>pogrubienie</b>.</li>
            <li style="margin-bottom: 8px;"><code>[1]</code> – przypis (zamiana na indeks górny).</li>
            <li style="margin-bottom: 8px;"><code>### Nagłówek</code> – nagłówek sekcji H3.</li>
            <li style="margin-bottom: 8px;"><code>[IMG1]</code> – miejsce na zdjęcie.</li>
            <li style="margin-bottom: 8px;"><code>&gt;</code> lub <code>wyimek:</code> – wyimek.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("👤 Metadane")
    f_author_name = st.text_input("Imię i nazwisko autora:", key="f_authn")
    f_bio = st.text_area("BIO (bez nazwiska):", height=100, key="f_bio")
    f_slug = st.text_input("Slug (URL):", key="f_slu")
    f_meta = st.text_area("Metaopis (SEO):", height=80, key="f_met")
    st.divider()
    f_przypisy = st.text_area("Przypisy:", height=100, key="f_prz")
    f_ksiazka = st.text_area("Sekcja 'Książka':", height=80, key="f_ksi")
    
    st.markdown("---")
    st.markdown("**🏷️ Pole własne (opcjonalne)**")
    c_label, c_content = st.columns([1, 2])
    with c_label:
        f_custom_label = st.text_input("Nazwa sekcji:", placeholder="np. Opera", key="f_cus_l")
    with c_content:
        f_custom_text = st.text_area("Treść sekcji:", height=68, key="f_cus_t")

# --- GENEROWANIE ---
if st.button("🚀 GENERUJ / ODŚWIEŻ KOD HTML", use_container_width=True):
    if not author_code or not f_body:
        st.error("Uzupełnij kod autora i treść!")
    else:
        clean_lead = wyczysc_brudy_kopiowania(f_lead)
        html_body = []
        lines = f_body.splitlines()
        in_list = False
        
        for line in lines:
            line_s = wyczysc_brudy_kopiowania(line)
            if not line_s:
                if in_list: html_body.append('</ol>'); in_list = False
                continue
            
            if line_s.startswith("###"):
                txt = line_s.replace("###", "").strip()
                html_body.append(f'<h3><b>{formatuj_tekst_glowny(txt)}</b></h3>')
                continue

            if re.match(r'^\d+\.\s', line_s):
                if not in_list: html_body.append('<ol>'); in_list = True
                txt = re.sub(r'^\d+\.\s', '', line_s).strip()
                html_body.append(f'<li><span style="font-weight: 400;">{uczyn_linki_klikalnymi(formatuj_tekst_glowny(txt))}</span></li>')
                continue
            else:
                if in_list: html_body.append('</ol>'); in_list = False

            tag_match = re.search(r'\[(.*?)\]', line_s)
            if tag_match and not re.sub(r'\[.*?\]', '', line_s).strip() and not tag_match.group(1).isdigit():
                img_html = generuj_obrazek(tag_match.group(1), author_code, base_url, file_ext)
                if img_html: html_body.append(img_html)
                continue

            if line_s.lower().startswith("wyimek:") or line_s.startswith(">"):
                txt = line_s.lstrip("> ").replace("wyimek:", "", 1).replace("WYIMEK:", "", 1).strip().strip('"„”')
                html_body.append(f'<blockquote><span style="font-weight: 400;">„{uczyn_linki_klikalnymi(formatuj_tekst_glowny(txt))}”</span></blockquote>')
                continue
            
            html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(formatuj_tekst_glowny(line_s))}</span>')

        if in_list: html_body.append('</ol>')

        # --- SEKCJE DOLNE (Przypisy, Książka, Pole własne) ---
        footer_sections = [
            ("Przypisy", f_przypisy),
            ("Książka", f_ksiazka),
            (f_custom_label, f_custom_text)
        ]

        for label, content in footer_sections:
            if label and content.strip():
                html_body.append(f'<p style="margin-top: 25px; margin-bottom: 5px;"><b>{label}:</b></p>')
                block = [f'<small style="font-size: 13px; line-height: 1.4; color: #444;">{uczyn_linki_klikalnymi(formatuj_proste(p.strip()))}</small>' for p in content.splitlines() if p.strip()]
                html_body.append("<br />".join(block))

        if wybor_banneru == "MKiDN":
            URL_BANER = "https://kulturaliberalna.pl/wp-content/uploads/2025/06/Baner-strona-WWW-top-1080-x-50-1080-x-100-px.png"
            html_body.append(f'<br /><hr style="border: 0; height: 1px; background: #eee; margin: 25px 0;" />')
            html_body.append(f'<div style="text-align: center;"><img src="{URL_BANER}" alt="" width="1080" height="100" /></div>')

        # WYNIK
        st.divider()
        st.success("✅ Kod HTML wygenerowany!")
        st.text_area("TREŚĆ HTML:", "\n".join(html_body), height=500)
        
        c3, c4 = st.columns(2)
        with c3:
            st.text_input("Slug:", f_slug)
            st.text_area("Metaopis:", f_meta, height=80)
        with c4:
            st.text_area("BIO AUTORA:", formatuj_tekst_glowny(f_bio), height=150)