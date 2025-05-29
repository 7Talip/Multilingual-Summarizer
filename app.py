
import os
import gradio as gr
import pdfplumber
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

LANGUAGES = ["English", "Turkish", "Arabic", "French", "German", "Spanish"]

TRANSLATIONS = {
    "English": {
        "summary_lang": "🗣️ Summary Language",
        "char_limit": "🔢 Character Limit (approximate)",
        "text_input": "📥 Paste Text Here",
        "text_placeholder": "Or paste a document here...",
        "pdf_upload": "📄 Or Upload a PDF File",
        "output": "🧠 Output (Summary, Title, Keywords)",
        "run_button": "Summarize"
    },
    "Turkish": {
        "summary_lang": "🗣️ Özetleme Dili",
        "char_limit": "🔢 Karakter Sınırı (yaklaşık)",
        "text_input": "📥 Metni Buraya Yapıştırın",
        "text_placeholder": "Ya da bir belge yapıştırın...",
        "pdf_upload": "📄 Ya da bir PDF Yükleyin",
        "output": "🧠 Çıktı (Özet, Başlık, Anahtar Kelimeler)",
        "run_button": "Özetle"
    },
    "French": {
        "summary_lang": "🗣️ Langue du Résumé",
        "char_limit": "🔢 Limite de caractères (approximative)",
        "text_input": "📥 Collez le texte ici",
        "text_placeholder": "Ou collez un document ici...",
        "pdf_upload": "📄 Ou téléchargez un fichier PDF",
        "output": "🧠 Résultat (Résumé, Titre, Mots-clés)",
        "run_button": "Résumer"
    },
    "German": {
        "summary_lang": "🗣️ Zusammenfassungs-Sprache",
        "char_limit": "🔢 Zeichenbegrenzung (ungefähr)",
        "text_input": "📥 Text hier einfügen",
        "text_placeholder": "Oder fügen Sie hier ein Dokument ein...",
        "pdf_upload": "📄 Oder laden Sie eine PDF-Datei hoch",
        "output": "🧠 Ausgabe (Zusammenfassung, Titel, Schlüsselwörter)",
        "run_button": "Zusammenfassen"
    },
    "Spanish": {
        "summary_lang": "🗣️ Idioma del Resumen",
        "char_limit": "🔢 Límite de caracteres (aproximado)",
        "text_input": "📥 Pega el texto aquí",
        "text_placeholder": "O pega un documento aquí...",
        "pdf_upload": "📄 O sube un archivo PDF",
        "output": "🧠 Resultado (Resumen, Título, Palabras clave)",
        "run_button": "Resumir"
    },
    "Arabic": {
        "summary_lang": "🗣️ لغة الملخص",
        "char_limit": "🔢 الحد التقريبي لعدد الأحرف",
        "text_input": "📥 الصق النص هنا",
        "text_placeholder": "أو الصق مستندًا هنا...",
        "pdf_upload": "📄 أو قم بتحميل ملف PDF",
        "output": "🧠 النتيجة (الملخص، العنوان، الكلمات المفتاحية)",
        "run_button": "تلخيص"
    }
}

def extract_text_from_pdf(file):
    try:
        with pdfplumber.open(file.name) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if not text.strip():
            return None, "The PDF appears to contain no extractable text."
        return text.strip(), None
    except Exception as e:
        return None, f"PDF reading error: {str(e)}"

def translate_text(text, target_lang):
    try:
        prompt = f"Translate the following text to {target_lang}:\n\n{text}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful translator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3000
        )
        return response.choices[0].message.content
    except Exception:
        return text

def analyze_text(text, summary_lang, char_limit):
    translated_text = translate_text(text, summary_lang)
    prompt = f"""You are a helpful assistant.

Please provide the following in {summary_lang}:
1. A clear and concise summary (limited to approximately {char_limit} characters).
2. A suitable title.
3. 5 relevant keywords.

Document:
{translated_text[:3000]}"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ OpenAI Error: {str(e)}"

def analyze_input(summary_lang, char_limit, text_input, pdf_file):
    text = ""
    error = None
    if pdf_file:
        text, error = extract_text_from_pdf(pdf_file)
    elif text_input and text_input.strip():
        text = text_input.strip()

    if error:
        return f"⚠️ PDF Error: {error}"
    if not text:
        return "⚠️ No text provided or extracted."

    return analyze_text(text, summary_lang, char_limit)

def interface_selector(interface_lang):
    t = TRANSLATIONS.get(interface_lang, TRANSLATIONS["English"])
    return (
        gr.update(visible=True),
        gr.update(label=t["summary_lang"]),
        gr.update(label=t["char_limit"]),
        gr.update(label=t["text_input"], placeholder=t["text_placeholder"]),
        gr.update(label=t["pdf_upload"]),
        gr.update(label=t["output"]),
        gr.update(value=t["run_button"])
    )

with gr.Blocks() as demo:
    gr.Markdown("## 🌐 Select Interface Language")

    with gr.Accordion("📘 View README / Usage Guide", open=False):
        gr.Markdown("""This application allows you to upload a PDF or paste text, select your preferred summary language, and receive:

- A clear summary ✂️  
- An auto-generated title 🏷️  
- 5 relevant keywords 🔑  

If the content language and summary language differ, the app will auto-translate before summarizing 🌐  

Powered by OpenAI GPT-3.5 and Gradio.""")

    lang_select = gr.Dropdown(label="Interface Language", choices=LANGUAGES, value="English")
    next_btn = gr.Button("Continue")

    with gr.Column(visible=False) as summary_section:
        summary_lang = gr.Dropdown(choices=LANGUAGES, value="English")
        char_limit = gr.Textbox(value="300")
        text_input = gr.Textbox(lines=10)
        pdf_file = gr.File()
        output = gr.Textbox()
        run_btn = gr.Button()

    next_btn.click(fn=interface_selector, inputs=[lang_select], outputs=[
        summary_section,
        summary_lang,
        char_limit,
        text_input,
        pdf_file,
        output,
        run_btn
    ])

    run_btn.click(fn=analyze_input, inputs=[summary_lang, char_limit, text_input, pdf_file], outputs=output)

demo.launch()
