import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from io import BytesIO
from typing import Tuple
import re

# PDF reading
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# NLP imports
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Baixar recursos do NLTK (executar uma vez)
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("omw-1.4")

stop_words = set(stopwords.words("portuguese"))
lemmatizer = WordNetLemmatizer()

load_dotenv()

app = Flask(__name__)

ALLOWED_EXTENSIONS = {"txt", "pdf"}

# --------- Helpers ---------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def read_txt(file_storage) -> str:
    return file_storage.read().decode("utf-8", errors="ignore")

def read_pdf(file_storage) -> str:
    if PyPDF2 is None:
        return ""
    reader = PyPDF2.PdfReader(BytesIO(file_storage.read()))
    text = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        text.append(txt)
    return "\n".join(text)

def extract_email_text(uploaded_file, pasted_text: str) -> str:
    if uploaded_file and uploaded_file.filename and allowed_file(uploaded_file.filename):
        ext = uploaded_file.filename.rsplit(".", 1)[1].lower()
        if ext == "txt":
            return read_txt(uploaded_file)
        elif ext == "pdf":
            return read_pdf(uploaded_file)
    return pasted_text or ""

# --------- NLP Preprocessing ---------
def preprocess_text(text: str) -> str:
    # Remove caracteres especiais
    text = re.sub(r"[^a-zA-Z0-9çãáéíóúàèêõô\s]", " ", text)
    # Lowercase
    text = text.lower()
    # Tokenização simples
    words = text.split()
    # Remove stopwords e aplica lemmatization
    words = [lemmatizer.lemmatize(w) for w in words if w not in stop_words]
    # Junta de volta em string
    return " ".join(words)

# --------- Simple heuristic classifier ---------
PRODUCTIVE_KEYWORDS = [
    "suporte", "erro", "bug", "falha", "acesso", "login",
    "status", "atualização", "andamento", "protocolo",
    "solicito", "solicitação", "como faço", "não consigo", "ajuda",
    "documento", "anexo", "prazo", "nota fiscal", "chamado", "ticket"
]
UNPRODUCTIVE_KEYWORDS = [
    "feliz natal", "bom dia", "boa tarde", "parabéns", "agradeço", "obrigado", "obrigada",
    "boas festas", "feliz ano novo", "saudações", "gentileza", "atenciosamente"
]

def classify_email(text: str) -> str:
    t = text.lower()
    prod_hits = sum(1 for k in PRODUCTIVE_KEYWORDS if k in t)
    unprod_hits = sum(1 for k in UNPRODUCTIVE_KEYWORDS if k in t)

    if "anexo" in t or "segue em anexo" in t:
        prod_hits += 1

    if "?" in t or re.search(r"\b(poderia|pode|como)\b", t):
        prod_hits += 1
    if prod_hits >= unprod_hits:
        return "Produtivo"
    return "Improdutivo"


def suggest_reply(category: str, text: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = f"""
Você é um assistente de atendimento ao cliente do setor financeiro.
Classificação: {category}.
Gere uma resposta breve, educada e objetiva em português brasileiro ao e-mail abaixo.
Inclua próximos passos claros e peça informações essenciais se estiverem faltando.
E-mail:
\"\"\"{text.strip()[:4000]}\"\"\"
Responda apenas com o corpo do e-mail (sem saudação inicial genérica nem assinatura).
"""
            chat = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=220,
            )
            content = chat.choices[0].message.content.strip()
            return content
        except Exception:
            pass  

    
    if category == "Produtivo":
        if re.search(r"\b(status|andamento|protocolo)\b", text.lower()):
            return (
                "Verificamos seu pedido e vamos consultar o status interno. "
                "Por favor, confirme o número do protocolo/CPF/CNPJ e a data da solicitação. "
                "Assim que atualizado, retornaremos neste mesmo e-mail."
            )
        if re.search(r"\b(acesso|login|senha|não consigo)\b", text.lower()):
            return (
                "Entendi a dificuldade de acesso. Para agilizar, informe o CPF/CNPJ, e-mail cadastrado "
                "e, se possível, um print do erro. Já encaminhei para o time técnico e "
                "retornaremos com as orientações de desbloqueio."
            )
        return (
            "Recebemos sua solicitação. Para prosseguir, compartilhe os dados essenciais "
            "(CPF/CNPJ, número do protocolo e detalhes do caso). Assim que recebermos, "
            "daremos andamento e retornaremos com a atualização."
        )
    else:
        return (
            "Agradecemos a mensagem! Não identificamos necessidade de ação neste momento. "
            "Se precisar de suporte ou tiver alguma solicitação específica, conte conosco por aqui."
        )

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/classificar", methods=["POST"])
def classificar():
    pasted_text = request.form.get("emailText", "").strip()
    uploaded_file = request.files.get("emailFile")

    text = extract_email_text(uploaded_file, pasted_text)
    if not text:
        return jsonify({"ok": False, "error": "Nenhum conteúdo de e-mail fornecido."}), 400

    # Aplica NLP básico antes de classificar
    text_nlp = preprocess_text(text)

    categoria = classify_email(text_nlp)
    resposta = suggest_reply(categoria, text)
    return jsonify({"ok": True, "categoria": categoria, "resposta": resposta})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
