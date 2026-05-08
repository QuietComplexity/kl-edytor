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

def formatuj_tekst_markdown(tekst):
    # 1. Bold: **tekst** lub *tekst* -> <b>
    tekst = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', tekst)
    tekst = re.sub(r'\*(.*?)\*', r'<b>\1</b>', tekst)
    # 2. Indeksy górne dla przypisów: [1] -> <sup>[1]</sup>
    tekst = re.sub(r'\[(\d+)\]', r'<sup>[\1]</sup>', tekst)
    return tekst

def uczyn_linki_klikalnymi(tekst):
    wzor_url = r'(https?://[^\s\]<]+)'
    return re.sub(wzor_url, r'<a href="\1" target="_blank">\1</a>', tekst)

def generuj_obrazek(tag_content, author_code, base_url, ext):
    clean_tag = tag_content.lower().strip().replace('.', '')
    if "cover" in clean_tag:
        return None
    
    w = 500 if ("pion" in clean_tag or "kwadrat" in clean_tag) else 675
    
    file_tag = usun_polskie_znaki(clean_tag).replace(" ", "_").replace("-", "_")
    f_name = f"{author_code}_{file_tag}{ext}"
    full_url = f"{base_url.rstrip('/')}/{f_name}"
    
    return f'<img class="alignnone wp-image-XXXX" src="{full_url}" alt="" width="{w}" height="auto" style="max-width: 100%; height: auto;" />'

# --- KONFIGURACJA STRONY ---
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
    st.divider()
    if st.button("🔄 Odśwież / Wyczyść wszystko"):
        st.rerun()

col1, col2 = st.columns(2)

with col1:
    st.subheader("🖋️ Artykuł")
    f_tytul_seo = st.text_input("Tytuł:")
    f_lead = st.text_area("Lead (Wstęp):", height=120)
    f_body = st.text_area("Tekst główny:", height=400)
    
    st.markdown("""
    ### 💡 Instrukcja formatowania:
    * `*tekst*` – **pogrubienie**.
    * `[1]` – automatyczny **indeks górny** (przypis w tekście).
    * `### Nagłówek` – nagłówek **H3**.
    * `[IMG1]` – zdjęcie w osobnej linii.
    * `>` lub `wyimek:` – sformatowany **wyimek**.
    """)

with col2:
    st.subheader("👤 Metadane")
    f_author_name = st.text_input("Imię i nazwisko autora:")
    f_bio = st.text_area("BIO (bez nazwiska):", height=100)
    f_slug = st.text_input("Slug (URL):")
    f_meta = st.text_area("Metaopis (SEO):", height=80)
    st.divider()
    f_ksiazka = st.text_area("Sekcja 'Książka':", height=80)
    f_przypisy = st.text_area("Przypisy (każdy w nowej linii):", height=100)

if st.button("🚀 GENERUJ PACZKĘ DLA WORDPRESS"):
    if not author_code or not f_body:
        st.error("Wymagany kod autora i treść!")
    else:
        clean_lead = wyczysc_brudy_kopiowania(f_lead)
        html_body = []
        lines = f_body.splitlines()
        in_list = False
        
        for line in lines:
            line_s = wyczysc_brudy_kopiowania(line)
            if not line_s:
                if in_list:
                    html_body.append('</ol>')
                    in_list = False
                continue
            
            # 1. NAGŁÓWKI
            if line_s.startswith("###"):
                txt = line_s.replace("###", "").strip()
                html_body.append(f'<h3><b>{formatuj_tekst_markdown(txt)}</b></h3>')
                continue

            # 2. LISTY
            if re.match(r'^\d+\.\s', line_s):
                if not in_list:
                    html_body.append('<ol>')
                    in_list = True
                txt = re.sub(r'^\d+\.\s', '', line_s).strip()
                html_body.append(f'<li><span style="font-weight: 400;">{uczyn_linki_klikalnymi(formatuj_tekst_markdown(txt))}</span></li>')
                continue
            else:
                if in_list:
                    html_body.append('</ol>')
                    in_list = False

            # 3. OBRAZKI
            tag_match = re.search(r'\[(.*?)\]', line_s)
            only_placeholders = re.sub(r'\[.*?\]', '', line_s).replace('-', '').replace(' ', '').strip()
            # Sprawdzamy czy tag w nawiasie nie jest przypisem (cyfrą), żeby nie wstawić tam obrazka
            if tag_match and not only_placeholders and not tag_match.group(1).isdigit():
                tag_content = tag_match.group(1)
                img_html = generuj_obrazek(tag_content, author_code, base_url, file_ext)
                if img_html: html_body.append(img_html)
                continue

            # 4. WYIMKI
            line_l = line_s.lower()
            if line_l.startswith("wyimek:") or line_s.startswith(">"):
                txt = line_s.lstrip("> ").replace("wyimek:", "", 1).replace("WYIMEK:", "", 1).strip().strip('"').strip('„').strip('”')
                html_body.append(f'<blockquote><span style="font-weight: 400;">„{uczyn_linki_klikalnymi(formatuj_tekst_markdown(txt))}”</span></blockquote>')
                continue
            
            # 5. ZWYKŁY TEKST
            html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(formatuj_tekst_markdown(line_s))}</span>')

        if in_list: html_body.append('</ol>')

        # STOPKA (Z mniejszą czcionką)
        if f_ksiazka:
            html_body.append(f'<div style="font-size: 0.9em;"><br />\n<b>Książka:</b>\n<span style="font-weight: 400;">{uczyn_linki_klikalnymi(formatuj_tekst_markdown(f_ksiazka))}</span></div>')
        
        if f_przypisy:
            html_body.append(f'<div style="font-size: 0.85em;"><br />\n<b>Przypisy:</b>')
            for p in f_przypisy.splitlines():
                if p.strip():
                    html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(formatuj_tekst_markdown(p.strip()))}</span>')
            html_body.append('</div>')

        html_body.append(f'\n<img src="{URL_BANER}" alt="" width="1080" height="100" />')

        st.divider()
        st.success("✅ Paczka gotowa!")
        
        c1, c2 = st.columns(2)
        with c1: st.text_input("1. TYTUŁ (SEO):", f_tytul_seo)
        with c2: st.text_area("2. LEAD (Wstęp):", formatuj_tekst_markdown(clean_lead), height=100)
        
        st.text_area("3. TREŚĆ GŁÓWNA HTML:", "\n\n".join(html_body), height=400)
        
        c3, c4 = st.columns(2)
        with c3:
            st.text_input("4. SLUG (URL):", f_slug)
            st.text_area("5. METAOPIS:", f_meta, height=80)
        with c4: st.text_area("6. BIO AUTORA:", formatuj_tekst_markdown(f_bio), height=150)