# 🩺 AI Doctor — Streamlit App

Your personal AI health assistant: chat about symptoms & medicines, analyze blood
reports, check symptoms, track vitals, and set medicine reminders — with login,
registration, and a database.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

For photo report OCR you also need Tesseract installed locally
(Ubuntu/Debian: `sudo apt install tesseract-ocr`).

## Host it LIVE (free) on Streamlit Community Cloud

1. **Create a GitHub account** at https://github.com (free).
2. **Create a new repository** (e.g. `ai-doctor`), set it to **Public**.
3. **Upload all files** from this folder (`app.py`, `database.py`,
   `medical_kb.py`, `report_parser.py`, `requirements.txt`, `packages.txt`,
   `.streamlit/config.toml`) to the repository.
4. Go to **https://share.streamlit.io** and sign in with GitHub.
5. Click **"Create app"** → select your repository, branch `main`, file `app.py`
   → **Deploy**.
6. In ~2–3 minutes you get a **live public URL** like
   `https://ai-doctor.streamlit.app` 🎉

### Optional: real GPT-powered chat
In the app sidebar, open **AI mode** and paste an **OpenAI API key**.
Without a key, the built-in medical knowledge base answers everything offline.

### Notes
- The SQLite database file lives with the app. On the free cloud tier the app
  may sleep when idle and the DB file can reset on redeploy — fine for personal use.
- This app gives general health information, not medical advice.

Stay healthy! 🌿
