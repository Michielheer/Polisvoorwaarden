import streamlit as st
import pdfplumber
import re
import openai
from dotenv import load_dotenv
import os
import pandas as pd

# API-sleutel laden uit .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Als er geen API-sleutel is, vraag de gebruiker erom
if not api_key:
    api_key = st.text_input("Voer je OpenAI API-sleutel in", type="password")
    if not api_key:
        st.warning("Voer een geldige OpenAI API-sleutel in om door te gaan.")
        st.stop()

openai.api_key = api_key

st.set_page_config(page_title="Voorwaardenanalyse", layout="wide")
st.title("Voorwaarden vergelijken met AI")

# Functie om volledige PDF-tekst te extraheren
def extract_full_text(uploaded_file):
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return full_text
    except Exception as e:
        st.error(f"Fout bij het verwerken van PDF: {str(e)}")
        return ""

# Functie om twee volledige documenten te vergelijken
def vergelijk_volledige_documenten(doc_a_text, doc_b_text, max_tokens=8000):
    # Beperk de lengte van beide documenten voor de context van het model
    doc_a_words = doc_a_text.split()
    doc_b_words = doc_b_text.split()
    
    if len(doc_a_words) > max_tokens:
        doc_a_text = " ".join(doc_a_words[:max_tokens]) + "..."
    if len(doc_b_words) > max_tokens:
        doc_b_text = " ".join(doc_b_words[:max_tokens]) + "..."
    
    # Bereid de prompt voor
    system_prompt = """
    Je bent een expert in het analyseren van voorwaarden-documenten. Je taak is om twee volledige documenten te vergelijken 
    en een samenvattend rapport op te stellen van alle substantiële verschillen die je vindt.
    
    Focus specifiek op:
    1. Verschillen in dekkingen (wat wel/niet gedekt is)
    2. Verschillen in bedragen (eigen risico, maximale uitkeringen, etc.)
    3. Verschillen in voorwaarden en bepalingen
    4. Verschillen in definities en begrippen
    5. Verschillen in uitsluitingen
    
    Maak een gestructureerd rapport met duidelijke kopjes per categorie. 
    Vermeld alleen substantiële verschillen die mogelijk juridische of praktische gevolgen hebben.
    """
    
    try:
        # Maak API-call naar OpenAI
        response = openai.chat.completions.create(
            model="gpt-4o",  # Of ander geschikt model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"# DOCUMENT A:\n{doc_a_text}\n\n# DOCUMENT B:\n{doc_b_text}"}
            ],
            temperature=0,
            max_tokens=3000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Fout bij AI-analyse: {str(e)}")
        return f"Er is een fout opgetreden: {str(e)}"

def extract_sections_from_pdf(uploaded_file):
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        # Splits op koppen als '1 ', '2.3 ', 'Artikel 5 ', 'Hoofdstuk 2 '
        sections = re.split(r"(?:\n|^)(\d+(?:\.\d+)*\s+|Artikel\s+\d+\s+|Hoofdstuk\s+\d+\s+)", full_text)
        # sections is nu een lijst: [pre, kop1, tekst1, kop2, tekst2, ...]
        # we bouwen (kop, tekst) paren
        result = []
        current_header = None
        for i in range(1, len(sections), 2):
            try:
                header = sections[i].strip()
                body = sections[i+1].strip() if i+1 < len(sections) else ""
                if len(body.split()) > 10:
                    result.append((header, body))
            except IndexError:
                # Voorkom problemen met incomplete sectie-paren
                pass
        return result
    except Exception as e:
        st.error(f"Fout bij het verwerken van het PDF-bestand: {str(e)}")
        return []

def vergelijk_secties(sectie_a, sectie_b):
    # Bereid context voor
    prompt = f"""
    Vergelijk deze twee secties uit voorwaarden-documenten en identificeer substantiële verschillen:
    
    # SECTIE A:
    {sectie_a}
    
    # SECTIE B:
    {sectie_b}
    
    Focus op concrete verschillen in:
    - Dekkingen en verzekerde risico's
    - Uitsluitingen
    - Bedragen (inclusief eigen risico)
    - Voorwaarden en procedures
    - Definities
    
    Noem alleen SUBSTANTIËLE verschillen die de dekking of rechten veranderen.
    Negeer pure formuleringsverschillen of opmaak.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Je analyseert verschillen tussen voorwaarden-documenten. Wees bondig en concreet."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        if "geen substantiële verschillen" in result.lower() or "geen significante verschillen" in result.lower():
            return None
        return result
    except Exception as e:
        st.error(f"Fout bij AI-analyse: {str(e)}")
        return f"Fout bij analyse: {str(e)}"

# Upload interface
col1, col2 = st.columns(2)
with col1:
    pdf_a = st.file_uploader("Upload voorwaarden A (PDF)", type="pdf", key="pdfA")
with col2:
    pdf_b = st.file_uploader("Upload voorwaarden B (PDF)", type="pdf", key="pdfB")

# Als beide bestanden zijn geüpload, geef analyseoptie
if pdf_a and pdf_b:
    st.success("Beide documenten geladen!")
    
    # Kies analysemethode
    analyse_type = st.radio(
        "Kies analysemethode:",
        ["Volledig document vergelijken (snelst)", 
         "Selecteer specifieke secties om te vergelijken", 
         "Volledige vergelijking per sectie (uitgebreid)"]
    )
    
    if analyse_type == "Volledig document vergelijken (snelst)":
        if st.button("Start volledige documentvergelijking"):
            with st.spinner("Documenten worden geanalyseerd... Dit kan even duren voor grote bestanden."):
                # Extractie van volledige tekst uit beide PDFs
                doc_a_text = extract_full_text(pdf_a)
                doc_b_text = extract_full_text(pdf_b)
                
                if doc_a_text and doc_b_text:
                    # Voer de volledige documentvergelijking uit
                    vergelijking = vergelijk_volledige_documenten(doc_a_text, doc_b_text)
                    
                    # Toon resultaten
                    st.subheader("Vergelijking van volledige documenten")
                    st.markdown(vergelijking)
                    
                    # Bied mogelijkheid om specifieke delen van de tekst te bekijken
                    with st.expander("Bekijk eerste deel van document A"):
                        st.markdown(doc_a_text[:5000] + "...")
                    with st.expander("Bekijk eerste deel van document B"):
                        st.markdown(doc_b_text[:5000] + "...")
                else:
                    st.error("Kon niet beide documenten verwerken. Controleer of de PDF's correct zijn.")
    
    elif analyse_type == "Selecteer specifieke secties om te vergelijken":
        # Extractie van secties
        with st.spinner("Secties extraheren uit documenten..."):
            secties_a = extract_sections_from_pdf(pdf_a)
            secties_b = extract_sections_from_pdf(pdf_b)
        
        st.write(f"Document A bevat {len(secties_a)} secties")
        st.write(f"Document B bevat {len(secties_b)} secties")
        
        # Selectboxes voor beide documenten
        options_a = [f"{i+1}: {header[:50]}..." for i, (header, _) in enumerate(secties_a)]
        options_b = [f"{i+1}: {header[:50]}..." for i, (header, _) in enumerate(secties_b)]
        
        col1, col2 = st.columns(2)
        with col1:
            idx_a = st.selectbox("Selecteer sectie uit document A", range(len(options_a)), format_func=lambda i: options_a[i])
        with col2:
            idx_b = st.selectbox("Selecteer sectie uit document B", range(len(options_b)), format_func=lambda i: options_b[i])
        
        # Toon geselecteerde secties
        if st.button("Vergelijk geselecteerde secties"):
            _, text_a = secties_a[idx_a]
            _, text_b = secties_b[idx_b]
            
            st.subheader("Vergelijking van geselecteerde secties")
            
            with st.spinner("AI vergelijkt de secties..."):
                verschillen = vergelijk_secties(text_a, text_b)
            
            if verschillen:
                st.success("Verschillen gevonden!")
                st.markdown(verschillen)
            else:
                st.info("Geen substantiële verschillen gevonden tussen deze secties.")
            
            # Toon volledige secties in uitklapbare elementen
            with st.expander("Toon volledige tekst van sectie A"):
                st.markdown(text_a)
            with st.expander("Toon volledige tekst van sectie B"):
                st.markdown(text_b)
    
    else:  # Volledige vergelijking per sectie
        if st.button("Start volledige vergelijking per sectie"):
            st.subheader("Volledige vergelijking van alle secties")
            st.write("Dit kan even duren, afhankelijk van het aantal secties...")
            
            # Extractie van secties
            with st.spinner("Secties extraheren uit documenten..."):
                secties_a = extract_sections_from_pdf(pdf_a)
                secties_b = extract_sections_from_pdf(pdf_b)
            
            # Strategie: vergelijk sectie-voor-sectie op basis van koptekst
            # We maken een dictionary van kopteksten voor snellere matching
            kopjes_b = {header.strip().lower(): (i, body) for i, (header, body) in enumerate(secties_b)}
            
            # Resultaten verzamelen
            resultaten = []
            progress = st.progress(0)
            
            # Voor elke sectie in A, zoek overeenkomende sectie in B
            for i, (header_a, body_a) in enumerate(secties_a):
                # Update voortgang
                progress.progress((i + 1) / len(secties_a))
                
                # Zoek naar dezelfde sectiekop in document B
                header_a_clean = header_a.strip().lower()
                match_found = False
                
                # Zoek exacte match eerst
                if header_a_clean in kopjes_b:
                    idx_b, body_b = kopjes_b[header_a_clean]
                    match_found = True
                else:
                    # Probeer een numerieke match op secties als 1.2, 2.3.1 etc.
                    numerieke_match = re.match(r"^(\d+(?:\.\d+)*)", header_a_clean)
                    if numerieke_match:
                        # Zoek naar sectie met zelfde nummer
                        num_prefix = numerieke_match.group(1)
                        for k in kopjes_b:
                            if k.startswith(num_prefix):
                                idx_b, body_b = kopjes_b[k]
                                match_found = True
                                break
                
                if match_found:
                    # Beide secties gevonden, analyseer verschillen
                    verschil = vergelijk_secties(body_a, body_b)
                    if verschil:  # Alleen opnemen als er significante verschillen zijn
                        resultaten.append({
                            "Sectie A": header_a,
                            "Sectie B": secties_b[idx_b][0],
                            "Verschillen": verschil
                        })
            
            # Toon resultaten
            if resultaten:
                st.success(f"{len(resultaten)} secties met verschillen gevonden!")
                
                # Toon als dataframe
                df = pd.DataFrame(resultaten)
                st.dataframe(df, use_container_width=True)
                
                # Toon ook uitgebreid rapport
                st.subheader("Gedetailleerd rapport van verschillen")
                for i, res in enumerate(resultaten):
                    with st.expander(f"Sectie {i+1}: {res['Sectie A']} vs {res['Sectie B']}"):
                        st.markdown("### Verschillen")
                        st.markdown(res["Verschillen"])
                        
                        # Vind de oorspronkelijke teksten
                        for ha, ta in secties_a:
                            if ha == res["Sectie A"]:
                                st.markdown("### Tekst in document A")
                                st.markdown(ta[:1000] + "..." if len(ta) > 1000 else ta)
                                break
                        
                        for hb, tb in secties_b:
                            if hb == res["Sectie B"]:
                                st.markdown("### Tekst in document B")
                                st.markdown(tb[:1000] + "..." if len(tb) > 1000 else tb)
                                break
            else:
                st.info("Geen substantiële verschillen gevonden tussen de voorwaarden.")
else:
    st.info("Upload beide voorwaarden-documenten (PDF) om te beginnen.")
