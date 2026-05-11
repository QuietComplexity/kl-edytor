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
    if not tekst: return ""
    # Usuwanie twardych spacji i śmieci z edytorów tekstowych
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

def parsuj_tekst_redakcyjny(surowy_tekst):
    """Parsuje blok tekstu i wyciąga metadane."""
    mapowanie = {
        "AUTOR": r"(?:AUTOR|AUTORKA):\s*(.*?)(?=\n(?:TYTUŁ|LEAD|BIO|URL|SŁOWO|SEO|METAOPIS|TAGI)|$)",
        "TYTUŁ": r"TYTUŁ:\s*(.*?)(?=\n(?:AUTOR|AUTORKA|LEAD|BIO|URL|SŁOWO|SEO|METAOPIS|TAGI)|$)",
        "LEAD": r"LEAD:\s*(.*?)(?=\n(?:AUTOR|AUTORKA|TYTUŁ|BIO|URL|SŁOWO|SEO|METAOPIS|TAGI)|$)",
        "BIO": r"BIO:\s*(.*?)(?=\n(?:AUTOR|AUTORKA|TYTUŁ|LEAD|URL|SŁOWO|SEO|METAOPIS|TAGI)|$)",
        "URL": r"URL:\s*(.*?)(?=\n(?:AUTOR|AUTORKA|TYTUŁ|LEAD|BIO|SŁOWO|SEO|METAOPIS|TAGI)|$)",
        "METAOPIS": r"METAOPIS:\s*(.*?)(?=\n(?:AUTOR|AUTORKA|TYTUŁ|LEAD|BIO|URL|SŁOWO|SEO|TAGI)|$)",
    }
    wyniki = {}
    for klucz, wzorzec in mapowanie.items():
        match = re.search(wzorzec, surowy_tekst, re.DOTALL | re.IGNORECASE)
        if match:
            wyniki[klucz] = match.group(1).replace('\n', ' ').strip()
        else:
            wyniki[klucz] = ""
    return wyniki

def reset_calkowity():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# --- PANEL BOCZNY ---
with st.sidebar:
    st.header("⚙️ Ustawienia")
    author_code = st.text_input("Kod autora (pliki):", placeholder="np. mik", key="auth_c").lower().strip()
    year = st.text_input("Rok:", value=str(datetime.now().year), key="y_c")
    month = st.text_input("Miesiąc:", value=datetime.now().strftime("%m"), key="m_c")
    file_ext = st.selectbox("Format zdjęć:", [".jpg", ".png", ".jpeg"], key="ext_c")
    
    st.divider()
    st.subheader("🖼️ Dodatkowy banner")
    wybor_banneru = st.radio("Wybierz opcję:", ["Brak", "MKiDN", "Inny"], index=0)
    
    st.divider()
    if st.button("🗑️ WYCZYŚĆ WSZYSTKO", use_container_width=True):
        reset_calkowity()
    
    base_url = f"https://kulturaliberalna.pl/wp-content/uploads/{year}/{month}/"

# --- FORMULARZ ---
st.title("📑 Formularz Redakcyjny KL")

st.subheader("📥 1. Wklej tekst z redakcji")
surowy_input = st.text_area("Wklej tutaj blok tekstu z metadanymi:", height=180)

parsed_data = {}
if surowy_input:
    parsed_data = parsuj_tekst_redakcyjny(surowy_input)

st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("🖋️ 2. Treść artykułu")
    f_tytul_seo = st.text_input("Tytuł (SEO):", value=parsed_data.get("TYTUŁ", ""), key="f_tit")
    f_lead = st.text_area("Lead (do osobnego okna WP):", value=parsed_data.get("LEAD", ""), height=100, key="f_led")
    
    # Pole na TEKST GŁÓWNY (bez leada na początku)
    f_body_only = st.text_area("Wklej tutaj SAM TEKST artykułu:", height=400, key="f_bod_only")
    
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #dcdfe3;">
        <span style="font-size: 1.2em;">💡</span> <b>Instrukcja:</b><br>
        <code>*bold*</code>, <code>[1]</code>, <code>### Nagłówek</code>, <code>[IMG1]</code>, <code>> wyimek</code>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("👤 3. Metadane")
    f_author_name = st.text_input("Imię i nazwisko autora:", value=parsed_data.get("AUTOR", ""), key="f_authn")
    f_bio = st.text_area("BIO (do zakładki BIO):", value=parsed_data.get("BIO", ""), height=80, key="f_bio")
    f_slug = st.text_input("Slug / URL:", value=parsed_data.get("URL", ""), key="f_slu")
    f_meta = st.text_area("Metaopis SEO:", value=parsed_data.get("METAOPIS", ""), height=80, key="f_met")
    
    st.divider()
    f_przypisy = st.text_area("Przypisy:", height=80, key="f_prz")
    f_ksiazka = st.text_area("Sekcja 'Książka':", height=80, key="f_ksi")
    
    st.markdown("**🏷️ Pole własne (opcjonalne)**")
    c_label, c_content = st.columns([1, 2])
    with c_label: f_custom_label = st.text_input("Nazwa:", placeholder="np. Opera", key="f_cus_l")
    with c_content: f_custom_text = st.text_area("Treść:", height=68, key="f_cus_t")

# --- GENEROWANIE ---
if st.button("🚀 GENERUJ KOD HTML", use_container_width=True):
    if not f_body_only:
        st.error("Wklej tekst główny!")
    else:
        html_body = []
        lines = f_body_only.splitlines()
        in_list = False
        
        for line in lines:
            line_s = wyczysc_brudy_kopiowania(line)
            if not line_s:
                if in_list: html_body.append('</ol>'); in_list = False
                continue
            
            # Nagłówki H3
            if line_s.startswith("###"):
                txt = line_s.replace("###", "").strip()
                html_body.append(f'<h3><b>{formatuj_tekst_glowny(txt)}</b></h3>')
                continue

            # Listy numerowane
            if re.match(r'^\d+\.\s', line_s):
                if not in_list: html_body.append('<ol>'); in_list = True
                txt = re.sub(r'^\d+\.\s', '', line_s).strip()
                html_body.append(f'<li><span style="font-weight: 400;">{uczyn_linki_klikalnymi(formatuj_tekst_glowny(txt))}</span></li>')
                continue
            else:
                if in_list: html_body.append('</ol>'); in_list = False

            # Obrazki [IMG...]
            tag_match = re.search(r'\[(.*?)\]', line_s)
            if tag_match and not re.sub(r'\[.*?\]', '', line_s).strip() and not tag_match.group(1).isdigit():
                img_html = generuj_obrazek(tag_match.group(1), author_code, base_url, file_ext)
                if img_html: html_body.append(img_html)
                continue

            # Wyimki
            if line_s.lower().startswith("wyimek:") or line_s.startswith(">"):
                txt = line_s.lstrip("> ").replace("wyimek:", "", 1).replace("WYIMEK:", "", 1).strip().strip('"„”')
                html_body.append(f'<blockquote><span style="font-weight: 400;">„{uczyn_linki_klikalnymi(formatuj_tekst_glowny(txt))}”</span></blockquote>')
                continue
            
            # Paragrafy (pogrubienie Lead nie jest tu potrzebne, bo Lead wyleciał do osobnego pola)
            html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(formatuj_tekst_glowny(line_s))}</span>')

        if in_list: html_body.append('</ol>')

        # SEKCJE DOLNE
        for label, content in [("Przypisy", f_przypisy), ("Książka", f_ksiazka), (f_custom_label, f_custom_text)]:
            if label and content.strip():
                html_body.append(f'<p style="margin-top: 25px; margin-bottom: 5px;"><b>{label}:</b></p>')
                block = [f'<small style="font-size: 13px; line-height: 1.4; color: #444;">{uczyn_linki_klikalnymi(formatuj_proste(p.strip()))}</small>' for p in content.splitlines() if p.strip()]
                html_body.append("<br />".join(block))

        # BANNER
        if wybor_banneru == "MKiDN":
            URL_BANER = "https://kulturaliberalna.pl/wp-content/uploads/2025/06/Baner-strona-WWW-top-1080-x-50-1080-x-100-px.png"
            html_body.append(f'<br /><hr style="border: 0; height: 1px; background: #eee; margin: 25px 0;" />')
            html_body.append(f'<div style="text-align: center;"><img src="{URL_BANER}" alt="" width="1080" height="100" /></div>')

        # WYNIKI
        st.divider()
        st.success("✅ Kod wygenerowany!")
        
        c_res1, c_res2 = st.columns(2)
        with c_res1: 
            st.text_input("Tytuł SEO:", f_tytul_seo)
            st.text_input("Slug:", f_slug)
            st.text_area("Gotowy LEAD (skopiuj do WP):", f_lead, height=100)
        with c_res2:
            st.text_area("Metaopis SEO:", f_meta, height=100)
            st.text_area("BIO (do WP):", formatuj_tekst_glowny(f_bio), height=100)

        st.text_area("KOD HTML TEKSTU GŁÓWNEGO:", "\n".join(html_body), height=500)