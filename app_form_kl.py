import streamlit as st
import re
from datetime import datetime

# --- FUNKCJE POMOCNICZE ---
def usun_polskie_znaki(tekst):
    polskie_znaki = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
    return tekst.translate(polskie_znaki)

def wyczysc_brudy_kopiowania(tekst):
    # Czyści śmieciowe tagi z systemów Apple i zbędne spacje
    tekst = tekst.replace('<span class="Apple-converted-space"> </span>', ' ')
    return tekst.strip()

def uczyn_linki_klikalnymi(tekst):
    wzor_url = r'(https?://[^\s\]]+)'
    return re.sub(wzor_url, r'<a href="\1" target="_blank">\1</a>', tekst)

def generuj_obrazek(tag, author_code, base_url, ext):
    # Standaryzacja tagu do małych liter (załatwia problem wielkości liter)
    tag_raw = tag.strip()
    tag_lower = tag_raw.lower()
    
    # USTALANIE SZEROKOŚCI
    if "cover" in tag_lower:
        w = 550
    elif "pion" in tag_lower or "kwadrat" in tag_lower:
        w = 500
    else:
        w = 675  # Domyślnie dla poziomu
    
    # BUDOWANIE NAZWY PLIKU (Kod autora + tag bez polskich znaków)
    # Przykład: rybak_img1_pion.jpg
    file_tag = usun_polskie_znaki(tag_lower).replace(" ", "_")
    f_name = f"{author_code}_{file_tag}{ext}"
    
    return f'<img class="alignnone wp-image-XXXX" src="{base_url + f_name}" alt="" width="{w}" height="auto" style="max-width: 100%; height: auto;" />'

# --- KONFIGURACJA STRONY ---
URL_BANER = "https://kulturaliberalna.pl/wp-content/uploads/2025/06/Baner-strona-WWW-top-1080-x-50-1080-x-100-px.png"
st.set_page_config(page_title="Formularz Redakcyjny KL", layout="wide")

st.title("📑 Formularz Redakcyjny KL")

# --- PANEL BOCZNY (USTAWIENIA TECHNICZNE) ---
with st.sidebar:
    st.header("⚙️ Ustawienia techniczne")
    author_code = st.text_input("Kod autora (np. rybak):", placeholder="rybak").lower().strip()
    year = st.text_input("Rok (do ścieżki):", value=str(datetime.now().year))
    month = st.text_input("Miesiąc (do ścieżki):", value=datetime.now().strftime("%m"))
    file_ext = st.selectbox("Format zdjęć:", [".jpg", ".png", ".jpeg"])
    base_url = f"https://kulturaliberalna.pl/wp-content/uploads/{year}/{month}/"
    if st.button("🗑️ Wyczyść formularz"):
        st.rerun()

# --- WEJŚCIE DANYCH (REDAKTOR) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🖋️ Treść Artykułu")
    f_tytul_seo = st.text_input("Tytuł (Nagłówek):")
    f_lead = st.text_area("Lead (pogrubiony):", height=100)
    
    st.info("""
    **Formatowanie zdjęć (Wielkość liter nie ma znaczenia):**
    - `[COVER]` -> 550px
    - `[IMG1 PION]` lub `[IMG1 KWADRAT]` -> 500px
    - `[IMG1]` lub `[IMG1 POZIOM]` -> 675px
    """)
    
    f_body = st.text_area("Tekst główny:", height=450)

with col2:
    st.subheader("👤 Metadane i Stopka")
    f_author_name = st.text_input("Imię i nazwisko autora:")
    f_bio = st.text_area("BIO autora (bez nazwiska):", height=100)
    f_slug = st.text_input("Slug (URL):")
    f_meta = st.text_area("Metaopis (SEO):", height=80)
    st.divider()
    f_ksiazka = st.text_area("Sekcja 'Książka':", height=80)
    f_przypisy = st.text_area("Przypisy (każdy w nowej linii):", height=150)

# --- GENEROWANIE DLA WORDPRESSOWCA ---
if st.button("🚀 GENERUJ PACZKĘ DLA WORDPRESS"):
    if not author_code or not f_body:
        st.error("Wymagany kod autora i treść główna!")
    else:
        html_body = []
        
        # 1. Lead
        if f_lead:
            html_body.append(f'<b>{wyczysc_brudy_kopiowania(f_lead)}</b>')
        
        # 2. Tekst główny i listy
        lines = f_body.splitlines()
        in_list = False
        
        for line in lines:
            line = wyczysc_brudy_kopiowania(line)
            if not line:
                if in_list:
                    html_body.append('</ol>')
                    in_list = False
                continue
            
            # Detekcja listy
            if re.match(r'^\d+\.\s', line):
                if not in_list:
                    html_body.append('<ol>')
                    in_list = True
                txt = re.sub(r'^\d+\.\s', '', line).strip()
                html_body.append(f'<li><span style="font-weight: 400;">{uczyn_linki_klikalnymi(txt)}</span></li>')
                continue
            else:
                if in_list:
                    html_body.append('</ol>')
                    in_list = False

            # Detekcja wyimków
            line_lower = line.lower()
            if line_lower.startswith("wyimek:") or line.startswith(">"):
                if line.startswith(">"):
                    txt = line.lstrip("> ").strip()
                else:
                    txt = line[7:].strip()
                
                txt = txt.strip('"').strip('„').strip('”')
                html_body.append(f'<blockquote><span style="font-weight: 400;">„{uczyn_linki_klikalnymi(txt)}”</span></blockquote>')
                continue
            
            # Detekcja obrazków (Tagi w nawiasach [])
            if "[" in line and "]" in line:
                tags = re.findall(r'\[(.*?)\]', line)
                for t in tags:
                    html_body.append(generuj_obrazek(t, author_code, base_url, file_ext))
                continue
            
            # Zwykły akapit
            html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(line)}</span>')

        if in_list: html_body.append('</ol>')

        # 3. Stopka
        if f_ksiazka:
            html_body.append(f'<br />\n<b>Książka:</b>\n<span style="font-weight: 400;">{uczyn_linki_klikalnymi(f_ksiazka)}</span>')
        
        if f_przypisy:
            html_body.append(f'<br />\n<b>Przypisy:</b>')
            for p in f_przypisy.splitlines():
                if p.strip():
                    html_body.append(f'<span style="font-weight: 400;">{uczyn_linki_klikalnymi(p.strip())}</span>')

        html_body.append(f'\n<img src="{URL_BANER}" alt="" width="1080" height="100" />')

        # --- WYJŚCIE DO KOPIOWANIA ---
        st.divider()
        st.success("✅ Paczka gotowa!")
        
        out1, out2 = st.columns(2)
        with out1:
            st.text_input("1. TYTUŁ:", f_tytul_seo)
            st.text_area("2. TREŚĆ HTML (Wklej do edytora tekstowego WP):", "\n\n".join(html_body), height=500)
        with out2:
            st.text_input("3. SLUG (URL):", f_slug)
            st.text_area("4. METAOPIS (SEO):", f_meta, height=80)
            st.divider()
            st.text_area("5. BIO AUTORA:", f_bio, height=150)