# Webster AI Assistant 🎓

An AI-powered academic assistant for Webster University Tashkent students.
Supports English, Uzbek, and Russian.

## Setup Instructions

### Step 1 — Install dependencies
```
pip3 install -r requirements.txt
```

### Step 2 — Add your documents
Copy these files into the `data/` folder:
- `webster-student-handbook.pdf`
- `COURSE_CATALOGS.docx`
- Any other Webster PDFs or DOCX files

### Step 3 — Load documents into the AI
```
python3 setup_documents.py
```

### Step 4 — Set your API key
```
export ANTHROPIC_API_KEY="your_key_here"
```

### Step 5 — Run the web app
```
python3 app.py
```
Then open: http://localhost:5001

### Step 6 — Run the Telegram bot (optional)
```
export WEBSTER_BOT_TOKEN="your_telegram_bot_token"
python3 telegram_bot.py
```

## Project Structure
```
webster-ai/
├── app.py                  # Flask web app
├── telegram_bot.py         # Telegram bot
├── assistant.py            # Core AI logic
├── vector_store.py         # Document search
├── document_processor.py   # Document loading
├── setup_documents.py      # One-time setup script
├── requirements.txt
├── templates/
│   └── index.html          # Web interface
└── data/                   # Put your Webster documents here
    ├── webster-student-handbook.pdf
    ├── COURSE_CATALOGS.docx
    └── vector_store.json   # Auto-generated after setup
```

## Research Paper
This project is part of a research study:
"Multilingual RAG-Based Academic Advising Assistant for International Universities: 
A Case Study at Webster University Tashkent"
