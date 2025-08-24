# Case Prático AutoU — Classificador de E-mails (pt-BR)

Aplicação web simples (Flask) que:
- Aceita upload de `.txt`/`.pdf` **ou** texto colado.
- Classifica o e-mail como **Produtivo** ou **Improdutivo** (heurística leve).
- Gera **resposta sugerida** (via OpenAI se `OPENAI_API_KEY` estiver definida, senão usa templates locais).

## Executar localmente

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# (opcional) export OPENAI_API_KEY=seu_token
python app.py
```

Abra: http://127.0.0.1:5000

## Estrutura
```
.
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    ├── styles.css
    └── main.js
```

## Observações
- Se não quiser usar OpenAI, o app já funciona com as respostas padrão.
- A leitura de PDF usa `PyPDF2`; para PDFs digitalizados (imagem), seria necessário OCR (ex.: Tesseract), que não está incluso.