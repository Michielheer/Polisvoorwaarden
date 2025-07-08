# PDF Vergelijker - Polisvoorwaarden

Een Streamlit applicatie die automatisch polisvoorwaarden van verschillende verzekeraars vergelijkt en de verschillen in een overzichtelijk formaat presenteert.

## Functies

- **PDF Upload**: Upload twee PDF bestanden met polisvoorwaarden
- **Automatische Analyse**: Gebruikt OpenAI GPT-4 om verschillen te identificeren
- **Meerdere Output Formaten**: 
  - Gedetailleerde tekstvergelijking
  - Overzichtstabel met verschillen
  - Downloadbare Word documenten
  - Downloadbare HTML rapporten
- **Professionele Presentatie**: Nette opmaak met status indicators

## Installatie

1. Clone de repository:
```bash
git clone https://github.com/Michielheer/Polisvoorwaarden.git
cd Polisvoorwaarden
```

2. Installeer de vereiste packages:
```bash
pip install streamlit pdfplumber openai python-dotenv python-docx pandas
```

3. Stel je OpenAI API key in in de `app.py` file of via een `.env` bestand.

## Gebruik

1. Start de applicatie:
```bash
streamlit run app.py
```

2. Upload twee PDF bestanden met polisvoorwaarden
3. Klik op "Vergelijk documenten"
4. Bekijk de resultaten en download de rapporten

## Bestandsstructuur

- `app.py` - Hoofdapplicatie met Streamlit interface
- `eenvoudige_vergelijker.py` - Eenvoudigere versie van de vergelijker
- `index.html` - Web interface (alternatief)
- `test.jsx` - React component voor testing

## Technologieën

- **Streamlit** - Web interface
- **OpenAI GPT-4** - AI-gedreven vergelijking
- **pdfplumber** - PDF tekst extractie
- **python-docx** - Word document generatie
- **Pandas** - Data verwerking

## Licentie

Dit project is voor persoonlijk gebruik ontwikkeld. 