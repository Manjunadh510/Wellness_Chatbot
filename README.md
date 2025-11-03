# Wellness Guide AI Chatbot 💬

A health-assistant chatbot with:
- ✅ User registration & login (JWT-based auth)
- ✅ Admin dashboard
- ✅ Chat history stored in SQLite
- ✅ Multilingual support (English, Hindi, Hinglish translation)
- ✅ spaCy NER
- ✅ Streamlit frontend + Flask backend


✅ Install dependencies
pip install -r requirements.txt

✅  Download spaCy model
python -m spacy download en_core_web_sm

✅ Run Backend (Flask)
python app.py
Backend runs at:

http://127.0.0.1:5000

✅ Run Frontend (Streamlit)
streamlit run frontend.py

Frontend runs at:
http://localhost:850
