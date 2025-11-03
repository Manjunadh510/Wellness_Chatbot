import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter


BACKEND_URL = "http://127.0.0.1:5000"

st.set_page_config(layout="wide")


# --- CSS for fixed header and layout ---
st.markdown(
    """
    <style>
        .fixedheader {
            margin:0;
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            background-color: #000;
            padding: 50px 20px 20px 20px;
        }
        .main-content {
            padding-top: 10px; /* Adjust padding to make space for the fixed header */
        }
        .block-container {
            padding-top: 45px;
            padding-left:0;
            padding-right:0;
            padding-bottom:0;
        }
        .stButton button {
            background-color: white;
            color: black;
            border: 1px solid #ccc;
            height:40px;
            padding: 10px;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .stButton button:hover {
            background-color: #e6e8eb;
        }
        .stSidebar {
            padding-top: 0;
            background-color:linear-gradient(90deg,rgba(42, 123, 155, 1) 0%, rgba(235, 235, 235, 1) 100%);
            # background: #020024;
            # background: linear-gradient(90deg, rgba(2, 0, 36, 1) 0%, rgba(9, 9, 121, 1) 0%, rgba(160, 192, 217, 1) 0%);
            # background: #2A7B9B;
            # background: linear-gradient(90deg,rgba(42, 123, 155, 1) 0%, rgba(252, 252, 252, 1) 72%, rgba(247, 247, 215, 1) 84%, rgba(247, 247, 215, 1) 95%);
        }
        .stSidebar button{
            background-color: white;
            color: black;
            box-shadow: 5px 5px 10px #878f9c;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            width: 180px;
            text-align:center;
            transition: background-color 0.3s;
        }
        .stSidebar button:hover {
            background-color: #e6e8eb;
        }
        .stApp{

          background: #2A7B9B;
          background: linear-gradient(90deg,rgba(42, 123, 155, 1) 0%, rgba(235, 235, 235, 1) 100%);
          #           background: #4fb4db;
          # background: linear-gradient(90deg,rgba(79, 180, 219, 1) 0%, rgba(70, 232, 137, 1) 100%, rgba(255, 252, 219, 1) 100%);
          #background-color:#e1e8e4;
        }
        .stForm {
            padding: 25px 30px 10px 30px; /* Space for the fixed header */
            background-color:white;
            min-height:400px;
            width:450px;
            border-radius:8px;
            box-shadow: 5px 5px 10px #878f9c;
            border:1px solid black;

        }
      .stChatInput{
        margin-bottom: -100px !important;
        padding-bottom: 0px !important;
        border:1px solid gray;
        border-radius:20px;
        box-shadow: 5px 5px 10px #878f9c;
      }



    </style>
    """,
    unsafe_allow_html=True
)


#intilaizing the session_state
if "token" not in st.session_state:
    st.session_state["token"] = None
    st.session_state["profile_data"] = {}

INITIAL_CHAT_MESSAGE = {"role": "assistant", "content": "Hello! I'm your Wellness Guide.How can I help you today?","entity":""}

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [INITIAL_CHAT_MESSAGE]

if "page" not in st.session_state:
    st.session_state["page"] = "login"

if "chat_id" not in st.session_state:
    st.session_state["chat_id"] = None

if "chat_list" not in st.session_state:
    st.session_state["chat_list"] = []


#similiar to middlewares functions
def login(email, password):
    url = f"{BACKEND_URL}/signin"
    data = {"email": email, "password": password}
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            token = response.json().get("token")
            st.session_state["token"] = token
            st.session_state["page"] = "profile"
            st.success(f"{response.json().get('message', 'Login successful')}")
            st.rerun()
        else:
            st.error(f"Login failed: {response.json().get('error', 'Unknown error')}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot Login.Please try again later.")


def register_user(name, email, password, age, language):
    url = f"{BACKEND_URL}/signup"
    data = {"name": name, "email": email, "password": password, "age": age, "language": language}
    try:
        response = requests.post(url, json=data)
        if response.status_code == 201:
            token = response.json().get("token")
            st.session_state["token"] = token
            st.session_state["page"] = "profile"
            st.success(f"{response.json().get('message', 'User registered successfully')}")
            st.rerun()
        else:
            st.error(f"Registration failed: {response.json().get('error', 'Unknown error')}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot Register.Please try again later.")



def get_profile():
    url = f"{BACKEND_URL}/profile"
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            profile_data = response.json().get("profile")
            st.session_state["profile_data"] = profile_data
            st.session_state["page"] = "profile"
            st.rerun()
        else:
            st.error(f"Failed to fetch profile: {response.json().get('error', 'Unknown error')}")

    except requests.exceptions.ConnectionError:
        st.error("Cannot get profile.Please try again later.")


def update_profile(name, age, language):
    url = f"{BACKEND_URL}/updateProfile"
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    data = {"name": name, "age": age, "language": language}
    try:
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            st.success("Profile updated successfully!")
            get_profile()
        else:
            st.error(f"Update failed: {response.json().get('error', 'Unknown error')}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot update profile.Please try again later.")

def chat_message(message):
    """
    Sends a user message to the Flask chat endpoint and updates history.
    """
    url = f"{BACKEND_URL}/chat"
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    data = {
        "message": message,
        "chat_id": st.session_state.get("chat_id")
    }

    st.session_state.chat_history.append({"role": "user", "content": message,"entity":""})

    with st.spinner("Thinking..."):
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                bot_response = response.json().get("message", "I'm having trouble processing that.")
                bot_entity = response.json().get("entity", "")
                st.session_state.chat_history.append({"role": "bot", "content": bot_response,"entity":bot_entity})
            else:
                st.error("Chat failed.")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to the backend.")

        st.rerun()

def load_chat(chat_id):
    """
    Loads messages for a selected chat and sets session state.
    """
    url = f"{BACKEND_URL}/get_chat/{chat_id}"
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            messages = response.json().get("history", [])
            st.session_state.chat_history = messages
            st.session_state.chat_id = chat_id
            st.session_state.page = "chat"
            st.rerun()
        else:
            st.error("Failed to load chat messages.")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend.")

def send_message_feedback(rating, comment=""):
    url = f"{BACKEND_URL}/feedback"
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    data = {
        "chat_id": st.session_state.chat_id,
        "rating": rating,
        "comment": comment
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            st.toast("Feedback Submitted.", icon="✅")
        else :
            st.toast("Oops! Something went wrong.", icon="🚨")
    except requests.exceptions.ConnectionError:
        st.error("Server not reachable.")


#frontend functioning


def show_login_page():
    col1, col2, col3 = st.columns([1, 1, 1])  # Center the form
    with col2:
        with st.form("login_form"):
            st.markdown("<div style='text-align: center; padding-bottom:10px;'><h3>User Login</h3></div>", unsafe_allow_html=True)
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")
            if submitted:
                login(email, password)

        st.markdown("<div style='font-size:20px; font-weight:bold;'>Don't have an account?</div>", unsafe_allow_html=True)
        if st.button("Register", key="go_to_register",width=150):
            st.session_state.page = "register"
            st.rerun()



def show_register_page():
    col1, col2, col3 = st.columns([1, 1, 1])  # Center the form
    with col2:

        with st.form("register_form"):
            st.markdown("<div style='text-align: center; padding-bottom:10px;'><h3>Register User</h3></div>", unsafe_allow_html=True)
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            age = st.number_input("Age", min_value=10, max_value=100)
            language = st.selectbox("Language", ["English", "Hindi"])
            submitted = st.form_submit_button("Register")
            if submitted:
                register_user(name, email, password, age, language)

        st.markdown("<div style='font-size:20px; font-weight:bold;'>Already have an account ?</div>", unsafe_allow_html=True)
        if st.button("Login", key="go_to_login",width=150):
            st.session_state.page = "login"
            st.rerun()


def show_profile_page():
    if not st.session_state.get('profile_data'):
        get_profile()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
      if st.session_state.get('profile_data'):
          profile_data = st.session_state.profile_data
          st.markdown("<div style='text-align: center; padding-bottom:10px;'><h3>User Profile</h3></div>", unsafe_allow_html=True)
          st.markdown(f"<p style='font-size:20px;'><strong>Name:</strong> {profile_data.get('name')}</p>", unsafe_allow_html=True)
          st.markdown(f"<p style='font-size:20px;'><strong>Email:</strong> {profile_data.get('email')}</p>", unsafe_allow_html=True)
          st.markdown(f"<p style='font-size:20px;'><strong>Age:</strong> {profile_data.get('age')}</p>", unsafe_allow_html=True)
          st.markdown(f"<p style='font-size:20px;'><strong>Language:</strong> {profile_data.get('language')}</p>", unsafe_allow_html=True)




def show_update_profile_page():
    if not st.session_state.get('profile_data'):
        get_profile()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
      st.markdown("<div style='text-align: center; padding-bottom:10px;'><h3>Update Profile</h3></div>", unsafe_allow_html=True)
      if st.session_state.get('profile_data'):
          current_name = st.session_state.profile_data.get('name')
          current_age = st.session_state.profile_data.get('age')
          current_language = st.session_state.profile_data.get('language')

          with st.form("update_form"):
              name = st.text_input("Name", value=current_name)
              age = st.number_input("Age", min_value=10, max_value=100, value=int(current_age))
              language = st.selectbox("Language", ["English", "Hindi"], index=["English", "Hindi"].index(current_language))
              submitted = st.form_submit_button("Update")
              if submitted:
                  update_profile(name, age, language)

def show_chat_history_page():
    st.markdown("<h3 style='text-align:center;'>Previous Chats</h3>", unsafe_allow_html=True)

    if not st.session_state.get("chat_list"):
        st.info("No previous chats found.")
        return

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        for chat in st.session_state.chat_list:
            chat_id = chat.get("chat_id")
            title = chat.get("title", f"Chat {chat_id}")
            if st.button(title, key=f"chat_{chat_id}",width=500):
                load_chat(chat_id)
                st.session_state.page = "chat"
                st.rerun()


def show_chatbot_page():
    if not st.session_state.token:
        st.error("Please log in to use the chatbot.")
        return

    #st.markdown("<h3 style='text-align: center; color:black;'>Your AI Wellness Guide</h3>", unsafe_allow_html=True)

    # --- Display Chat History ---
    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state.chat_history):
            role = msg.get("role", "")
            content = msg.get("content", "")
            entity = msg.get("entity", "")

            if role == "user":
                st.markdown(f"""
                <div style='text-align: right; margin-right: 150px ; '>
                    <span style='display:inline-block; background-color:#DCF8C6; color:black; padding:10px 15px; border-radius: 15px; max-width:70%;'>
                        {content}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='text-align: left; margin-left:150px;margin-top:20px; margin-bottom:20px;'>
                    <span style='display:inline-block; background-color:white; color:black; padding:10px 15px; border-radius: 15px; max-width:70%;'>
                        {content }
                    </span>
                </div>
                """, unsafe_allow_html=True)

                if role in ("assistant", "bot") and entity:
                    col1, col2 = st.columns([0.13, 0.87])  # Adjust ratio to match bubble position
                    with col2:
                        with st.popover("💬 Was this response helpful?"):
                            rating = st.feedback("stars", key=f"feedback_{st.session_state.chat_id}_{i}")
                            comment = st.text_input("Leave your comment", key=f"comment_{st.session_state.chat_id}_{i}")
                            if st.button("Submit Feedback", key=f"submit_{st.session_state.chat_id}_{i}",width=150):
                                send_message_feedback(rating, comment)


    # Input box
    if prompt := st.chat_input("Type your message here..."):
        chat_message(prompt)

#ADMIN

def show_admin_login():

    col1, col2, col3 = st.columns([1, 1, 1])  # Center the form
    with col2:
        with st.form("admin_login_form"):
            st.markdown("<div style='text-align: center; padding-bottom:10px;'><h3>👨‍💼 Admin Login</h3></div>", unsafe_allow_html=True)
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")
            if submitted:
                response = requests.post(f"{BACKEND_URL}/admin_login", json={"email": email, "password": password})
                if response.status_code == 200:
                    st.session_state.admin_token = response.json()["token"]
                    st.session_state.page = "admin_dashboard"
                    st.toast("Login successful!")
                    st.rerun()
                else:
                    st.error(response.json().get("error", "Login failed"))


def show_ratings_chart():

    headers = {"Authorization": f"Bearer {st.session_state.admin_token}"}
    res = requests.get(f"{BACKEND_URL}/admin_get_feedbacks", headers=headers)

    if res.status_code != 200:
        st.error("Could not load ratings")
        return

    data = res.json()
    if not data:
        st.info("No ratings yet.")
        return

    ratings = [int(fb.get("rating", 0) + 1 ) for fb in data if (fb.get("rating", -1) + 1 )]

    rating_counts = Counter(ratings)
    rating_labels = [1, 2, 3, 4, 5]   # fixed x-axis
    rating_values = [rating_counts.get(r, 0) for r in rating_labels]

    # Plot
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.bar(rating_labels, rating_values)
    ax.set_xlabel("Rating")
    ax.set_ylabel("Count")
    ax.set_title("User Rating Distribution")
    ax.set_xticks([1, 2, 3, 4, 5])   # ensure integer ticks

    st.pyplot(fig)


def show_entity_stats():
    headers = {"Authorization": f"Bearer {st.session_state.admin_token}"}
    res = requests.get(f"{BACKEND_URL}/admin/entity_stats", headers=headers)

    if res.status_code != 200:
        st.error("Unable to load entity stats")
        return

    data = res.json()
    if not data:
        st.info("No Topics yet.")
        return
    entities = [row["entity"] for row in data]
    counts = [row["count"] for row in data]
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.pie(counts, labels=entities, autopct='%1.1f%%', wedgeprops=dict(width=0.4))
    ax.set_title("Most Asked Health Topics (Entities)")
    st.pyplot(fig)



def show_admin_stats():
    st.markdown("""
        <h3 style='text-align: center; margin-bottom:20px;'>📊 Admin Dashboard</h3>
        <style>
            .stat-card {
                padding: 20px;
                border-radius: 12px;
                background: #f8f9fa;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                transition: transform 0.2s;
                margin-bottom:20px;
            }
            .stat-card:hover {
                transform: translateY(-4px);
            }
            .stat-number {
                font-size: 32px;
                font-weight: 700;
                color: #2f80ed;
            }
            .stat-label {
                font-size: 16px;
                color: #555;
            }
        </style>
    """, unsafe_allow_html=True)

    url = f"{BACKEND_URL}/admin_stats"
    headers = {"Authorization": f"Bearer {st.session_state.admin_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        st.error("Failed to load dashboard stats.")
        return

    data = response.json()

    users_count = data.get("total_users", 0)
    kb_count = data.get("total_kb_items", 0)
    chats_count = data.get("total_chats", 0)
    feedback_count = data.get("total_feedbacks", 0)
    query_count = data.get("total_queries", chats_count)  # fallback

    col1, col2, col3,col4,col5 = st.columns([1,2,2,2,1])
    col6, col7,col8,col9,col10 = st.columns([1,2,2,2,1])

    def stat_box(col, icon, label, value):
        col.markdown(f"""
            <div class="stat-card">
                <div style="font-size:28px;">{icon}</div>
                <div class="stat-number">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
        """, unsafe_allow_html=True)

    stat_box(col2, "👥", "Total Users", users_count)
    stat_box(col3, "🩺", "Health Topics", kb_count)
    stat_box(col4, "💬", "Chats", chats_count)
    stat_box(col7, "⭐", "Feedbacks", feedback_count)
    stat_box(col8, "📨", "Queries Handled", query_count)

    c1,c2,c3,c4=st.columns([0.5,2,2,0.5])
    with c2:
        st.markdown("<h4 style='text-align:center;'>⭐ Ratings Overview</h4>", unsafe_allow_html=True)
        show_ratings_chart()
    with c3:
        st.markdown("<h4 style='text-align:center;'>Most Asked Topics</h4>", unsafe_allow_html=True)
        show_entity_stats()


def show_feedbacks():
    st.markdown("<div style='text-align: center; padding-bottom:10px;'><h3>⭐ User Feedbacks</h3></div>", unsafe_allow_html=True)

    headers = {"Authorization": f"Bearer {st.session_state.admin_token}"}
    res = requests.get(f"{BACKEND_URL}/admin_get_feedbacks", headers=headers)

    if res.status_code != 200:
        st.error("Failed to fetch feedbacks")
        return

    feedbacks = res.json()

    if not feedbacks:
        st.info("No feedback records found yet.")
        return
    col1,col2,col3=st.columns([1,2,1])
    # Display each feedback in a card box
    with col2:
      for fb in feedbacks:
          comment = fb.get("comment", "")
          if(comment!=""):
              rating_stars = "⭐" * (int(fb.get("rating", 0)) +1) # Convert numeric rating to stars
              user = fb.get("user_email", "Unknown User")
              time = fb.get("timestamp", "")

              st.markdown(
                  f"""
                  <div style="
                      background-color: #ffffff;
                      padding: 12px 18px;
                      border-radius: 10px;
                      box-shadow: 0px 2px 8px rgba(0,0,0,0.15);
                      margin-bottom: 12px;
                  ">
                      <p><strong>{rating_stars}</strong> <span style="color: #777; font-size: 13px;">({time})</span></p>
                      <p style="font-size: 14px; margin-top: -8px;"><i>{comment if comment else "No comment provided"}</i></p>
                      <p style="font-size: 13px; color: grey; margin-top: -6px;">👤 {user}</p>
                  </div>
                  """,
                  unsafe_allow_html=True
              )


def show_knowledge_base_editor():
    st.markdown("""
        <div style='text-align: center; padding-bottom: 10px;'>
            <h3>📋 Knowledge Base Records</h3>
        </div>
    """, unsafe_allow_html=True)

    headers = {"Authorization": f"Bearer {st.session_state.admin_token}"}
    res = requests.get(f"{BACKEND_URL}/admin_get_kb", headers=headers)

    if res.status_code != 200:
        st.error("Failed to load knowledge base")
        return

    kb = res.json()

    # White background container
    st.markdown("""
        <style>
            .kb-box {
                background-color: white;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #ddd;
                margin-bottom:15px;
            }
            .kb-header {
                font-weight: 600;
                background-color: white;
                padding: 8px;
                border-radius: 6px;
                margin-bottom: 5px;
            }
        </style>
    """, unsafe_allow_html=True)

    with st.container():

        # Header Row
        h1, h2, h3, h4, h5, h6, h7 = st.columns([0.1,0.5,1,1,0.4,0.4,0.1])
        h2.markdown("<div class='kb-header'>Condition</div>", unsafe_allow_html=True)
        h3.markdown("<div class='kb-header'>First Aid</div>", unsafe_allow_html=True)
        h4.markdown("<div class='kb-header'>Prevention</div>", unsafe_allow_html=True)
        h5.markdown("<div class='kb-header'>Edit</div>", unsafe_allow_html=True)
        h6.markdown("<div class='kb-header'>Delete</div>", unsafe_allow_html=True)

        # Rows
        for item in kb:
            col1, col2, col3, col4, col5, col6, col7 = st.columns([0.1,0.5,1,1,0.4,0.4,0.1])

            col2.write(f"**{item['condition']}**")
            col3.write(item["first_aid"])
            col4.write(item["prevention"])

            if col5.button("✏️", key=f"edit_{item['id']}"):
                st.session_state.edit_item = item
                st.session_state.admin_page = "edit_kb"
                st.rerun()

            if col6.button("🗑️", key=f"delete_{item['id']}"):
                requests.delete(f"{BACKEND_URL}/admin/delete_kb/{item['id']}", headers=headers)
                st.toast("Deleted successfully!")
                st.rerun()


def show_add_kb_page():
    st.markdown("<div style='text-align: center; padding-bottom:10px;'><h3>Add New Knowledge Base Entry</h3></div>", unsafe_allow_html=True)
    col1,col2,col3 =st.columns([1,2,1])
    with col2:
        c = st.text_input("Condition", placeholder="Enter condition (ex: Fever)")
        a = st.text_area("First Aid", placeholder="Enter first aid steps...")
        p = st.text_area("Prevention", placeholder="Enter prevention tips...")

        if st.button("✅ Add Entry",width=150):
            if not c:
                st.error("Condition can't be empty")
            else:
                headers = {"Authorization": f"Bearer {st.session_state.admin_token}"}
                requests.post(f"{BACKEND_URL}/admin/add_kb", headers=headers, json={
                    "condition": c,
                    "first_aid": a,
                    "prevention": p
                })
                st.success("Entry added successfully!")
                st.session_state.admin_page = "kb"
                st.rerun()

def show_edit_kb_page():
    edit = st.session_state.get("edit_item")

    if not edit:
        st.error("No item selected")
        return
    st.markdown(f"<div style='text-align: center; padding-bottom:10px;'><h3>✏️ Edit: {edit['condition']}</h3></div>", unsafe_allow_html=True)
    col1,col2,col3 =st.columns([1,2,1])
    with col2:
        new_condition = st.text_input("Condition", edit["condition"])
        new_aid = st.text_area("First Aid", edit["first_aid"])
        new_prev = st.text_area("Prevention", edit["prevention"])

        if st.button("💾 Save Changes",width=150):
            headers = {"Authorization": f"Bearer {st.session_state.admin_token}"}
            requests.put(
                f"{BACKEND_URL}/admin/update_kb/{edit['id']}",
                headers=headers,
                json={
                    "condition": new_condition,
                    "first_aid": new_aid,
                    "prevention": new_prev
                }
            )
            st.success("Updated successfully!")
            st.session_state.admin_page = "kb"
            st.rerun()


def show_admin_dashboard():
    if "admin_token" not in st.session_state:
        st.error("Unauthorized access! Please log in as admin.")
        return

    st.sidebar.title("⚙️ Admin Panel")

    # Sidebar Navigation Buttons
    if st.sidebar.button("📊 Dashboard "):
        st.session_state.admin_page = "dashboard"

    if st.sidebar.button("💬 Feedbacks"):
        st.session_state.admin_page = "feedbacks"

    if st.sidebar.button("Knowledge Base"):
        st.session_state.admin_page = "kb"

    if st.sidebar.button("Add Knowledge Entry"):
        st.session_state.admin_page = "add_kb"

    # Logout
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.session_state.page = "login"
        st.rerun()

    # Default
    page = st.session_state.get("admin_page", "dashboard")

    if page == "dashboard":
        show_admin_stats()

    elif page == "feedbacks":
        show_feedbacks()

    elif page == "kb":
        show_knowledge_base_editor()

    elif page == "add_kb":
        show_add_kb_page()

    elif page == "edit_kb":
        show_edit_kb_page()




#App run
def main():

    with st.container():
      st.markdown("<div class='fixedheader'>", unsafe_allow_html=True)

      col1, col2 = st.columns([0.6, 0.4])

      with col1:
          st.markdown("<h2 style='color:white;padding-top:2px;padding-left:30px;'>Wellness Guide</h2>", unsafe_allow_html=True)

      with col2:
          if st.session_state.get("token") :
              if not st.session_state.get("profile_data"):
                  get_profile()
              st.markdown(
                  f"<p style='color:white; font-weight:bold; font-size:24px; margin:0; padding-left:20px;'>"
                  f"Welcome, {st.session_state.profile_data.get('name')}!</p>",
                  unsafe_allow_html=True
              )
          else:
              if("admin_token" not in st.session_state):
                  c1, c2, c3 = st.columns(3)
                  with c1:
                      if st.button("Login",width=150):
                          st.session_state.page = "login"
                          st.rerun()
                  with c2:
                      if st.button("Register",width=150):
                          st.session_state.page = "register"
                          st.rerun()
                  with c3:
                      if st.button("Admin Login",width=150):
                          st.session_state.page = "admin_login"
                          st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


    if st.session_state.token:
        st.sidebar.title("Navigation")
        if st.sidebar.button("View Profile"):
            st.session_state.page = "profile"
            st.rerun()
        if st.sidebar.button("Update Profile"):
            st.session_state.page = "update_profile"
            st.rerun()
        if st.sidebar.button("🆕 New Chat"):
            # Create a new chat on the backend
            url = f"{BACKEND_URL}/new_chat"
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            data = {"title": "New Chat"}
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    st.session_state.chat_id = response.json().get("chat_id")
                    st.session_state.chat_history = [INITIAL_CHAT_MESSAGE]
                    st.session_state.page = "chat"
                    st.rerun()
                else:
                    st.error("Could not create new chat.")
            except requests.exceptions.ConnectionError:
                st.error("Server connection failed.")

        # Fetch chat history
        if st.sidebar.button("📜 Chat History"):
              url = f"{BACKEND_URL}/get_chats"
              headers = {"Authorization": f"Bearer {st.session_state.token}"}
              try:
                  response = requests.get(url, headers=headers)
                  if response.status_code == 200:
                      st.session_state.chat_list = response.json().get("chats", [])
                      st.session_state.page = "chat_history"
                      st.rerun()
                  else:
                      st.error("Unable to fetch chat history.")
              except requests.exceptions.ConnectionError:
                  st.error("Server connection failed.")

        if st.sidebar.button("Logout"):
              st.session_state.token = None
              st.session_state.page = "login"
              st.session_state.profile_data = {}
              st.session_state.chat_history = []
              st.session_state.chat_id = None
              st.session_state.chat_list = []
              st.rerun()



    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    if st.session_state.page == "login":
        show_login_page()
    elif st.session_state.page == "register":
        show_register_page()
    elif st.session_state.page == "admin_login":
        show_admin_login()
    elif st.session_state.page == "admin_dashboard":
        show_admin_dashboard()
    elif st.session_state.token and st.session_state.page == "profile":
        show_profile_page()
    elif st.session_state.token and st.session_state.page == "update_profile":
        show_update_profile_page()
    elif st.session_state.token and st.session_state.page == "chat":
        show_chatbot_page()
    elif st.session_state.token and st.session_state.page == "chat_history":
        show_chat_history_page()

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
