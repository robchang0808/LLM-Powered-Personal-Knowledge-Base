# Personal Knowledge Base – Behavioral Finance 

## Setup

### 1. Get a free Gemini API key
Go to https://aistudio.google.com → sign in with Google → "Get API Key" → Create one.

### 2. Set your key

Mac/Linux:
```bash
export GEMINI_API_KEY=AIzaSyAKU4CuDDmG0S1ZWwmS2r8rS9_xSej7SOU
```

Windows (Command Prompt):
```cmd
set GEMINI_API_KEY=AIzaSyAKU4CuDDmG0S1ZWwmS2r8rS9_xSej7SOU
```

Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY="AIzaSyAKU4CuDDmG0S1ZWwmS2r8rS9_xSej7SOU"
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run
```bash
python app.py
```

### 5. Open in browser
```
http://localhost:5050
```

## First steps
1. Go to **Compile Wiki** and click "Compile Now" — Gemini will read the 4 pre-loaded sources and generate wiki articles automatically
2. Go to **Browse Wiki** to read the articles
3. Go to **Ask Questions** and try: *"Why do investors hold losing stocks too long?"*

## Structure
```
kb_system/
├── app.py              Web app (Flask)
├── requirements.txt
├── README.md
├── raw/                Raw notes (4 pre-seeded on Behavioral Finance)
└── wiki/               LLM-compiled articles (generated on first compile)
```
