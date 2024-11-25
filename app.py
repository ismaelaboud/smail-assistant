import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from chatbot import PersonalizedChatbot
import os
from dotenv import load_dotenv
import requests
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
    UserMixin
)
from google_auth import flow, get_google_provider_cfg, GOOGLE_CLIENT_ID
import google.auth.transport.requests
from google.oauth2 import id_token
from pip._vendor import cachecontrol
import json
from flask_sqlalchemy import SQLAlchemy
from models import db, Chat

# Load environment variables
load_dotenv()

# User class
class User(UserMixin):
    def __init__(self, user_id, name, email):
        self.id = user_id
        self.name = name
        self.email = email

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chats.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
chatbot = PersonalizedChatbot(name="ismael")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User loader callback
@login_manager.user_loader
def load_user(user_id):
    if "google_id" not in session:
        return None
    return User(
        user_id=session["google_id"],
        name=session.get("name"),
        email=session.get("email")
    )

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    try:
        message = request.json.get('message')
        
        # Updated for Pixtral-12B
        response = requests.post(
            'https://api.mistral.ai/v1/chat/completions',
            headers={
                'Authorization': f"Bearer {os.getenv('MISTRAL_API_KEY')}",
                'Content-Type': 'application/json'
            },
            json={
                'model': 'pixtral-12b',  # Changed model to pixtral-12b
                'messages': [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant capable of understanding and processing both text and images."
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 1000,  # Increased max tokens for longer responses
                'top_p': 0.9,
                'presence_penalty': 0.1,
                'frequency_penalty': 0.1
            },
            timeout=int(os.getenv('REQUEST_TIMEOUT', 30))
        )
        
        response.raise_for_status()
        bot_response = response.json()['choices'][0]['message']['content']
        
        # Generate audio response
        audio_response = chatbot.text_to_speech(bot_response)
        
        # Save the chat to database
        new_chat = Chat(
            user_id=current_user.id,
            message=message,
            response=bot_response
        )
        db.session.add(new_chat)
        db.session.commit()
        
        return jsonify({
            'text': bot_response,
            'audio': audio_response
        })

    except Exception as e:
        return jsonify({
            'text': f'I apologize, but there was an error: {str(e)}',
            'audio': ''
        }), 500

@app.route('/update-voice', methods=['POST'])
def update_voice():
    config = request.json
    chatbot.set_voice_properties(
        gender=config.get('gender', 'male'),
        rate=int(config.get('rate', 150)),
        volume=float(config.get('volume', 0.9))
    )
    return jsonify({'status': 'success'})

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    try:
        flow.fetch_token(authorization_response=request.url)

        if not session["state"] == request.args["state"]:
            return redirect(url_for("login"))

        credentials = flow.credentials
        request_session = requests.session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        try:
            id_info = id_token.verify_oauth2_token(
                id_token=credentials._id_token,
                request=token_request,
                audience=GOOGLE_CLIENT_ID,
                clock_skew_in_seconds=300  # Add 5 minutes of clock skew tolerance
            )
        except ValueError as e:
            print(f"Token verification error: {str(e)}")
            return redirect(url_for("login"))

        session["google_id"] = id_info.get("sub")
        session["name"] = id_info.get("name")
        session["email"] = id_info.get("email")
        
        # Create and login user
        user = User(
            user_id=session["google_id"],
            name=session["name"],
            email=session["email"]
        )
        login_user(user)
        
        return redirect(url_for("home"))
    except Exception as e:
        print(f"Callback error: {str(e)}")
        return redirect(url_for("login"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("home"))

@app.route('/get-chats', methods=['GET'])
@login_required
def get_chats():
    chats = Chat.query.filter_by(user_id=current_user.id)\
                     .order_by(Chat.timestamp.desc())\
                     .limit(50)\
                     .all()
    return jsonify([chat.to_dict() for chat in chats])

if __name__ == '__main__':
    app.run(debug=True) 