import streamlit as st
import re
from datetime import datetime

# --- FUNKCJE POMOCNICZE ---
def usun_polskie_znaki(tekst):
    polskie_znaki = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
    return tekst.translate(polskie_znaki)

def wyczysc_brudy_kopiowania(tekst):
    tekst = tekst.replace('\xa0', ' ').replace('<span class="Apple-converted-space"> </span>', ' ')
    return tekst.strip()

def uczyn_linki_klikalnymi(tekst):
    wzor_url = r'(https?://[^\s\]]+)'
    return re.sub(wzor_url, r'<a href="\1" target="_blank">\1</a>', tekst)

def generuj_obrazek(tag_content, author_code, base_url, ext):
    # Czyszczenie zawartości tagu z kropek i spacji
    clean_tag = tag_content.lower().strip().replace('.', '')
    
    # Ustalanie szerokości
    if "cover" in clean_tag:
        w = 550
    elif "pion" in clean_tag or "kwadrat" in clean_tag:
        w = 500
    else:
        w = 675
    
    # Budowa bezpiecznej nazwy pliku
    file_tag = usun_polskie_znaki(clean_tag).replace(" ", "_").replace("-", "_")
    f_name = f"{author_code}_{file_tag}{ext}"
    full_url = f"{base_url.rstrip('/')}/{f_name}"
    
    return f'<img class="alignnone wp-image-XXXX" src="{full_url}" alt="" width="{w}" height="auto" style="max-width: 100%; height: auto;" />'

# --- KONFIGURACJA ---
URL_BANER = "https://kulturaliberalna.pl/wp-content/uploads/2025/06/Baner-strona-WWW-top-1080-x-50-1080-x-100-px.png"
st.set_page_config(page_title="Formularz Redakcyjny KL", layout="wide")

st.title("📑 Formularz Redakcyjny KL")

with st.sidebar:
    st.header("⚙️ Ustawienia techniczne")
    author_code = st.text_input("Kod autora:", placeholder="rybak").lower().strip().replace(" ", "")
    year = st.text_input("Rok:", value=str(datetime.now().year))
    month = st.text_input("Miesiąc:", value=datetime.now().strftime("%m"))
    file_ext = st.selectbox("Format zdjęć:", [".jpg", ".png", ".jpeg"])
    base_url = f"https://kulturaliberalna.pl/wp-content/uploads/{year}/{month}/"

col1, col2 = st.columns(2)

with col1:
    st.subheader("🖋️ Artykuł")
    f_tytul_seo = st.text_input("Tytuł:")
    f_lead = st.text_area("Lead (Wstęp):", height=120)
    f_body = st.text_area("Tekst główny:", height=400)

with col2:
    st.subheader("👤 Metadane")
    f_author_name = st.text_input("Imię i nazwisko autora:")
    f_bio = st.text_area("BIO (bez nazwiska):", height=100)
    f_slug = st.text_input("Slug (URL):")
    f_meta = st.text_area("Metaopis (SEO):", height=80)
    st.divider()
    f_ksiazka = st.text_area("Sekcja 'Książka':", height=80)
    f_przypisy = st.text_area("Przypisy:", height=100)

if st.button("🚀 GENERUJ PACZKĘ DLA WORDPRESS"):
    if not author_code or not f_body:
        st.error("Wymagany kod autora i treść!")
    else:
        clean_lead = wyczysc_brudy_kopiowania(f_lead)
        html_body = []
        lines = f_body.splitlines()
        in_list = False
        
        for line in lines:
            line_stripped = wyczysc_brudy_kopiowania(line)
            if not line_stripped:
                if in_list:
                    html_body.append('</ol>')
                    in_list = False
                continue
            
            # 1. WYKRYWANIE LISTY
            if re.match(r'^\d+\.\s', line_stripped):
                if not in_list:
                    html_body.append('<ol>')
                    in_list = True
                txt = re.sub(r'^\d+\.\s', '', line_stripped).strip()
                html_body.append(f'<li><span style="font-weight: 400;">{uczyn_linki_klikalnymi(txt)}</span></li>')
                continue
            else:
                if in_list:
                    html_body.append('</ol>')
                    in_list = False

            # 2. WYKRYWANIE OBRAZKA (Nawet z myślnikami: ---[IMG1]---)
            # Szukamy wzoru [coś] w linii, która nie ma innych liter poza tymi w nawiasie
            tag_match = re.search(r'\[(.*?)\]', line_stripped)
            # Sprawdzamy czy linia to TYLKO tag i ewentualne ozdobniki (nie ma innych słów)
            only_placeholders = re.sub(r'\[.*?\]', '', line_stripped).replace('-', '').replace(' ', '').strip()
            
            if tag_match and not only_placeholders:
                tag_content = tag_match.group(1)
                html_body.append(generuj_obrazek(tag_content, author_code, base_url, file_ext))
                continue

            # 3. WYIMKI
            line_l = line_stripped.lower()
            if line_l.startswith("wyimek:") or line_stripped.startswith(">"):
                txt = line_stripped.lstrip("> ").replace("wyimek:", "", 1).replace("WYIMEK:", "", 1).strip().strip('"').strip('„').strip('”')
                html_body.append(f'<blockquote><span style="font-weight: 400;">„{uczyn_linki_klikalnymi(txt)}”</span></blockquote>')
                continue
            
            # 4. ZWYKŁY TEKST
            html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(line_stripped)}</span>')

        if in_list: html_body.append('</ol>')

        # Stopka
        if f_ksiazka:
            html_body.append(f'<br />\n<b>Książka:</b>\n<span style="font-weight: 400;">{uczyn_linki_klikalnymi(f_ksiazka)}</span>')
        if f_przypisy:
            html_body.append(f'<br />\n<b>Przypisy:</b>')
            for p in f_przypisy.splitlines():
                if p.strip():
                    html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(p.strip())}</span>')

        html_body.append(f'\n<img src="{URL_BANER}" alt="" width="1080" height="100" />')

        st.divider()
        st.success("✅ Paczka gotowa!")
        c1, c2 = st.columns(2)
        with c1: st.text_input("1. TYTUŁ:", f_tytul_seo)
        with c2: st.text_area("2. LEAD:", clean_lead, height=100)
        st.text_area("3. TREŚĆ GŁÓWNA HTML:", "\n\n".join(html_body), height=400)
        c3, c4 = st.columns(2)
        with c3:
            st.text_input("4. SLUG:", f_slug)
            st.text_area("5. METAOPIS:", f_meta, height=80)
        with c4: st.text_area("6. BIO AUTORA:", f_bio, height=150)