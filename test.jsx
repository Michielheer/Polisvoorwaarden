import React, { useState } from "react";
import { Upload, AlertTriangle, Loader2, CheckCircle, Download } from "lucide-react";

const PolicyProcessor = () => {
  const [pdfs, setPdfs] = useState({ pdf1: null, pdf2: null });
  const [comparison, setComparison] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const extractTextFromPdf = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("/api/extract-text", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("PDF extractie mislukt");
      const data = await res.json();
      return data.text;
    } catch (err) {
      throw err;
    }
  };

  const compareWithOpenAI = async (text1, text2, name1, name2) => {
    const prompt = `Vergelijk de polisvoorwaarden van ${name1} en ${name2}. Geef een puntsgewijze opsomming van **de concrete en expliciete verschillen**, per onderdeel:

- Artikel 1: Gedekte schadeoorzaken
- Artikel 2: Wat te doen bij schade
- Artikel 3: Uitsluitingen
- Artikel 4: Aanvullende dekkingen
- Eigen risico
- Maximumvergoedingen
- Dekking op locatie (woning, perceel, auto, tijdelijk elders)
- Verplichtingen bij verhuizing of verbouwing

**Gebruik dit format per onderdeel:**
🔹 Verschil in formulering tussen ${name1} en ${name2}
🔹 Specifieke clausules of bedragen die wel bij ${name1} staan maar niet bij ${name2} (en andersom)
🔹 Wijs op tekstuele afwezigheid of extra bepalingen bij ${name1} versus ${name2}

${name1}:
${text1}

${name2}:
${text2}`;

    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.REACT_APP_OPENAI_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4o",
        temperature: 0.2,
        messages: [
          {
            role: "system",
            content:
              "Je bent een juridisch specialist in verzekeringsrecht. Je vergelijkt polisvoorwaarden voor verzekeringen en geeft **gedetailleerde, letterlijke verschillen** per onderwerp. Je interpreteert niets. Je vergelijkt alleen wat er expliciet staat in de documenten."
          },
          { role: "user", content: prompt },
        ],
      }),
    });

    if (!res.ok) {
      throw new Error("OpenAI API fout");
    }

    const data = await res.json();
    return data.choices[0].message.content;
  };

  const handleCompare = async () => {
    if (!pdfs.pdf1 || !pdfs.pdf2) return;
    setLoading(true);
    setError(null);
    try {
      const [text1, text2] = await Promise.all([
        extractTextFromPdf(pdfs.pdf1),
        extractTextFromPdf(pdfs.pdf2),
      ]);
      const name1 = pdfs.pdf1.name.replace(/\.pdf$/i, '');
      const name2 = pdfs.pdf2.name.replace(/\.pdf$/i, '');
      const comparisonText = await compareWithOpenAI(text1, text2, name1, name2);
      setComparison(comparisonText);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadComparison = () => {
    const blob = new Blob([comparison], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "vergelijking.txt";
    link.click();
    URL.revokeObjectURL(url);
  };

  const downloadWordDocument = () => {
    // Simuleer Word document download (in echte implementatie zou je een backend API gebruiken)
    const content = `Vergelijking polisvoorwaarden: ${pdfs.pdf1?.name.replace(/\.pdf$/i, '')} vs ${pdfs.pdf2?.name.replace(/\.pdf$/i, '')}

Datum: ${new Date().toLocaleDateString('nl-NL')}

${comparison}

---
Deze vergelijking is automatisch gegenereerd en dient als indicatie. Raadpleeg altijd de originele polisvoorwaarden voor de exacte voorwaarden.`;

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Vergelijking_${pdfs.pdf1?.name.replace(/\.pdf$/i, '')}_vs_${pdfs.pdf2?.name.replace(/\.pdf$/i, '')}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h1 className="text-2xl font-bold mb-4">PDF Vergelijker</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {["pdf1", "pdf2"].map((key) => (
            <label
              key={key}
              className="flex flex-col items-center justify-center h-32 border-2 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100"
            >
              <div className="flex flex-col items-center">
                <Upload className="w-8 h-8 text-gray-400 mb-1" />
                <p className="text-sm text-gray-600">
                  {pdfs[key]?.name || `Upload ${key === "pdf1" ? "eerste" : "tweede"} polisvoorwaarden`}
                </p>
              </div>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setPdfs((prev) => ({ ...prev, [key]: e.target.files[0] }))}
                className="hidden"
              />
            </label>
          ))}
        </div>

        <div className="mt-6 text-center">
          <button
            onClick={handleCompare}
            disabled={!pdfs.pdf1 || !pdfs.pdf2 || loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="animate-spin h-5 w-5" /> Documenten worden vergeleken...
              </span>
            ) : (
              "Vergelijk documenten"
            )}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-600 rounded-lg flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {comparison && (
          <div className="mt-6 bg-gray-50 p-4 rounded-lg">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-800">
                Verschillen tussen {pdfs.pdf1?.name.replace(/\.pdf$/i, '')} en {pdfs.pdf2?.name.replace(/\.pdf$/i, '')}
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={downloadComparison}
                  className="flex items-center gap-1 bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700"
                >
                  <Download className="w-4 h-4" /> Download TXT
                </button>
                <button
                  onClick={downloadWordDocument}
                  className="flex items-center gap-1 bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700"
                >
                  <Download className="w-4 h-4" /> Download Word
                </button>
              </div>
            </div>
            <pre className="whitespace-pre-wrap text-sm text-gray-700 max-h-[500px] overflow-auto">
              {comparison}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default PolicyProcessor; 