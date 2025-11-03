
import sqlite3
import jwt
import bcrypt
import datetime
from flask import Flask, jsonify, request
import re
import json
import random
import os


import spacy
from spacy.matcher import Matcher
from transformers import MarianMTModel, MarianTokenizer
from langdetect import detect
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from googletrans import Translator



app=Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
DB_NAME="users.db"
KB_NAME="knowledge_base.db"
ADMIN_DB="admins.db"
MARIAN_LOADED = False
translator = Translator()

## BASIC THINGS

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def jwt_token(email):
    payload = {
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")
    return token

def decode_jwt(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired."
    except jwt.InvalidTokenError:
        return None, "Invalid token."

def verify_jwt():
    """
    Returns: (email, error)
    """
    header = request.headers.get('Authorization')
    if not header:
      return None, "Missing Authorization header"

    parts = header.split()
    if len(parts) != 2 or parts[0] != "Bearer":
      return None, "Invalid Authorization header format"

    token = parts[1]
    payload, error = decode_jwt(token)
    if error:
        return None, error

    return payload['email'], None

##SPACY TRAIN AND TRANSLATION

try:
    hi_en_tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-hi-en")
    hi_en_model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-hi-en")
    en_hi_tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-hi")
    en_hi_model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-hi")
    MARIAN_LOADED = True
except Exception:
    print("MarianMT models failed to load. Multilingual support disabled.")


with open("health_knowledge_base_expanded.json", "r") as f:
      kb_data = json.load(f)

nlp = spacy.load("en_core_web_sm")
matcher = Matcher(nlp.vocab)

spacy_train_symptoms = set()
for data in kb_data:
    spacy_train_symptoms.add(data["condition"].lower())
    for phrase in data["symptoms"]:
        for word in str(phrase).lower().split():
                if len(word) > 3 and word not in ['with', 'like', 'from', 'over', 'more', 'less', 'than', 'only', 'high', 'low', 'or', 'and', 'feeling']:
                     spacy_train_symptoms.add(word)

spacy_train_body_parts = ["head", "stomach", "throat", "leg", "chest", "back","neck","eyes","nose","hand","ankle"]

# Add patterns
for term in spacy_train_symptoms:
    matcher.add("SYMPTOM", [[{"LOWER": t} for t in term.split()]])
for part in spacy_train_body_parts:
    matcher.add("BODY_PART", [[{"LOWER": t} for t in part.split()]])

### ADMIN RELATED
@app.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    # 🧠 Basic validation
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # ✅ Connect with row_factory for dict-like access
    conn = sqlite3.connect("admins.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM admin_users WHERE email = ?", (email,))
    admin = cursor.fetchone()
    conn.close()

    if not admin:
        return jsonify({"error": "Invalid email"}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), admin["password"].encode('utf-8')):
        return jsonify({"error": "Invalid password"}), 401

    token = jwt_token(admin["email"])

    return jsonify({
        "message": "Admin login successful",
        "token": token
    }), 200

@app.route("/admin/entity_stats", methods=["GET"])
def entity_stats():
    email, error = verify_jwt()
    if error:
        return jsonify({"error": error}), 401

    if email != "admin@gmail.com":
        return jsonify({"error": "Access denied"}), 403

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT entity, COUNT(*) as count
        FROM chat_messages
        WHERE role = 'bot' AND entity IS NOT NULL AND entity != ''
        GROUP BY entity
        ORDER BY count DESC
    """)

    data = [{"entity": row[0], "count": row[1]} for row in cursor.fetchall()]
    conn.close()

    return jsonify(data), 200


@app.route('/admin_stats', methods=['GET'])
def admin_stats():
    email, error = verify_jwt()
    if error:
        return jsonify({"error": error}), 401

    # Only admin allowed
    if email != "admin@gmail.com":
        return jsonify({"error": "Access denied"}), 403

    # Get stats
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chats")
    total_chats = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM feedback")
    total_feedbacks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chat_messages")
    total_queries = cursor.fetchone()[0]

    conn.close()
    conn = sqlite3.connect("knowledge_base.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM knowledge_base")
    total_kb = cursor.fetchone()[0]
    conn.close()
    return jsonify({
        "total_users": total_users,
        "total_chats": total_chats,
        "total_feedbacks": total_feedbacks,
        "total_queries": total_queries,
        "total_kb_items": total_kb
    }), 200


@app.route("/admin_get_feedbacks", methods=["GET"])
def get_feedbacks():
    email, error = verify_jwt()
    if error:
        return jsonify({"error": error}), 401

    if email != "admin@gmail.com":
        return jsonify({"error": "Access denied"}), 403

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, user_email, rating, comment, timestamp FROM feedback ORDER BY timestamp DESC")

    records = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(records), 200

@app.route("/admin_get_kb", methods=["GET"])
def admin_get_kb():
    email, error = verify_jwt()
    if error:
        return jsonify({"error": error}), 401

    if email != "admin@gmail.com":
        return jsonify({"error": "Access denied"}), 403

    conn = sqlite3.connect("knowledge_base.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, condition, first_aid, prevention FROM knowledge_base")
    rows = cursor.fetchall()
    conn.close()

    kb = [dict(row) for row in rows]
    return jsonify(kb), 200

@app.route("/admin/add_kb", methods=["POST"])
def admin_add_kb():

    email, error = verify_jwt()
    if error:
        return jsonify({"error": error}), 401

    if email != "admin@gmail.com":
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    condition = data.get("condition")
    first_aid = data.get("first_aid", "")
    prevention = data.get("prevention", "")

    conn = sqlite3.connect("knowledge_base.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO knowledge_base (condition, explanation, symptoms, first_aid, prevention) VALUES (?, ?, ?, ?, ?)",
            (condition, "", "[]", first_aid, prevention)
        )
        conn.commit()
        return jsonify({"message": "Added successfully"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Condition already exists"}), 400

    finally:
        conn.close()

@app.route("/admin/update_kb/<int:id>", methods=["PUT"])
def admin_update_kb(id):
    email, error = verify_jwt()
    if error:
        return jsonify({"error": error}), 401

    if email != "admin@gmail.com":
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    condition = data.get("condition")
    first_aid = data.get("first_aid")
    prevention = data.get("prevention")

    conn = sqlite3.connect("knowledge_base.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE knowledge_base SET condition = ?, first_aid = ?, prevention = ? WHERE id = ?",
        (condition, first_aid, prevention, id)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Updated successfully"}), 200

@app.route("/admin/delete_kb/<int:id>", methods=["DELETE"])
def admin_delete_kb(id):

    email, error = verify_jwt()
    if error:
        return jsonify({"error": error}), 401

    if email != "admin@gmail.com":
        return jsonify({"error": "Access denied"}), 403

    conn = sqlite3.connect("knowledge_base.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM knowledge_base WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Deleted successfully"}), 200

###RESOPNSE RELATED

def extract_entities(text):
    doc = nlp(text)
    entities = {"symptoms": [], "body_parts": []}
    matches = matcher(doc)
    extracted_texts = set()
    for match_id, start, end in matches:
        token_text = doc[start:end].text
        match_text = token_text.lower()

        if match_text not in extracted_texts:
          label = nlp.vocab.strings[match_id]
          if label == "SYMPTOM":
              entities["symptoms"].append(token_text)
          elif label == "BODY_PART":
              entities["body_parts"].append(token_text)
          extracted_texts.add(match_text)
    return entities

def translate_text(text, tokenizer, model):
    tokens = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        translated = model.generate(
            **tokens,
            max_length=512,
            num_beams=4,
            early_stopping=True
        )
    return tokenizer.decode(translated[0], skip_special_tokens=True)

def google_translate_text(text, dest_lang="hi", src_lang="en"):
    try:
        result = translator.translate(text, src=src_lang, dest=dest_lang)
        return result.text
    except Exception as e:
        print("Translation error:", e)
        return text

def detect_language(text):
    if re.search(r"[^\x00-\x7F]", text):
        return "hindi"

    try:
      lang = detect(text)
    except:
      lang = "en"

    if lang == "hi":
        return "hindi"

    # Check for Hinglish keywords
    hinglish_keywords = [
        "mujhe", "hai", "bukhar", "dard", "thoda", "sir", "khansi",
        "pet", "jala", "bukhar", "haath", "pair", "thak", "kamjor", "nahi"
    ]
    if any(word in text.lower() for word in hinglish_keywords):
        return "hinglish"

    return "english"

def hinglish_to_hindi(text):
    try:
        return transliterate(text, sanscript.ITRANS, sanscript.DEVANAGARI)
    except Exception:
        return text

def preprocess_input(user_input):
    lang = detect_language(user_input)
    original_lang = lang

    if lang == "english":
        text = user_input
    elif lang == "hindi":
        text = translate_text(user_input, hi_en_tokenizer, hi_en_model)
    elif lang == "hinglish":
        hindi_script = hinglish_to_hindi(user_input)
        text = translate_text(hindi_script, hi_en_tokenizer, hi_en_model)
    else:
        text = user_input

    return text, original_lang

def get_advice_from_kb(extracted_symptoms, todo):
    if not extracted_symptoms:
        return None, None

    user_symptoms_set = set(s.lower().strip() for s in extracted_symptoms)
    best_match = None
    max_overlap = 0

    #Try exact condition name match first
    for entry in kb_data:
        condition_name = entry["condition"].lower()
        if condition_name in user_symptoms_set:
            advice = entry.get(todo, f"No specific {todo} advice available.")
            if isinstance(advice, list):
                advice = " ".join(advice)
            return advice, entry["condition"]

    # Fallback: fuzzy symptom overlap
    for entry in kb_data:
        kb_symptoms = set(word.lower().strip() for word in entry.get("symptoms", []))
        overlap = len(user_symptoms_set.intersection(kb_symptoms))
        if overlap > max_overlap:
            max_overlap = overlap
            best_match = entry

    if best_match and max_overlap > 0:
        advice = best_match.get(todo, f"No specific {todo} advice available.")
        if isinstance(advice, list):
            advice = " ".join(advice)
        return advice, best_match["condition"]

    return None, None

def generate_safe_response_en(extracted_symptoms, todo):
    advice, condition_name = get_advice_from_kb(extracted_symptoms, todo)
    action_type = "Prevention Tip" if todo == "prevention" else "First Aid"

    if advice and condition_name:
        response_body = f"Regarding **{condition_name}**, here is the recommended **{action_type}**: {advice}"
        final_response_en = response_body
    else:
        if extracted_symptoms:
             response_body = f"I found the terms: {', '.join(extracted_symptoms)}, but I couldn't find specific advice for that combination. Please consult a specialist."
             final_response_en = response_body
        else:
             response_body = "I'm sorry, I couldn't understand your query. Please rephrase your question about symptoms or first aid."
             final_response_en = response_body

    return final_response_en, condition_name

def clean_for_translation(text):
    text = re.sub(r"\*\*|\*|_|~|`", "", text)
    return text.strip()

##USER RELATED

@app.route("/", methods=["GET"])
def home():
    return {"message": "Flask backend is running!"}

@app.route('/signup', methods=['POST'])
def register_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    pwd = data.get('password')
    age = data.get('age')
    language = data.get('language')

    if not all([name, email, pwd, age, language]):
        return jsonify({"message": "All fields are required"}), 400

    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({"error": " Invalid email format"}), 400

    if len(pwd) < 8:
        return jsonify({"error": " Password must be at least 8 characters long."}), 400
    if not re.search(r'\d', pwd):
        return jsonify({"error": " Password must contain at least 1 digit."}), 400
    if not re.search(r'[@$!%*#?&]', pwd):
        return jsonify({"error": " Password must contain at least 1 special character."}), 400

    if(int(age) > 100 or int(age) < 10):
        return jsonify({"error": " Age must be between 10 and 100."}), 400

    if language not in ["English","Hindi"]:
        return jsonify({"error": " Language must English or Hindi Only."}), 400


    hashed_password = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        stmt="INSERT INTO users (name, email, password, age, language) VALUES (?, ?, ?, ?, ?)"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(stmt,(name, email, hashed_password, age, language))
        conn.commit()
        conn.close()

        token = jwt_token(email)
        return jsonify({
            "message": " User registered successfully",
            "token": token
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": " Email already exists"}), 400
    except Exception as e:
        app.logger.error(e, exc_info=True)
        return jsonify({"error": " Registration failed. Please try again."}), 500

@app.route('/signin', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    pwd = data.get('password')


    if not all([email, pwd]):
      return jsonify({"error": "Email and password are required"}), 400

    try:
      stmt="SELECT * FROM users WHERE email=?"
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(stmt, (email,))
      user = cursor.fetchone()
      conn.close()

      if user and bcrypt.checkpw(pwd.encode('utf-8'), user["password"].encode('utf-8')):
          token = jwt_token(user["email"])
          return jsonify({"message": "Login successful", "token": token}), 200
      else:
          return jsonify({"error": " Invalid credentials"}), 401
    except Exception as e:
        app.logger.error(e, exc_info=True)
        return jsonify({"error": " Login failed. Please try again."}), 500


@app.route('/profile', methods=['GET'])
def get_profile():
    email, error = verify_jwt()
    if error:
        return jsonify({"error": f" {error}"}), 401

    try:
        stmt="SELECT name, email, age, language FROM users WHERE email=?"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(stmt,(email,))
        user = cursor.fetchone()
        conn.close()

        if not user:
          return jsonify({"error": " User not found"}), 404
        profile_data = {
          "name": user["name"],
          "email": user["email"],
          "age": user["age"],
          "language": user["language"]
        }
        return jsonify({"profile": profile_data}), 200
    except Exception as e:
        app.logger.error(e, exc_info=True)
        return jsonify({"error": " Something went wrong. Please try again."}), 500

@app.route('/updateProfile', methods=['PUT'])
def update_profile():
    email, error = verify_jwt()
    if error:
        return jsonify({"error": f"{error}"}), 401

    data = request.get_json()
    name = data.get("name")
    age = data.get("age")
    language = data.get("language")

    if not all([name, age, language]):
        return jsonify({"error": " Name, age, and language cannot be empty."}), 400
    if language not in ["English","Hindi"]:
        return jsonify({"error": " Language must English or Hindi Only."}), 400
    if(int(age) > 100 or int(age) < 10):
        return jsonify({"error": " Age must be between 10 and 100."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET name=?, age=?, language=? WHERE email=?",
            (name, age, language, email)
        )
        conn.commit()
        conn.close()

        return jsonify({"message": "Profile updated successfully"}), 200

    except Exception as e:
        app.logger.error(e, exc_info=True)
        return jsonify({"error": "Unable to update profile. Please try again."}), 500

@app.route('/feedback', methods=['POST'])
def message_feedback():
    email, error = verify_jwt()
    if error:
        return jsonify({"error": error}), 401

    data = request.get_json()
    chat_id = data.get("chat_id")
    rating = data.get("rating")
    comment = data.get("comment", "")

    if not chat_id or rating is None:
        return jsonify({"error": "Invalid data"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback (chat_id, user_email, rating, comment)
        VALUES (?, ?, ?, ?)
    """, (chat_id, email, rating, comment))
    conn.commit()
    conn.close()

    return jsonify({"message": "Feedback recorded"}), 201



@app.route('/new_chat', methods=['POST'])
def new_chat():
    email, error = verify_jwt()
    if error:
        return jsonify({"error": f"{error}"}), 401

    data = request.get_json()
    title = data.get('title', 'New Chat')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get user_id using email
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    user_id = user['id']

    # Insert new chat row
    cursor.execute(
        'INSERT INTO chats (user_id, title) VALUES (?, ?)',
        (user_id, title)
    )
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'message': 'Chat created', 'chat_id': chat_id}), 200


@app.route('/get_chats', methods=['GET'])
def chat_history_list():
    email, error = verify_jwt()
    if error:
        return jsonify({"error": f"{error}"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    user_id = user['id']

    cursor.execute(
        'SELECT id, title, created_at FROM chats WHERE user_id = ? ORDER BY created_at DESC',
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    chats = [{'chat_id': r['id'], 'title': r['title'], 'created_at': r['created_at']} for r in rows]
    return jsonify({'chats': chats}), 200


@app.route('/get_chat/<int:chat_id>', methods=['GET'])
def get_chat(chat_id):
    email, error = verify_jwt()
    if error:
        return jsonify({"error": f"{error}"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT role, message, entity, timestamp
        FROM chat_messages
        WHERE chat_id = ?
        ORDER BY timestamp ASC
    ''', (chat_id,))
    rows = cursor.fetchall()
    conn.close()

    history = [{'role': r['role'], 'content': r['message'], 'entity': r['entity'], 'timestamp': r['timestamp']} for r in rows]
    return jsonify({'history': history}), 200


@app.route("/chat", methods=["POST"])
def chat():
    email, error = verify_jwt()
    if error:
        return jsonify({"error": f"{error}"}), 401

    data = request.get_json()
    message = data.get("message", "")
    chat_id = data.get("chat_id")
    if not message:
        return jsonify({"error": "Message is required"}), 400

    conn = get_db_connection()
    cursor= conn.cursor()

    cursor.execute("SELECT title FROM chats WHERE id = ?", (chat_id,))
    current_title = cursor.fetchone()['title']

    if current_title == "New Chat":
        new_title = message[:50].strip()  # first few words
        cursor.execute("UPDATE chats SET title = ? WHERE id = ?", (new_title, chat_id))

    cursor.execute(
    'INSERT INTO chat_messages (chat_id, role, message, entity) VALUES (?, ?, ?, ?)',
    (chat_id, 'user', message, ""))

    # {'symptoms': ['fever'], 'body_parts': ['throat']}

    message, user_lang = preprocess_input(message)
    todo = "prevention" if any(x in message for x in ["prevent", "prevention"]) else "first_aid"
    entities = extract_entities(message)
    slots = set(entities["symptoms"])
    response ,condition_name = generate_safe_response_en(slots, todo)


    if MARIAN_LOADED and user_lang in ["hindi", "hinglish"]:
        clean_resp = clean_for_translation(response)
        # response = translate_text(clean_resp, en_hi_tokenizer, en_hi_model)
        response=google_translate_text(clean_resp, dest_lang="hi", src_lang="en")
        response += "\n ⚠️ यह सामान्य जानकारी है। कृपया डॉक्टर से सलाह लें।"
    else :
        DISCLAIMER_EN = " \n ⚠️ This is general advice, not a medical diagnosis. Please consult a doctor for proper guidance."
        response += DISCLAIMER_EN

    cursor.execute(
    'INSERT INTO chat_messages (chat_id, role, message, entity) VALUES (?, ?, ?, ?)',
    (chat_id, 'bot', response, condition_name))

    conn.commit()
    conn.close()


    return jsonify({
        # "intent": intent,
        "message": response,
        "entity" : condition_name or ""
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

